"""
Essay Writing Coach — Tool Definitions
=======================================
Agent: IELTS Writing Task 2 Coach (Google ADK)
Target users: Vietnamese learners, level A2-B1
Essay types: opinion, discussion, adv_dis, problem_solution, two_part_question

Each tool is a standalone Python function with:
- Clear docstring (used as tool description by ADK)
- Type-annotated parameters
- Return type annotation
- Usage examples in docstring

References used by each tool are listed in the docstring.
Actual LLM calls are made via google-genai SDK.
"""

import os
import json
import re
from pathlib import Path
from typing import Literal

from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

EssayType = Literal[
    "opinion",
    "discussion",
    "adv_dis",
    "problem_solution",
    "two_part_question",
]

Section = Literal["introduction", "body1", "body2", "body3", "conclusion"]

Level = Literal["A2", "B1"]


# ---------------------------------------------------------------------------
# Internal helpers — NOT exposed as ADK tools
# ---------------------------------------------------------------------------

_REF_CACHE: dict[str, str] = {}

def _load_ref(filename: str) -> str:
    """Load a file from the references/ directory and cache it in memory."""
    if filename not in _REF_CACHE:
        ref_dir = Path(__file__).parent.parent / "references"
        try:
            _REF_CACHE[filename] = (ref_dir / filename).read_text(encoding="utf-8")
        except FileNotFoundError:
            _REF_CACHE[filename] = ""
    return _REF_CACHE[filename]


def _call_gemini_mock(user_prompt: str, system_instruction: str = "") -> str:
    """Return schema-valid mock JSON when MOCK_GEMINI=1.

    Dispatched by distinctive keywords in system_instruction so each tool
    gets the correct mock response without calling the real API.
    """
    si = system_instruction.lower()

    # ── paraphrase_prompt ────────────────────────────────────────────────
    if "paraphrase" in si and "3 cách" in si:
        return json.dumps({
            "level": "B1",
            "paraphrases": [
                {"text": "[MOCK] It is often argued that music serves as an effective means of uniting individuals from diverse cultures.",
                 "technique": "Synonym Substitution"},
                {"text": "[MOCK] The notion that music plays a crucial role in fostering cohesion among people of varied backgrounds is widely held.",
                 "technique": "Structure Change"},
                {"text": "[MOCK] Many contend that music possesses a unique ability to bridge divides between cultures and generations.",
                 "technique": "Perspective Shift"},
            ],
            "explanation": "[MOCK] Ba cách paraphrase đề bài ở trình độ B1.",
            "common_synonyms": {"say": ["argue", "claim"], "good": ["effective", "beneficial"]},
        })

    # ── guide_essay_section ──────────────────────────────────────────────
    if "instructions" in si and "template" in si and "checklist" in si:
        return json.dumps({
            "section": "introduction",
            "next_section": "body1",
            "instructions": [
                "[MOCK] Bước 1: Paraphrase đề bài bằng cách thay từ đồng nghĩa.",
                "[MOCK] Bước 2: Nêu rõ quan điểm (thesis statement).",
                "[MOCK] Bước 3: Kiểm tra lại câu mở đầu.",
            ],
            "template": "[MOCK] It is [often/widely] argued that [topic]. This essay strongly [agrees/disagrees] with this view.",
            "example": "[MOCK] It is often argued that music serves as a universal connector across cultures. This essay strongly agrees with this perspective.",
            "useful_phrases": [
                "It is often argued that",
                "This essay will argue that",
                "Many people believe that",
            ],
            "common_errors": [
                "[MOCK] Lặp từ từ đề bài — thay bằng từ đồng nghĩa.",
                "[MOCK] Quên nêu thesis statement rõ ràng.",
            ],
            "checklist": [
                "[MOCK] Đã paraphrase đề bài chưa?",
                "[MOCK] Đã nêu thesis statement chưa?",
                "[MOCK] Câu dẫn có tự nhiên không?",
            ],
        })

    # ── suggest_sentence_structures ──────────────────────────────────────
    if "variations" in si and "pattern" in si:
        return json.dumps({
            "original": user_prompt[:80],
            "variations": [
                {
                    "pattern": "S + V + O, particularly by + V-ing, which + V + O",
                    "text": "[MOCK] Technology offers numerous benefits, particularly by saving time, which allows people to focus on creative tasks.",
                    "level": "B1",
                    "explanation": "[MOCK] Mở rộng câu đơn bằng cụm 'particularly by'.",
                },
                {
                    "pattern": "Not only ... but also ...",
                    "text": "[MOCK] Technology not only saves time but also connects people across the world.",
                    "level": "B1",
                    "explanation": "[MOCK] Dùng cặp 'not only ... but also' để liệt kê 2 lợi ích.",
                },
            ],
            "explanation": "[MOCK] Hai cấu trúc câu phù hợp trình độ B1.",
            "avoid": [
                "[MOCK] Tránh bắt đầu mọi câu bằng 'Technology is'.",
                "[MOCK] Tránh dùng 'very good' — thay bằng 'highly beneficial'.",
            ],
        })

    # ── enrich_vocabulary ────────────────────────────────────────────────
    if "overused" in si and "suggestions" in si:
        return json.dumps({
            "overused_words": ["people (2x)", "good", "technology (2x)"],
            "suggestions": {
                "people": [
                    {"word": "individuals", "meaning": "cá nhân", "example": "[MOCK] Individuals benefit greatly from modern technology."},
                    {"word": "society", "meaning": "xã hội", "example": "[MOCK] Society as a whole has embraced digital tools."},
                ],
                "good": [
                    {"word": "beneficial", "meaning": "có lợi", "example": "[MOCK] Technology is highly beneficial for education."},
                    {"word": "advantageous", "meaning": "thuận lợi", "example": "[MOCK] It is advantageous to learn digital skills."},
                ],
            },
            "topic_words": [
                {"word": "technological advancements", "meaning": "những tiến bộ công nghệ", "example": "[MOCK] Technological advancements have transformed daily life."},
                {"word": "digital literacy", "meaning": "kỹ năng số", "example": "[MOCK] Digital literacy is essential in the modern workplace."},
            ],
            "collocations": ["foster innovation", "bridge the digital divide", "harness technology"],
            "improved_text": "[MOCK] Technological advancements are highly beneficial for individuals. These innovations effectively enable society to accomplish tasks more efficiently.",
            "explanation": "[MOCK] Đã thay thế các từ lặp bằng từ vựng học thuật phù hợp IELTS Band 6.",
        })

    # ── fallback (classify uses keyword match, rarely hits Gemini) ───────
    return json.dumps({"_mock": True, "status": "ok", "note": "fallback mock"})


def _call_gemini(user_prompt: str, system_instruction: str = "") -> str:
    """Call Gemini 2.5 Flash and return the raw text response (forced JSON).

    If env var MOCK_GEMINI=1, returns a fixed mock response without calling
    the real API — useful for local development and testing within quota.

    gemini-2.5-flash uses thinking mode by default. When thinking parts are
    present, response.text may be None even though the actual answer exists
    in a non-thought content part. This function extracts text explicitly
    from non-thought parts to handle both cases reliably.
    """
    # ── Mock mode ─────────────────────────────────────────────────────────
    if os.environ.get("MOCK_GEMINI", "").strip() == "1":
        return _call_gemini_mock(user_prompt, system_instruction)

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return ""
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_instruction}\n\n{user_prompt}" if system_instruction else user_prompt
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        # Fast path: response.text is populated (non-thinking or short prompts)
        if response.text:
            return response.text

        # Fallback: extract text from non-thought parts explicitly.
        # gemini-2.5-flash thinking mode can separate thought parts (thought=True)
        # from the actual answer (thought=False/None). response.text returns None
        # when only thought parts are present in the first candidate.
        if response.candidates:
            cand = response.candidates[0]
            if cand.content and cand.content.parts:
                texts = [
                    p.text
                    for p in cand.content.parts
                    if p.text and not getattr(p, "thought", False)
                ]
                if texts:
                    return "".join(texts)
        return ""
    except Exception as exc:
        # Surface the error class name so callers can log/display it
        # Returns a special sentinel that _safe_parse_json will reject (returns None)
        return json.dumps({"_api_error": type(exc).__name__, "_api_message": str(exc)[:300]})



def _safe_parse_json(raw: str):
    """Attempt to parse a JSON string; return None on failure or API error."""
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        # Reject the API-error sentinel dict so callers return their error fallback
        if isinstance(parsed, dict) and "_api_error" in parsed:
            return None
        return parsed
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Tool 1 — classify_essay_type
# ---------------------------------------------------------------------------

_CLASSIFICATION_RULES: list[tuple] = [
    ("discussion", [
        "discuss both these views",
        "discuss both views",
        "discuss both",
    ]),
    ("adv_dis", [
        "advantages and disadvantages",
        "benefits and drawbacks",
        "positive or negative development",
        "positive or negative",
        "outweigh",
    ]),
    ("problem_solution", [
        "what are the causes",
        "what are the reasons",
        "what measures",
        "what solutions",
        "how could this be solved",
        "how could this problem be tackled",
        "what can be done to solve",
        "reasons for this",
        "causes of this",
        "what problems",
    ]),
    ("opinion", [
        "to what extent do you agree or disagree",
        "to what extent do you agree",
        "agree or disagree",
        "do you agree or disagree",
        "do you agree",
        "how far do you agree",
        "in your opinion",
        "do you think",
        "give your own opinion",
    ]),
]


def _keyword_classify(prompt_lower: str):
    for essay_type, keywords in _CLASSIFICATION_RULES:
        found = [kw for kw in keywords if kw in prompt_lower]
        if found:
            return essay_type, found
    return None, []


def _is_two_part_question(prompt: str) -> bool:
    return len(re.findall(r"\?", prompt)) >= 2


def classify_essay_type(prompt: str) -> dict:
    """
    Phân loại dạng đề IELTS Writing Task 2 dựa trên từ khoá trong đề bài.

    Nhận vào đề bài (tiếng Anh), trả về:
    - essay_type: một trong 5 dạng
    - confidence: "high" | "medium" | "low"
    - keywords_found: danh sách từ khoá nhận diện được
    - explanation: giải thích ngắn bằng tiếng Việt tại sao classify như vậy

    KEYWORDS NHẬN DIỆN (từ references/):
    - opinion:           "agree or disagree", "to what extent", "do you think",
                         "in your opinion", "how far do you agree"
    - discussion:        "discuss both", "discuss both views", "discuss both these views"
    - adv_dis:           "advantages and disadvantages", "outweigh", "positive or negative
                         development", "benefits and drawbacks"
    - problem_solution:  "what are the causes", "what measures", "what solutions",
                         "how could this be solved", "what can be done to solve",
                         "reasons for this", "how could this problem be tackled"
    - two_part_question: đề có 2 dấu "?" riêng biệt, hoặc 2 câu hỏi rõ ràng
                         (e.g. "Why is this? What effect does it have?")

    EDGE CASES:
    - "Do you agree? What can be done?" → two_part_question (2 câu hỏi)
    - "Positive or negative development?" → adv_dis
    - "Why might this be the case? What are the disadvantages?" → two_part_question

    Args:
        prompt: Đề bài IELTS Writing Task 2 (tiếng Anh)

    Returns:
        dict với keys: essay_type, confidence, keywords_found, explanation

    Example:
        >>> classify_essay_type(
        ...     "Music is a good way of bringing people together. "
        ...     "To what extent do you agree or disagree?"
        ... )
        {
            "essay_type": "opinion",
            "confidence": "high",
            "keywords_found": ["to what extent do you agree or disagree"],
            "explanation": "Đề dùng 'to what extent do you agree or disagree' — "
                           "đây là dấu hiệu rõ ràng của Opinion essay. "
                           "Bạn cần nêu rõ ý kiến cá nhân và bảo vệ quan điểm đó."
        }

    Reference: references/opinion_brainstorm.md, references/discussion_brainstorm.md,
               references/adv_dis_brainstorm.md, references/problem_solution_brainstorm.md,
               references/two_part_question_brainstorm.md, references/test_cases.md
    """
    if not prompt or not prompt.strip():
        return {"error": "Đề bài không được để trống."}

    prompt_lower = prompt.lower()

    # Step 1: Two-part question heuristic (2+ question marks)
    if _is_two_part_question(prompt):
        kw_type, found_kw = _keyword_classify(prompt_lower)
        if kw_type in ("opinion", "problem_solution", None):
            return {
                "essay_type": "two_part_question",
                "confidence": "high",
                "keywords_found": found_kw or ["2 câu hỏi riêng biệt"],
                "explanation": (
                    "Đề có 2 câu hỏi riêng biệt (2 dấu '?'). "
                    "Đây là dạng Two-Part Question — bạn phải trả lời cả hai câu hỏi, "
                    "mỗi câu một đoạn thân bài riêng."
                ),
            }

    # Step 2: Pure keyword matching
    kw_type, found_kw = _keyword_classify(prompt_lower)
    if kw_type is not None:
        explanations = {
            "opinion": (
                f"Đề dùng từ khoá '{', '.join(found_kw)}' — "
                "đây là dấu hiệu rõ ràng của Opinion essay. "
                "Bạn cần nêu rõ ý kiến cá nhân (agree/disagree) và bảo vệ quan điểm đó."
            ),
            "discussion": (
                f"Đề dùng từ khoá '{', '.join(found_kw)}' — "
                "đây là dạng Discussion essay. "
                "Bạn cần trình bày cả hai quan điểm trước khi nêu ý kiến cá nhân."
            ),
            "adv_dis": (
                f"Đề dùng từ khoá '{', '.join(found_kw)}' — "
                "đây là dạng Advantages & Disadvantages essay. "
                "Body 1 trình bày ưu điểm, Body 2 trình bày nhược điểm (hoặc ngược lại)."
            ),
            "problem_solution": (
                f"Đề dùng từ khoá '{', '.join(found_kw)}' — "
                "đây là dạng Problem-Solution essay. "
                "Body 1 phân tích nguyên nhân/vấn đề, Body 2 đề xuất giải pháp."
            ),
        }
        return {
            "essay_type": kw_type,
            "confidence": "high",
            "keywords_found": found_kw,
            "explanation": explanations[kw_type],
        }

    # Step 3: Fallback — ask Gemini
    test_cases_ref = _load_ref("test_cases.feature")
    system_instr = (
        "Bạn là chuyên gia IELTS Writing Task 2. "
        "Phân loại đề bài sau vào một trong 5 dạng: "
        "opinion, discussion, adv_dis, problem_solution, two_part_question. "
        "Trả về JSON hợp lệ với đúng 4 keys: essay_type (string), confidence (string: 'high'|'medium'|'low'), "
        "keywords_found (array of strings), explanation (string tiếng Việt). "
        "Không thêm bất kỳ text nào ngoài JSON."
    )
    user_msg = (
        f"Đề bài: \"{prompt}\"\n\n"
        f"Tham khảo các ví dụ phân loại:\n{test_cases_ref[:3000]}"
    )
    raw = _call_gemini(user_msg, system_instr)
    parsed = _safe_parse_json(raw)

    if parsed and isinstance(parsed, dict) and "essay_type" in parsed:
        valid_types = {"opinion", "discussion", "adv_dis", "problem_solution", "two_part_question"}
        if parsed.get("essay_type") not in valid_types:
            parsed["essay_type"] = "opinion"
        parsed.setdefault("confidence", "low")
        parsed.setdefault("keywords_found", [])
        parsed.setdefault("explanation", "Phân loại dựa trên phân tích ngữ nghĩa đề bài.")
        return parsed

    return {
        "error": "Không thể phân loại đề bài. Vui lòng kiểm tra lại đề hoặc thử lại.",
        "essay_type": None,
        "confidence": "low",
        "keywords_found": [],
        "explanation": "Không nhận diện được từ khoá đặc trưng và Gemini API không phản hồi.",
    }


# ---------------------------------------------------------------------------
# Tool 2 — paraphrase_prompt
# ---------------------------------------------------------------------------

def paraphrase_prompt(prompt: str, level: Level = "B1") -> dict:
    """
    Tạo 3 cách paraphrase đề bài IELTS Writing Task 2 phù hợp với level người học.

    Paraphrase là bước đầu tiên của Introduction — thay từ và cấu trúc câu
    mà giữ nguyên nghĩa gốc, KHÔNG copy nguyên văn từ đề bài.

    NGUYÊN TẮC PARAPHRASE (từ Mindset L3 + Pauline Cullen):
    - Dùng synonyms thay thế từ quan trọng trong đề
    - Đổi cấu trúc câu (active ↔ passive, noun phrase, cleft sentence)
    - Không dùng lại quá 2 từ liên tiếp từ đề gốc
    - Giữ đúng nghĩa — không thêm hoặc bớt thông tin

    CHIẾN LƯỢC PARAPHRASE THEO LEVEL:
    - A2: Dùng synonyms đơn giản + đổi word order cơ bản
    - B1: Synonyms học thuật + đổi cấu trúc câu (passive voice, noun phrase)

    Args:
        prompt: Đề bài gốc (tiếng Anh)
        level:  "A2" hoặc "B1" — ảnh hưởng độ phức tạp của từ vựng và cấu trúc

    Returns:
        dict với keys:
        - original: đề gốc
        - paraphrases: list 3 cách paraphrase (mỗi item có "text" và "technique")
        - explanation: giải thích ngắn bằng tiếng Việt về cách paraphrase
        - common_synonyms: dict các từ quan trọng → synonyms gợi ý

    Reference: references/essay_templates.md, references/linking_words.md,
               references/opinion_brainstorm.md
    """
    if not prompt or not prompt.strip():
        return {"error": "Đề bài không được để trống."}

    vocab_ref    = _load_ref("vocabulary_by_topic.md")
    template_ref = _load_ref("essay_templates.md")

    level_guidance = {
        "A2": (
            "Người học ở level A2: dùng từ vựng đơn giản, cấu trúc câu cơ bản. "
            "Ưu tiên thay thế bằng synonyms ngắn gọn, dễ hiểu. "
            "Tránh passive voice phức tạp hoặc cấu trúc đảo ngữ."
        ),
        "B1": (
            "Người học ở level B1: có thể dùng từ vựng học thuật, passive voice, "
            "noun phrase, cleft sentence (It is... that...). "
            "Ưu tiên 3 kỹ thuật: synonym substitution, structure change, perspective shift."
        ),
    }

    system_instr = (
        "Bạn là giáo viên IELTS Writing chuyên dạy học viên người Việt. "
        "Tạo 3 cách paraphrase đề bài theo đúng nguyên tắc IELTS, phù hợp với level được yêu cầu. "
        "Trả về JSON hợp lệ với keys: "
        "original (string), "
        "paraphrases (array of objects với keys: text, technique), "
        "explanation (string tiếng Việt), "
        "common_synonyms (object: từ gốc → array synonyms). "
        "Không thêm bất kỳ text nào ngoài JSON."
    )

    user_msg = (
        f"Đề bài: \"{prompt}\"\n"
        f"Level người học: {level}\n"
        f"Hướng dẫn level: {level_guidance.get(level, '')}\n\n"
        f"Nguyên tắc paraphrase từ tài liệu:\n{template_ref[:1500]}\n\n"
        f"Từ vựng tham khảo (synonyms học thuật):\n{vocab_ref[:1500]}"
    )

    raw = _call_gemini(user_msg, system_instr)
    parsed = _safe_parse_json(raw)

    if parsed and isinstance(parsed, dict) and "paraphrases" in parsed:
        parsed["original"] = prompt
        parsed["level"] = level
        return parsed

    return {
        "error": "Không thể tạo paraphrase. Vui lòng thử lại.",
        "original": prompt,
        "level": level,
        "paraphrases": [],
        "explanation": "",
        "common_synonyms": {},
    }


# ---------------------------------------------------------------------------
# Tool 3 — guide_essay_section
# ---------------------------------------------------------------------------

_SECTION_ROLE: dict = {
    ("opinion",          "introduction"): "Paraphrase đề + nêu thesis (agree/disagree) + báo sẽ đưa ra 2 lý do.",
    ("opinion",          "body1"):        "Lý do 1 ủng hộ quan điểm: Topic sentence → Giải thích → Ví dụ cụ thể.",
    ("opinion",          "body2"):        "Lý do 2 ủng hộ quan điểm: Topic sentence → Giải thích → Ví dụ cụ thể.",
    ("opinion",          "conclusion"):   "Tóm tắt 2 lý do + nhắc lại quan điểm cá nhân (không đưa ý mới).",
    ("discussion",       "introduction"): "Paraphrase đề + nêu 2 phía tranh luận + báo sẽ xem xét cả hai.",
    ("discussion",       "body1"):        "Quan điểm A: trình bày + giải thích + ví dụ từ nhóm ủng hộ View A.",
    ("discussion",       "body2"):        "Quan điểm B: trình bày + giải thích + ví dụ từ nhóm ủng hộ View B + nêu ý kiến cá nhân.",
    ("discussion",       "conclusion"):   "Kết luận — tóm tắt 2 quan điểm + khẳng định lại ý kiến cá nhân.",
    ("adv_dis",          "introduction"): "Paraphrase đề + nêu sẽ phân tích cả ưu và nhược điểm.",
    ("adv_dis",          "body1"):        "Ưu điểm (Advantages): 2-3 điểm, mỗi điểm có giải thích + ví dụ.",
    ("adv_dis",          "body2"):        "Nhược điểm (Disadvantages): 2-3 điểm, mỗi điểm có giải thích + ví dụ.",
    ("adv_dis",          "conclusion"):   "Tóm tắt ưu/nhược + đưa ra verdict nếu là 'outweigh' variant.",
    ("problem_solution", "introduction"): "Paraphrase đề + nêu sẽ phân tích nguyên nhân và đề xuất giải pháp.",
    ("problem_solution", "body1"):        "Nguyên nhân/Vấn đề: 2-3 nguyên nhân chính, mỗi cái có giải thích.",
    ("problem_solution", "body2"):        "Giải pháp: 2-3 giải pháp thực tế, mỗi cái có giải thích tại sao hiệu quả.",
    ("problem_solution", "body3"):        "Giải pháp bổ sung hoặc hệ quả dự kiến (chỉ dùng nếu variant 3 đoạn).",
    ("problem_solution", "conclusion"):   "Tóm tắt nguyên nhân và giải pháp + kêu gọi hành động (nếu phù hợp).",
    ("two_part_question","introduction"): "Paraphrase đề + báo sẽ trả lời cả 2 câu hỏi.",
    ("two_part_question","body1"):        "Trả lời Câu hỏi 1: Topic sentence → Giải thích → Ví dụ.",
    ("two_part_question","body2"):        "Trả lời Câu hỏi 2: Topic sentence → Giải thích → Ví dụ.",
    ("two_part_question","conclusion"):   "Tóm tắt câu trả lời cho cả 2 câu hỏi ngắn gọn.",
}

_SECTION_NEXT: dict = {
    "introduction": "body1",
    "body1":        "body2",
    "body2":        "conclusion",
    "body3":        "conclusion",
    "conclusion":   None,
}


def guide_essay_section(
    section: Section,
    essay_type: EssayType,
    context: dict,
) -> dict:
    """
    Hướng dẫn viết từng phần cụ thể của bài essay IELTS Writing Task 2.

    Đây là tool chính của agent — dẫn dắt user qua từng bước:
    introduction → body1 → body2 → (body3 nếu cần) → conclusion

    SECTIONS:
    - "introduction": hướng dẫn viết mở bài (paraphrase + thesis)
    - "body1":        body paragraph đầu tiên (dựa trên essay_type)
    - "body2":        body paragraph thứ hai
    - "body3":        body paragraph thứ ba (chỉ dùng cho problem_solution variant C)
    - "conclusion":   hướng dẫn viết kết bài

    CONTEXT DICTIONARY:
    {
        "prompt":        str  — đề bài gốc
        "essay_type":    str  — đã classify
        "thesis":        str  — ý kiến của user (nếu là opinion/discussion)
        "paraphrase":    str  — câu paraphrase đã chọn
        "body1_ideas":   list — ideas đã brainstorm cho body 1
        "body2_ideas":   list — ideas đã brainstorm cho body 2
        "user_draft":    str  — đoạn user đã viết (nếu có, để feedback)
        "level":         str  — "A2" hoặc "B1"
    }

    Args:
        section:    phần bài cần hướng dẫn
        essay_type: dạng đề đã classify
        context:    dict chứa thông tin ngữ cảnh từ các bước trước

    Returns:
        dict với keys:
        - section:        tên phần đang hướng dẫn
        - instructions:   hướng dẫn từng bước bằng tiếng Việt
        - template:       mẫu câu/đoạn văn để user điền vào
        - example:        ví dụ hoàn chỉnh phù hợp với đề bài của user
        - useful_phrases: list các phrases hữu ích cho section này
        - common_errors:  list lỗi thường gặp cần tránh
        - checklist:      list các điểm cần check trước khi chuyển sang section tiếp

    Reference: references/essay_templates.md, references/opinion_brainstorm.md,
               references/discussion_brainstorm.md, references/adv_dis_brainstorm.md,
               references/problem_solution_brainstorm.md,
               references/two_part_question_brainstorm.md,
               references/linking_words.md
    """
    if not section or not essay_type:
        return {"error": "section và essay_type không được để trống."}

    template_ref = _load_ref("essay_templates.md")
    linking_ref  = _load_ref("linking_words.md")

    brainstorm_map = {
        "opinion":           "opinion.feature",
        "discussion":        "discussion.feature",
        "adv_dis":           "adv_dis.feature",
        "problem_solution":  "problem_solution.feature",
        "two_part_question": "two_part_question.feature",
    }
    brainstorm_ref = _load_ref(brainstorm_map.get(essay_type, "essay_templates.md"))

    section_role = _SECTION_ROLE.get((essay_type, section), f"Viết phần {section} của {essay_type} essay.")
    level        = context.get("level", "B1")
    essay_prompt = context.get("prompt", "")
    thesis       = context.get("thesis", "")
    paraphrase   = context.get("paraphrase", "")
    user_draft   = context.get("user_draft", "")

    system_instr = (
        "Bạn là giáo viên IELTS Writing chuyên dạy học viên người Việt ở trình độ A2-B1. "
        "Hướng dẫn phải bằng tiếng Việt, ví dụ câu tiếng Anh. "
        "Trả về JSON hợp lệ với đúng các keys sau: "
        "section (string), "
        "instructions (array of strings — mỗi bước hướng dẫn ngắn gọn bằng tiếng Việt), "
        "template (string — mẫu điền vào với [placeholder] bằng tiếng Anh), "
        "example (string — câu/đoạn văn hoàn chỉnh tiếng Anh phù hợp với đề bài), "
        "useful_phrases (array of strings tiếng Anh), "
        "common_errors (array of strings tiếng Việt), "
        "checklist (array of strings tiếng Việt). "
        "Không thêm bất kỳ text nào ngoài JSON."
    )

    user_msg = (
        f"Hướng dẫn viết phần: {section}\n"
        f"Dạng đề: {essay_type}\n"
        f"Vai trò của phần này: {section_role}\n"
        f"Level người học: {level}\n"
        f"Đề bài: \"{essay_prompt}\"\n"
        + (f"Paraphrase đã chọn: \"{paraphrase}\"\n" if paraphrase else "")
        + (f"Thesis/quan điểm của user: \"{thesis}\"\n" if thesis else "")
        + (f"Đoạn user đã viết (nếu có để feedback): \"{user_draft}\"\n" if user_draft else "")
        + f"\nTemplate tham khảo:\n{template_ref[:2000]}\n\n"
        f"Brainstorm tham khảo:\n{brainstorm_ref[:1500]}\n\n"
        f"Linking words tham khảo:\n{linking_ref[:1000]}"
    )

    raw = _call_gemini(user_msg, system_instr)
    parsed = _safe_parse_json(raw)

    if parsed and isinstance(parsed, dict) and "instructions" in parsed:
        parsed["section"] = section
        parsed["next_section"] = _SECTION_NEXT.get(section)
        return parsed

    return {
        "error": "Không thể tạo hướng dẫn. Vui lòng thử lại.",
        "section": section,
        "instructions": [],
        "template": "",
        "example": "",
        "useful_phrases": [],
        "common_errors": [],
        "checklist": [],
        "next_section": _SECTION_NEXT.get(section),
    }


# ---------------------------------------------------------------------------
# Tool 4 — suggest_sentence_structures
# ---------------------------------------------------------------------------

def suggest_sentence_structures(idea: str, level: Level = "B1") -> dict:
    """
    Gợi ý các cách viết câu phong phú hơn cho một ý (idea) của user.

    Khi user viết câu đơn giản hoặc lặp lại cấu trúc S+V+O, tool này
    gợi ý các biến thể cấu trúc câu giữ nguyên nghĩa nhưng phức tạp hơn.
    Giúp cải thiện band Grammatical Range and Accuracy.

    TRANSFORMATION PATTERNS (từ Sam McCarter Academic Writing Practice):
    1. Despite / In spite of + noun phrase
    2. Not having / Without + gerund
    3. With + noun phrase (result)
    4. Having + past participle
    5. Much as (concession)
    6. So/And (result)
    7. Otherwise (condition + consequence)
    8. Instead (substitution)
    9. Resulting in / Leading to (cause-effect)

    S+V+O EXPANSION (từ Mindset L3):
    - Simple: S + V + O
    - Adding: S + V + O, and/furthermore S + V + O
    - Contrast: S + V + O, however/although S + V + O
    - Cause: S + V + O because S + V + O
    - Result: S + V + O, so/consequently S + V + O
    - Condition: If S + V, S + V + O
    - Concession: Although/While S + V + O, S + V + O

    LEVEL ADJUSTMENT:
    - A2: Gợi ý các cách nối đơn giản (and, but, because, so)
    - B1: Gợi ý transformation patterns phức tạp hơn

    Args:
        idea:  Câu/ý user muốn viết (tiếng Anh hoặc Việt-Anh)
        level: "A2" hoặc "B1"

    Returns:
        dict với keys:
        - original:     câu gốc của user
        - variations:   list các biến thể câu (mỗi item có "text" và "pattern")
        - explanation:  giải thích ngắn bằng tiếng Việt về từng pattern
        - level_note:   ghi chú về độ phù hợp với level
        - avoid:        những lỗi cấu trúc câu cần tránh

    Reference: references/sentence_structures.md (Sam McCarter patterns),
               references/linking_words.md (discourse markers)
    """
    if not idea or not idea.strip():
        return {"error": "Ý/câu không được để trống."}

    struct_ref  = _load_ref("sentence_structures.md")
    linking_ref = _load_ref("linking_words.md")

    level_note_hint = {
        "A2": "Chỉ gợi ý patterns cơ bản: and/but/because/so, although, if. Không dùng cấu trúc quá phức tạp.",
        "B1": "Gợi ý cả patterns cơ bản lẫn nâng cao: Despite, Having+PP, With+NP, not only...but also, resulting in.",
    }

    system_instr = (
        "Bạn là giáo viên IELTS Writing chuyên dạy học viên người Việt ở trình độ A2-B1. "
        "Gợi ý 3-4 cách viết câu phong phú hơn cho ý của user. "
        "Trả về JSON hợp lệ với đúng các keys: "
        "original (string), "
        "variations (array of objects: text (string), pattern (string tên cấu trúc)), "
        "explanation (string tiếng Việt — giải thích từng variation), "
        "level_note (string tiếng Việt — ghi chú về level), "
        "avoid (array of strings tiếng Việt — lỗi cần tránh). "
        "Không thêm bất kỳ text nào ngoài JSON."
    )

    user_msg = (
        f"Câu/ý của user: \"{idea}\"\n"
        f"Level: {level}\n"
        f"Hướng dẫn level: {level_note_hint.get(level, '')}\n\n"
        f"Các patterns câu từ tài liệu:\n{struct_ref}\n\n"
        f"Linking words tham khảo:\n{linking_ref[:800]}"
    )

    raw = _call_gemini(user_msg, system_instr)
    parsed = _safe_parse_json(raw)

    if parsed and isinstance(parsed, dict) and "variations" in parsed:
        parsed["original"] = idea
        return parsed

    return {
        "error": "Không thể gợi ý cấu trúc câu. Vui lòng thử lại.",
        "original": idea,
        "variations": [],
        "explanation": "",
        "level_note": "",
        "avoid": [],
    }


# ---------------------------------------------------------------------------
# Tool 5 — enrich_vocabulary
# ---------------------------------------------------------------------------

_OVERUSED_WORDS = {
    "good", "bad", "big", "large", "small", "show", "use", "think",
    "say", "problem", "help", "important", "change", "increase",
    "decrease", "people", "government", "need", "make",
}


def _detect_overused(text: str) -> dict:
    """Count occurrences of overused words + any word repeated 3+ times."""
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    counts: dict = {}
    for w in words:
        if w in _OVERUSED_WORDS:
            counts[w] = counts.get(w, 0) + 1
    all_counts: dict = {}
    for w in words:
        all_counts[w] = all_counts.get(w, 0) + 1
    for w, cnt in all_counts.items():
        if cnt >= 3 and w not in counts:
            counts[w] = cnt
    return counts


def enrich_vocabulary(text: str, topic: str = "") -> dict:
    """
    Phát hiện từ vựng đơn điệu hoặc bị lặp trong đoạn văn của user
    và gợi ý synonyms/collocations học thuật phù hợp hơn.

    Giúp cải thiện band Lexical Resource bằng cách:
    - Phát hiện từ bị lặp nhiều lần
    - Gợi ý synonyms học thuật (academic vocabulary)
    - Gợi ý collocations phổ biến trong IELTS
    - Giải thích nghĩa và cách dùng bằng tiếng Việt

    COMMON OVERUSED WORDS (sẽ flag):
    good, bad, big, small, show, use, think, say, problem, help,
    important, change, increase, decrease, people, government, need, make

    TOPIC-BASED VOCABULARY (từ references/vocabulary_by_topic.md):
    Nếu topic được cung cấp, ưu tiên gợi ý từ trong topic đó:
    - environment, technology, education, work, health, society,
      transport, food, crime, family, media, science

    COLLOCATIONS (từ Mindset L3 + Pauline Cullen):
    - have a significant impact on / play a crucial role in
    - be closely linked to / raise awareness of
    - tackle the problem of / contribute to / lead to / result in

    Args:
        text:  Đoạn văn hoặc câu của user (tiếng Anh)
        topic: Chủ đề bài essay (optional) — giúp gợi ý từ vựng chính xác hơn

    Returns:
        dict với keys:
        - overused_words:  list các từ bị lặp/đơn điệu phát hiện được
        - suggestions:     dict {từ gốc → list các lựa chọn thay thế}
                           Mỗi lựa chọn có: word, meaning_vi, example, register
        - topic_words:     list từ vựng liên quan đến topic (nếu topic được cung cấp)
        - collocations:    list collocations phù hợp với nội dung đoạn văn
        - improved_text:   đề xuất đoạn văn đã được cải thiện từ vựng
        - explanation:     giải thích ngắn bằng tiếng Việt

    Reference: references/vocabulary_by_topic.md (12 topics × 20-22 words),
               references/linking_words.md (collocations section),
               references/sentence_structures.md
    """
    if not text or not text.strip():
        return {"error": "Đoạn văn không được để trống."}

    vocab_ref   = _load_ref("vocabulary_by_topic.md")
    linking_ref = _load_ref("linking_words.md")

    overused_counts  = _detect_overused(text)
    overused_display = [
        f"{w} ({cnt}x)" if cnt > 1 else w
        for w, cnt in sorted(overused_counts.items(), key=lambda x: -x[1])
    ]

    system_instr = (
        "Bạn là giáo viên IELTS Writing chuyên dạy học viên người Việt. "
        "Phân tích đoạn văn và gợi ý cải thiện từ vựng. "
        "Ưu tiên từ có trong tài liệu references trước, sau đó mới bổ sung thêm. "
        "Trả về JSON hợp lệ với đúng các keys: "
        "overused_words (array of strings như 'technology (4x)'), "
        "suggestions (object: từ gốc → array of objects: word, meaning_vi, example, register), "
        "topic_words (array of objects: word, meaning_vi, example), "
        "collocations (array of strings tiếng Anh), "
        "improved_text (string — đoạn văn đã cải thiện), "
        "explanation (string tiếng Việt). "
        "Không thêm bất kỳ text nào ngoài JSON."
    )

    user_msg = (
        f"Đoạn văn cần phân tích:\n\"{text}\"\n\n"
        + (f"Chủ đề bài essay: {topic}\n" if topic else "")
        + f"Từ bị lặp đã phát hiện: {', '.join(overused_display) if overused_display else 'chưa rõ'}\n\n"
        f"Từ vựng theo chủ đề từ tài liệu (ưu tiên dùng nguồn này):\n{vocab_ref}\n\n"
        f"Collocations tham khảo:\n{linking_ref[:600]}"
    )

    raw = _call_gemini(user_msg, system_instr)
    parsed = _safe_parse_json(raw)

    if parsed and isinstance(parsed, dict) and "suggestions" in parsed:
        if overused_display:
            parsed["overused_words"] = overused_display
        return parsed

    return {
        "error": "Không thể phân tích từ vựng. Vui lòng thử lại.",
        "overused_words": overused_display,
        "suggestions": {},
        "topic_words": [],
        "collocations": [],
        "improved_text": text,
        "explanation": "",
    }


# ---------------------------------------------------------------------------
# Essay Evaluation Tool
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import List

class CriterionEvaluation(BaseModel):
    band: float = Field(..., description="Điểm số lẻ từ 1.0 đến 6.5 (bước nhảy 0.5)")
    feedback: str = Field(..., description="Nhận xét ngắn gọn bằng tiếng Việt")
    suggestions: List[str] = Field(..., description="1-3 gợi ý cụ thể để cải thiện nâng band, bằng tiếng Việt")

class EssayEvaluationResponse(BaseModel):
    task_response: CriterionEvaluation
    coherence_cohesion: CriterionEvaluation
    lexical_resource: CriterionEvaluation
    grammatical_range: CriterionEvaluation


def ielts_round(avg: float) -> float:
    """Round-half-up to nearest 0.5, theo chuẩn IELTS."""
    import math
    return math.floor(avg * 2 + 0.5) / 2


def _build_evaluation_a2ui(overall_band: float, criteria: dict, essay_type: str, word_count: int) -> dict:
    """Helper to build an A2UI v0.9 payload for essay evaluation."""
    components = [
        {
            "id": "root",
            "component": "Column",
            "children": [
                "title",
                "overall_card",
                "divider_overall",
                "criteria_header",
                "criteria_list",
                "divider_bottom"
            ]
        },
        {
            "id": "title",
            "component": "Text",
            "text": f"📊 IELTS Writing Task 2 Evaluation (Overall: {overall_band} / 6.5)",
            "variant": "h1"
        },
        {
            "id": "overall_card",
            "component": "Card",
            "children": ["overall_header", "overall_meta"]
        },
        {
            "id": "overall_header",
            "component": "Text",
            "text": f"🏆 Overall Band Score: {overall_band} / 6.5",
            "variant": "h2"
        },
        {
            "id": "overall_meta",
            "component": "Text",
            "text": f"Dạng đề: {essay_type.replace('_', ' ').title()} | Tổng số từ: {word_count} từ",
            "variant": "caption"
        },
        {
            "id": "divider_overall",
            "component": "Divider"
        },
        {
            "id": "criteria_header",
            "component": "Text",
            "text": "🎯 Đánh giá chi tiết từng tiêu chí",
            "variant": "h2"
        },
        {
            "id": "criteria_list",
            "component": "Column",
            "children": ["tr_card", "cc_card", "lr_card", "gr_card"]
        },
        {
            "id": "divider_bottom",
            "component": "Divider"
        }
    ]

    criteria_keys = {
        "task_response": ("Task Response (Đáp ứng yêu cầu)", "tr"),
        "coherence_cohesion": ("Coherence & Cohesion (Mạch lạc)", "cc"),
        "lexical_resource": ("Lexical Resource (Từ vựng)", "lr"),
        "grammatical_range": ("Grammatical Range (Ngữ pháp)", "gr")
    }

    for key, (label, prefix) in criteria_keys.items():
        crit_data = criteria.get(key, {})
        band = crit_data.get("band", 1.0)
        feedback = crit_data.get("feedback", "Không có nhận xét.")
        suggestions = crit_data.get("suggestions", [])
        
        sug_lines = []
        for i, s in enumerate(suggestions):
            sug_lines.append(f"- {s}")
        sug_text = "\n".join(sug_lines) if sug_lines else "_Không có gợi ý cụ thể._"

        components.append({
            "id": f"{prefix}_card",
            "component": "Card",
            "children": [
                f"{prefix}_title",
                f"{prefix}_feedback_lbl",
                f"{prefix}_feedback_val",
                f"{prefix}_sug_lbl",
                f"{prefix}_sug_val"
            ]
        })
        components.append({
            "id": f"{prefix}_title",
            "component": "Text",
            "text": f"📌 {label}: {band} / 6.5",
            "variant": "h3"
        })
        components.append({
            "id": f"{prefix}_feedback_lbl",
            "component": "Text",
            "text": "📝 **Nhận xét từ giáo viên:**",
            "variant": "body"
        })
        components.append({
            "id": f"{prefix}_feedback_val",
            "component": "Text",
            "text": feedback,
            "variant": "body"
        })
        components.append({
            "id": f"{prefix}_sug_lbl",
            "component": "Text",
            "text": "💡 **Lời khuyên nâng band:**",
            "variant": "body"
        })
        components.append({
            "id": f"{prefix}_sug_val",
            "component": "Text",
            "text": sug_text,
            "variant": "body"
        })

    return {
        "version": "v0.9",
        "updateComponents": {
            "surfaceId": "main",
            "components": components
        }
    }


def evaluate_essay(essay_text: str, essay_type: str) -> dict:
    """Đánh giá và chấm điểm toàn diện bài viết IELTS Writing Task 2.

    Chỉ chấm điểm trong phạm vi 1.0 đến 6.5 theo bước nhảy 0.5 cho 4 tiêu chí.
    Tính điểm Overall Band làm tròn theo chuẩn IELTS.

    Args:
        essay_text: Toàn bộ bài luận của học viên cần đánh giá.
        essay_type: Dạng bài luận (opinion, discussion, problem_solution, advantages_disadvantages, two_part_question).

    Returns:
        Một dict chứa overall_band, điểm chi tiết từng tiêu chí, số từ và trạng thái lỗi.
    """
    # 1. Mock mode check
    if os.environ.get("MOCK_GEMINI", "").strip() == "1":
        words = len(essay_text.split())
        mock_result = {
            "overall_band": 5.0,
            "criteria": {
                "task_response": {
                    "band": 5.0,
                    "feedback": "Bài viết đã trả lời đầy đủ các phần của câu hỏi đề bài đưa ra. Tuy nhiên các ý tưởng phân tích còn tương đối đơn giản và thiếu ví dụ thực tế thuyết phục để làm nổi bật luận điểm.",
                    "suggestions": [
                        "Hãy bổ sung thêm các ví dụ thực tế (ví dụ như từ trải nghiệm cá nhân hoặc số liệu chung) để củng cố luận điểm.",
                        "Phát triển sâu hơn các nguyên nhân/giải pháp thay vì chỉ liệt kê chung chung."
                    ]
                },
                "coherence_cohesion": {
                    "band": 5.0,
                    "feedback": "Có bố cục rõ ràng gồm đầy đủ Mở bài, Thân bài và Kết bài. Tuy nhiên, sự liên kết giữa các câu trong đoạn còn hơi gượng gạo và dùng lặp lại một số từ nối máy móc.",
                    "suggestions": [
                        "Sử dụng đa dạng các trạng từ liên kết như 'Furthermore', 'Consequently', 'On the other hand' thay vì lặp lại 'And', 'But'.",
                        "Đảm bảo mỗi đoạn thân bài có một câu chủ đề (Topic Sentence) rõ ràng ở đầu đoạn."
                    ]
                },
                "lexical_resource": {
                    "band": 5.0,
                    "feedback": "Vốn từ vựng tương đối đủ dùng cho chủ đề này, người học hiểu nghĩa từ. Song, từ vựng còn ở mức cơ bản, nhiều từ bị lặp lại nhiều lần (như 'good', 'important').",
                    "suggestions": [
                        "Sử dụng các từ đồng nghĩa học thuật hơn (ví dụ: 'crucial', 'significant' thay cho 'important').",
                        "Học và áp dụng thêm các cụm từ (collocations) tự nhiên liên quan đến chủ đề."
                    ]
                },
                "grammatical_range": {
                    "band": 5.0,
                    "feedback": "Kết hợp được câu đơn và câu ghép cơ bản tương đối tốt. Tuy nhiên, khi thử viết các câu phức dài phức tạp thì vẫn còn mắc lỗi chia động từ hoặc dùng sai mệnh đề quan hệ.",
                    "suggestions": [
                        "Kiểm tra kỹ chia động từ số ít/số nhiều và các thì của câu.",
                        "Luyện tập viết các cấu trúc câu phức phổ biến như câu điều kiện (If) hoặc mệnh đề quan hệ (Which/Who)."
                    ]
                }
            },
            "essay_type": essay_type,
            "word_count": words,
            "error": False
        }
        mock_result["ui_available"] = True
        mock_result["ui"] = _build_evaluation_a2ui(5.0, mock_result["criteria"], essay_type, words)
        return mock_result

    # 2. Real API evaluation
    # Load Rubric JSON
    rubric_path = Path(__file__).parent.parent / "references" / "ielts_scoring_rubric.json"
    
    try:
        with open(rubric_path, "r", encoding="utf-8") as f:
            rubric_json = f.read()
    except Exception:
        rubric_json = "{}"

    # Build prompt
    prompt = (
        f"You are an expert IELTS Writing Task 2 examiner.\n"
        f"Evaluate the following student essay of type '{essay_type}' based on the provided IELTS simplified scoring rubric (from band 1.0 to 6.5).\n\n"
        f"Here is the simplified IELTS scoring rubric (mapping band scores to descriptions of student writing):\n"
        f"{rubric_json}\n\n"
        f"Student Essay to evaluate:\n"
        f"\"\"\"\n{essay_text}\n\"\"\"\n\n"
        f"Guidelines for your evaluation:\n"
        f"1. Carefully analyze the student's essay.\n"
        f"2. For each of the four criteria (task_response, coherence_cohesion, lexical_resource, grammatical_range), assign a band score.\n"
        f"3. The band score MUST be a float number chosen STRICTLY from the enum: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]. Do NOT assign any other score.\n"
        f"4. For each criterion, provide detailed 'feedback' (1-3 sentences) in Vietnamese explaining why this score was given, and 'suggestions' (1-3 items) in Vietnamese offering actionable advice for the student to improve.\n"
        f"5. All text in 'feedback' and 'suggestions' must be in Vietnamese."
    )

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"error": True, "message": "Không tìm thấy API Key cấu hình."}

    client = genai.Client(api_key=api_key)
    models = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    last_err = None

    import time
    for model in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EssayEvaluationResponse,
                    )
                )
                if response.text:
                    raw_data = json.loads(response.text)
                    criteria_keys = ["task_response", "coherence_cohesion", "lexical_resource", "grammatical_range"]
                    bands = []
                    valid_bands = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]
                    processed_criteria = {}

                    for key in criteria_keys:
                        crit = raw_data.get(key, {})
                        raw_band = crit.get("band", 1.0)
                        try:
                            val = float(raw_band)
                            closest_band = min(valid_bands, key=lambda x: abs(x - val))
                        except Exception:
                            closest_band = 1.0

                        bands.append(closest_band)
                        processed_criteria[key] = {
                            "band": closest_band,
                            "feedback": crit.get("feedback", "Không có nhận xét chi tiết."),
                            "suggestions": crit.get("suggestions", [])
                        }

                    overall_band = ielts_round(sum(bands) / 4.0)

                    res_dict = {
                        "overall_band": overall_band,
                        "criteria": processed_criteria,
                        "essay_type": essay_type,
                        "word_count": len(essay_text.split()),
                        "error": False
                    }
                    res_dict["ui_available"] = True
                    res_dict["ui"] = _build_evaluation_a2ui(overall_band, processed_criteria, essay_type, len(essay_text.split()))
                    return res_dict
            except Exception as e:
                err_str = str(e)
                last_err = e
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    time.sleep(2 ** (attempt + 1))
                    continue
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    break
                else:
                    break

    err_msg = "Hệ thống đang quá tải, vui lòng thử lại sau ít phút."
    if last_err:
        err_msg = f"Đã xảy ra lỗi kết nối ({type(last_err).__name__}). Vui lòng thử lại sau ít phút."
    return {"error": True, "message": err_msg}


# ---------------------------------------------------------------------------
# Tool registry (cho ADK agent)
# ---------------------------------------------------------------------------

TOOLS = [
    classify_essay_type,
    paraphrase_prompt,
    guide_essay_section,
    suggest_sentence_structures,
    enrich_vocabulary,
    evaluate_essay,
]

TOOL_DESCRIPTIONS = {
    "classify_essay_type": (
        "Phân loại dạng đề IELTS Writing Task 2: "
        "opinion, discussion, adv_dis, problem_solution, hoặc two_part_question. "
        "Dùng khi user cung cấp đề bài."
    ),
    "paraphrase_prompt": (
        "Tạo 3 cách paraphrase đề bài phù hợp với level A2 hoặc B1. "
        "Dùng khi bắt đầu viết Introduction."
    ),
    "guide_essay_section": (
        "Hướng quan viết từng phần cụ thể: introduction, body1, body2, conclusion. "
        "Cung cấp template, ví dụ, phrases hữu ích và checklist. "
        "Dùng khi user sắp viết một phần của bài."
    ),
    "suggest_sentence_structures": (
        "Gợi ý cách viết câu phong phú hơn cho một ý của user. "
        "Dùng khi câu user viết quá đơn giản hoặc lặp cấu trúc S+V+O."
    ),
    "enrich_vocabulary": (
        "Phát hiện từ bị lặp và gợi ý synonyms/collocations học thuật. "
        "Dùng khi user dùng từ đơn điệu hoặc yêu cầu cải thiện từ vựng."
    ),
    "evaluate_essay": (
        "Chấm điểm và đánh giá toàn diện bài viết IELTS Writing Task 2 hoàn chỉnh "
        "dựa trên khung rubric rút gọn từ 1.0 đến 6.5. "
        "Dùng khi bài viết đã hoàn tất."
    ),
}


if __name__ == "__main__":
    # Quick sanity check — print tool names and signatures
    import inspect
    for tool in TOOLS:
        sig = inspect.signature(tool)
        print(f"✅ {tool.__name__}{sig}")
    print(f"\nTotal tools: {len(TOOLS)}")
