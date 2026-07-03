"""
Essay Writing Coach — Tool Definitions (OOP Version)
===================================================
Agent: IELTS Writing Task 2 Coach (Google ADK)
Target users: Vietnamese learners, level A2-B1
Essay types: opinion, discussion, adv_dis, problem_solution, two_part_question

This file contains the Object-Oriented implementation for the tools.
It exposes 6 top-level standalone functions that serve as the ADK tools interfaces,
internally delegating execution to modular class instances.
"""

import os

# Load env variables from .env file manually to force override any stale OS shell credentials
try:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
except Exception:
    pass

# Clean Vertex AI conflict and force-forward the key
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
import json
import re
from pathlib import Path
from typing import Literal, List
from pydantic import BaseModel, Field

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
# Pydantic Schemas for Structured JSON evaluation
# ---------------------------------------------------------------------------

class CriterionEvaluation(BaseModel):
    band: float = Field(..., description="Điểm số lẻ từ 1.0 đến 6.5 (bước nhảy 0.5)")
    feedback: str = Field(..., description="Nhận xét ngắn gọn bằng tiếng Việt")
    suggestions: List[str] = Field(..., description="1-3 gợi ý cụ thể để cải thiện nâng band, bằng tiếng Việt")

class EssayEvaluationResponse(BaseModel):
    task_response: CriterionEvaluation
    coherence_cohesion: CriterionEvaluation
    lexical_resource: CriterionEvaluation
    grammatical_range: CriterionEvaluation


# ---------------------------------------------------------------------------
# Constants & Mappings
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
    ("two_part_question", "introduction"): "Paraphrase đề + báo sẽ trả lời cả 2 câu hỏi.",
    ("two_part_question", "body1"):        "Trả lời Câu hỏi 1: Topic sentence → Giải thích → Ví dụ.",
    ("two_part_question", "body2"):        "Trả lời Câu hỏi 2: Topic sentence → Giải thích → Ví dụ.",
    ("two_part_question", "conclusion"):   "Tóm tắt câu trả lời cho cả 2 câu hỏi ngắn gọn.",
}

_SECTION_NEXT: dict = {
    "introduction": "body1",
    "body1":        "body2",
    "body2":        "conclusion",
    "body3":        "conclusion",
    "conclusion":   None,
}

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

_OVERUSED_WORDS = {
    "good", "bad", "big", "large", "small", "show", "use", "think",
    "say", "problem", "help", "important", "change", "increase",
    "decrease", "people", "government", "need", "make",
}


# ---------------------------------------------------------------------------
# Infrastructure Classes (Reference Loading & Gemini SDK Communication)
# ---------------------------------------------------------------------------

class ReferenceRepository:
    """Class managing caching and reading reference files dynamically."""
    _REF_CACHE: dict[str, str] = {}

    @classmethod
    def load_ref(cls, filename: str) -> str:
        """Load a file from the references/ directory, caching it in memory."""
        if filename not in cls._REF_CACHE:
            ref_dir = Path(__file__).parent.parent / "references"
            try:
                cls._REF_CACHE[filename] = (ref_dir / filename).read_text(encoding="utf-8")
            except FileNotFoundError:
                cls._REF_CACHE[filename] = ""
        return cls._REF_CACHE[filename]


class GeminiServiceClient:
    """Service client responsible for API communication with Gemini Models."""

    @staticmethod
    def call_gemini(user_prompt: str, system_instruction: str = "") -> str:
        """Call Gemini model with fallback support and error logging."""
        if os.environ.get("MOCK_GEMINI", "").strip() == "1":
            return GeminiServiceClient._call_gemini_mock(user_prompt, system_instruction)

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
            # Fast path
            if response.text:
                return response.text

            # Fallback for thought content separation in candidates
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
            return json.dumps({"_api_error": type(exc).__name__, "_api_message": str(exc)[:300]})

    @staticmethod
    def safe_parse_json(raw: str):
        """Parse raw response JSON safely, rejecting sentinel error dicts."""
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "_api_error" in parsed:
                return None
            return parsed
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _call_gemini_mock(user_prompt: str, system_instruction: str = "") -> str:
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

        # ── fallback
        return json.dumps({"_mock": True, "status": "ok", "note": "fallback mock"})


# ---------------------------------------------------------------------------
# Business Logic Classes (OOP implementation of each ADK Tool)
# ---------------------------------------------------------------------------

class EssayTypeClassifier:
    """Class orchestrating the classification of IELTS Writing Task 2 essay types."""

    def classify(self, prompt: str) -> dict:
        if not prompt or not prompt.strip():
            return {"error": "Đề bài không được để trống."}

        prompt_lower = prompt.lower()

        # Step 1: Two-part question heuristic (2+ question marks)
        if self._is_two_part_question(prompt):
            kw_type, found_kw = self._keyword_classify(prompt_lower)
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
        kw_type, found_kw = self._keyword_classify(prompt_lower)
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
        test_cases_ref = ReferenceRepository.load_ref("test_cases.feature")
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
        raw = GeminiServiceClient.call_gemini(user_msg, system_instr)
        parsed = GeminiServiceClient.safe_parse_json(raw)

        if parsed and isinstance(parsed, dict) and "essay_type" in parsed:
            valid_types = {"opinion", "discussion", "adv_dis", "problem_solution", "two_part_question"}
            if parsed["essay_type"] in valid_types:
                return parsed

        return {
            "essay_type": None,
            "confidence": "low",
            "keywords_found": [],
            "explanation": "Không nhận diện được từ khoá đặc trưng và Gemini API không phản hồi.",
        }

    def _keyword_classify(self, prompt_lower: str) -> tuple:
        for essay_type, keywords in _CLASSIFICATION_RULES:
            found = [kw for kw in keywords if kw in prompt_lower]
            if found:
                return essay_type, found
        return None, []

    def _is_two_part_question(self, prompt: str) -> bool:
        return len(re.findall(r"\?", prompt)) >= 2


class PromptParaphraser:
    """Class orchestrating prompt paraphrasing suggestions based on target band level."""

    def paraphrase(self, prompt: str, level: Level = "B1") -> dict:
        if not prompt or not prompt.strip():
            return {"error": "Đề bài không được để trống."}

        vocab_ref = ReferenceRepository.load_ref("vocabulary_by_topic.md")
        template_ref = ReferenceRepository.load_ref("essay_templates.md")

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

        raw = GeminiServiceClient.call_gemini(user_msg, system_instr)
        parsed = GeminiServiceClient.safe_parse_json(raw)

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


class EssaySectionGuide:
    """Class orchestrating step-by-step section guidelines for writing essays."""

    def guide(self, section: Section, essay_type: EssayType, context: dict) -> dict:
        if not section or not essay_type:
            return {"error": "section và essay_type không được để trống."}

        template_ref = ReferenceRepository.load_ref("essay_templates.md")
        linking_ref = ReferenceRepository.load_ref("linking_words.md")

        brainstorm_map = {
            "opinion":           "opinion.feature",
            "discussion":        "discussion.feature",
            "adv_dis":           "adv_dis.feature",
            "problem_solution":  "problem_solution.feature",
            "two_part_question": "two_part_question.feature",
        }
        brainstorm_ref = ReferenceRepository.load_ref(brainstorm_map.get(essay_type, "essay_templates.md"))

        section_role = _SECTION_ROLE.get((essay_type, section), f"Viết phần {section} của {essay_type} essay.")
        level = context.get("level", "B1")
        essay_prompt = context.get("prompt", "")
        thesis = context.get("thesis", "")
        paraphrase = context.get("paraphrase", "")
        user_draft = context.get("user_draft", "")

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

        raw = GeminiServiceClient.call_gemini(user_msg, system_instr)
        parsed = GeminiServiceClient.safe_parse_json(raw)

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


class SentenceStructureSuggester:
    """Class orchestrating Grammatical Range and Accuracy (GRA) sentence updates."""

    def suggest(self, idea: str, level: Level = "B1") -> dict:
        if not idea or not idea.strip():
            return {"error": "Ý/câu không được để trống."}

        struct_ref = ReferenceRepository.load_ref("sentence_structures.md")
        linking_ref = ReferenceRepository.load_ref("linking_words.md")

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

        raw = GeminiServiceClient.call_gemini(user_msg, system_instr)
        parsed = GeminiServiceClient.safe_parse_json(raw)

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


class VocabularyEnricher:
    """Class orchestrating Lexical Resource (LR) suggestions and topic words."""

    def enrich(self, text: str, topic: str = "") -> dict:
        if not text or not text.strip():
            return {"error": "Đoạn văn không được để trống."}

        vocab_ref = ReferenceRepository.load_ref("vocabulary_by_topic.md")
        linking_ref = ReferenceRepository.load_ref("linking_words.md")

        overused_counts = self._detect_overused(text)
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
            "collocations (array of strings), "
            "improved_text (string đoạn văn đầy đủ đã được nâng cấp từ vựng), "
            "explanation (string tiếng Việt giải thích lý do nâng cấp). "
            "Không thêm bất kỳ text nào ngoài JSON."
        )

        user_msg = (
            f"Đoạn văn của user: \"{text}\"\n"
            f"Chủ đề (topic): {topic}\n"
            f"Từ lặp tự động đếm: {', '.join(overused_display)}\n\n"
            f"Từ vựng học thuật tham khảo:\n{vocab_ref[:1500]}\n\n"
            f"Collocations/Linking words tham khảo:\n{linking_ref[:800]}"
        )

        raw = GeminiServiceClient.call_gemini(user_msg, system_instr)
        parsed = GeminiServiceClient.safe_parse_json(raw)

        if parsed and isinstance(parsed, dict) and ("suggestions" in parsed or "topic_words" in parsed):
            if not parsed.get("overused_words"):
                parsed["overused_words"] = overused_display
            return parsed

        return {
            "error": "Không thể phân tích từ vựng. Vui lòng thử lại.",
            "overused_words": overused_display,
            "suggestions": {},
            "topic_words": [],
            "collocations": [],
            "improved_text": "",
            "explanation": "",
        }

    def _detect_overused(self, text: str) -> dict:
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


class IELTSEssayEvaluator:
    """Class orchestrating IELTS Writing Task 2 scoring and A2UI generation."""

    def evaluate(self, essay_text: str, essay_type: str) -> dict:
        if os.environ.get("MOCK_GEMINI", "").strip() == "1":
            return self._get_mock_evaluation(essay_text, essay_type)

        # Real API evaluation
        rubric_path = Path(__file__).parent.parent / "references" / "ielts_scoring_rubric.json"
        try:
            with open(rubric_path, "r", encoding="utf-8") as f:
                rubric_json = f.read()
        except Exception:
            rubric_json = "{}"

        grammar_path = Path(__file__).parent.parent / "references" / "sentence_structures.md"
        try:
            with open(grammar_path, "r", encoding="utf-8") as f:
                grammar_txt = f.read()
        except Exception:
            grammar_txt = ""

        prompt = (
            f"You are an expert IELTS Writing Task 2 examiner.\n"
            f"Evaluate the following student essay of type '{essay_type}' based on the provided IELTS simplified scoring rubric (from band 1.0 to 6.5).\n\n"
            f"Here is the simplified IELTS scoring rubric (mapping band scores to descriptions of student writing):\n"
            f"{rubric_json}\n\n"
            f"Here is the grammar reference containing target sentence structures we coached the student to use:\n"
            f"{grammar_txt}\n\n"
            f"Student Essay to evaluate:\n"
            f"\"\"\"\n{essay_text}\n\"\"\"\n\n"
            f"Guidelines for your evaluation:\n"
            f"1. Carefully analyze the student's essay.\n"
            f"2. For each of the four criteria (task_response, coherence_cohesion, lexical_resource, grammatical_range), assign a band score.\n"
            f"3. Specifically for 'grammatical_range' (Ngữ pháp), check if the student has attempted or correctly used the patterns defined in the grammar reference (such as 'Despite/In spite of', concession, active/passive voice, etc.). In the feedback and suggestions for 'grammatical_range', mention which specific target structures they used correctly and which ones they should attempt to use to improve their score.\n"
            f"4. The band score MUST be a float number chosen STRICTLY from the enum: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]. Do NOT assign any other score.\n"
            f"5. For each criterion, provide detailed 'feedback' (1-3 sentences) in Vietnamese explaining why this score was given, and 'suggestions' (1-3 items) in Vietnamese offering actionable advice for the student to improve.\n"
            f"6. All text in 'feedback' and 'suggestions' must be in Vietnamese."
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

                        overall_band = self._ielts_round(sum(bands) / 4.0)
                        word_count = len(essay_text.split())

                        res_dict = {
                            "overall_band": overall_band,
                            "criteria": processed_criteria,
                            "essay_type": essay_type,
                            "word_count": word_count,
                            "error": False
                        }
                        res_dict["ui_available"] = True
                        res_dict["ui"] = self._build_evaluation_a2ui(overall_band, processed_criteria, essay_type, word_count)
                        return res_dict
                except Exception as e:
                    err_str = str(e)
                    last_err = e
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        break

        err_msg = str(last_err) if last_err else "Lỗi kết nối hoặc API hết quota."
        return {
            "error": True,
            "message": f"Không thể kết nối đến máy chủ chấm điểm: {err_msg}"
        }

    def _ielts_round(self, avg: float) -> float:
        import math
        return math.floor(avg * 2 + 0.5) / 2

    def _get_mock_evaluation(self, essay_text: str, essay_type: str) -> dict:
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
        mock_result["ui"] = self._build_evaluation_a2ui(5.0, mock_result["criteria"], essay_type, words)
        return mock_result

    def _build_evaluation_a2ui(self, overall_band: float, criteria: dict, essay_type: str, word_count: int) -> dict:
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
            for s in suggestions:
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


# ---------------------------------------------------------------------------
# Facade Interface Wrapper Functions (ADK compatible, unmodified signatures)
# ---------------------------------------------------------------------------

def classify_essay_type(prompt: str) -> dict:
    """
    Phân loại dạng đề IELTS Writing Task 2 dựa trên từ khoá trong đề bài.
    """
    return EssayTypeClassifier().classify(prompt)


def paraphrase_prompt(prompt: str, level: Level = "B1") -> dict:
    """
    Tạo 3 cách paraphrase đề bài IELTS Writing Task 2 phù hợp với level người học.
    """
    return PromptParaphraser().paraphrase(prompt, level)


def guide_essay_section(section: Section, essay_type: EssayType, context: dict) -> dict:
    """
    Hướng dẫn viết từng phần cụ thể của bài essay IELTS Writing Task 2.
    """
    return EssaySectionGuide().guide(section, essay_type, context)


def suggest_sentence_structures(idea: str, level: Level = "B1") -> dict:
    """
    Gợi ý các cách viết câu phong phú hơn cho một ý (idea) của user.
    """
    return SentenceStructureSuggester().suggest(idea, level)


def enrich_vocabulary(text: str, topic: str = "") -> dict:
    """
    Phát hiện từ vựng đơn điệu hoặc bị lặp trong đoạn văn của user
    và gợi ý synonyms/collocations học thuật phù hợp hơn.
    """
    return VocabularyEnricher().enrich(text, topic)


def evaluate_essay(essay_text: str, essay_type: str) -> dict:
    """Đánh giá và chấm điểm toàn diện bài viết IELTS Writing Task 2.
    """
    return IELTSEssayEvaluator().evaluate(essay_text, essay_type)


# ---------------------------------------------------------------------------
# ADK Tools Registry
# ---------------------------------------------------------------------------
TOOLS = [
    classify_essay_type,
    paraphrase_prompt,
    guide_essay_section,
    suggest_sentence_structures,
    enrich_vocabulary,
]

