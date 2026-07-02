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
Actual LLM calls will be made via Google ADK tool invocation.
"""

from typing import Literal

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
# Tool 1 — classify_essay_type
# ---------------------------------------------------------------------------

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
            "keywords_found": ["to what extent", "agree or disagree"],
            "explanation": "Đề dùng 'to what extent do you agree or disagree' — "
                           "đây là dấu hiệu rõ ràng của Opinion essay. "
                           "Bạn cần nêu rõ ý kiến cá nhân và bảo vệ quan điểm đó."
        }

    Reference: references/opinion_brainstorm.md, references/discussion_brainstorm.md,
               references/adv_dis_brainstorm.md, references/problem_solution_brainstorm.md,
               references/two_part_question_brainstorm.md, references/test_cases.md
    """
    # Implementation: ADK will call Gemini with the prompt and classification rules
    pass


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
          e.g. "music brings people together" → "music helps unite people from different backgrounds"
    - B1: Synonyms học thuật + đổi cấu trúc câu (passive voice, noun phrase)
          e.g. "It has been argued that music serves as a universal language..."

    PARAPHRASE TECHNIQUES (3 cách tạo ra 3 options):
    1. Synonym substitution: thay các content words bằng synonyms
    2. Structure change: đổi cấu trúc câu (active→passive, verb→noun phrase)
    3. Perspective shift: đổi góc nhìn ("some people think" → "it is widely believed that")

    Args:
        prompt: Đề bài gốc (tiếng Anh)
        level:  "A2" hoặc "B1" — ảnh hưởng độ phức tạp của từ vựng và cấu trúc

    Returns:
        dict với keys:
        - original: đề gốc
        - paraphrases: list 3 cách paraphrase (mỗi item có "text" và "technique")
        - explanation: giải thích ngắn bằng tiếng Việt về cách paraphrase
        - common_synonyms: dict các từ quan trọng → synonyms gợi ý

    Example:
        >>> paraphrase_prompt(
        ...     "The working week should be shorter and workers should have a longer weekend.",
        ...     level="B1"
        ... )
        {
            "original": "The working week should be shorter and workers should have a longer weekend.",
            "paraphrases": [
                {
                    "text": "It has been suggested that employees would benefit from reduced working hours and an extended weekend.",
                    "technique": "passive + synonyms (workers→employees, shorter→reduced, longer→extended)"
                },
                {
                    "text": "There is growing support for the idea that the standard working week should be condensed, giving workers more leisure time at weekends.",
                    "technique": "noun phrase opening + synonyms"
                },
                {
                    "text": "Many people argue that reducing the number of working days per week would benefit employees.",
                    "technique": "perspective shift + simplification (A2-friendly)"
                }
            ],
            "explanation": "Ba cách paraphrase trên dùng: (1) passive voice + synonyms học thuật, "
                           "(2) mở đầu bằng noun phrase, (3) đơn giản hơn phù hợp với A2.",
            "common_synonyms": {
                "workers": ["employees", "the workforce", "staff"],
                "shorter": ["reduced", "condensed", "fewer"],
                "longer": ["extended", "additional", "more"]
            }
        }

    Reference: references/essay_templates.md (Introduction section),
               references/linking_words.md,
               references/opinion_brainstorm.md (Introduction — Cách viết)
    """
    pass


# ---------------------------------------------------------------------------
# Tool 3 — guide_essay_section
# ---------------------------------------------------------------------------

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

    NỘI DUNG HƯỚNG DẪN THEO ESSAY_TYPE + SECTION:
    ┌─────────────────┬────────────────────┬────────────────────┬──────────────────┐
    │ essay_type      │ body1              │ body2              │ body3            │
    ├─────────────────┼────────────────────┼────────────────────┼──────────────────┤
    │ opinion         │ Reason 1 + example │ Reason 2 + example │ —                │
    │ discussion      │ View A + evidence  │ View B + evidence  │ —                │
    │ adv_dis         │ Advantages         │ Disadvantages      │ —                │
    │ problem_solution│ Causes/Problems    │ Solutions          │ (optional)       │
    │ two_part_question│ Answer Q1         │ Answer Q2          │ —                │
    └─────────────────┴────────────────────┴────────────────────┴──────────────────┘

    CONTEXT DICTIONARY (thông tin từ các bước trước):
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

    Example:
        >>> guide_essay_section(
        ...     section="introduction",
        ...     essay_type="opinion",
        ...     context={
        ...         "prompt": "Music brings people of different cultures together. To what extent do you agree?",
        ...         "paraphrase": "It has been suggested that music serves as a universal language...",
        ...         "thesis": "I strongly agree",
        ...         "level": "B1"
        ...     }
        ... )
        {
            "section": "introduction",
            "instructions": [
                "1. Bắt đầu bằng câu paraphrase đề (KHÔNG copy nguyên văn)",
                "2. Nêu rõ ý kiến của bạn (agree/disagree)",
                "3. Giới thiệu ngắn sẽ trình bày những gì trong bài"
            ],
            "template": "[Paraphrase đề]. I [strongly agree/disagree] with this view [for two main reasons / and in this essay I will explain why].",
            "example": "It has been suggested that music serves as a universal language, capable of uniting people from vastly different cultural backgrounds. I strongly agree with this view, and in this essay I will explain two key reasons for my position.",
            "useful_phrases": [
                "It has been suggested that...",
                "There is growing debate about...",
                "I strongly agree/disagree with this view because...",
                "This essay will examine..."
            ],
            "common_errors": [
                "Đừng copy nguyên văn từ đề bài",
                "Đừng viết quá dài — introduction chỉ cần 2-3 câu",
                "Phải nêu rõ thesis (agree/disagree) — không để mơ hồ"
            ],
            "checklist": [
                "Câu đầu có phải paraphrase thực sự không (không lặp từ nguyên văn)?",
                "Có thesis statement rõ ràng chưa?",
                "Có nêu sẽ làm gì trong bài không?"
            ]
        }

    Reference: references/essay_templates.md, references/opinion_brainstorm.md,
               references/discussion_brainstorm.md, references/adv_dis_brainstorm.md,
               references/problem_solution_brainstorm.md,
               references/two_part_question_brainstorm.md,
               references/linking_words.md
    """
    pass


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
          + synonyms cơ bản
    - B1: Gợi ý transformation patterns phức tạp hơn
          + academic linking words (nevertheless, consequently, despite)

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

    Example:
        >>> suggest_sentence_structures(
        ...     "Technology is good. It saves time. People can shop online.",
        ...     level="B1"
        ... )
        {
            "original": "Technology is good. It saves time. People can shop online.",
            "variations": [
                {
                    "text": "Technology offers significant benefits, particularly in terms of saving time. For example, people can now shop online instead of travelling to physical stores.",
                    "pattern": "S+V+O expansion + For example"
                },
                {
                    "text": "With the rise of technology, people are able to save time on everyday tasks such as shopping, which can now be done entirely online.",
                    "pattern": "With + noun phrase (result) + relative clause"
                },
                {
                    "text": "Technology has not only saved people time but also made shopping more accessible by enabling online purchases.",
                    "pattern": "Not only... but also (addition)"
                },
                {
                    "text": "Although technology has its drawbacks, it is undeniably beneficial in terms of time-saving, as online shopping demonstrates.",
                    "pattern": "Although (concession) + evidence"
                }
            ],
            "explanation": "Câu gốc lặp cấu trúc S+V+O 3 lần liên tiếp. Các biến thể trên dùng: "
                           "(1) mở rộng + ví dụ, (2) With + noun phrase, "
                           "(3) not only...but also, (4) although (nhượng bộ).",
            "level_note": "B1: variations 1-4 đều phù hợp. Variation 2-4 nâng cao hơn một chút.",
            "avoid": [
                "Tránh viết 3-4 câu ngắn liên tiếp cùng cấu trúc S+V+O",
                "Tránh bắt đầu nhiều câu bằng 'I think' hoặc 'I believe'",
                "Tránh dùng 'and' quá nhiều để nối ý"
            ]
        }

    Reference: references/sentence_structures.md (Sam McCarter patterns),
               references/linking_words.md (discourse markers)
    """
    pass


# ---------------------------------------------------------------------------
# Tool 5 — enrich_vocabulary
# ---------------------------------------------------------------------------

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
    - environment: emission, carbon footprint, biodiversity, sustainable, deforestation...
    - technology:  innovation, connectivity, cyberbullying, automation, privacy...
    - education:   curriculum, compulsory, critical thinking, vocational training...
    - work:        productivity, unemployment, gig economy, burnout, collaboration...
    - health:      sedentary, obesity, well-being, preventable, ageing population...
    - society:     globalisation, diversity, urbanisation, social cohesion, inequality...
    - transport:   congestion, commute, sustainable transport, carbon emission...
    - food:        food security, contamination, dietary habit, food waste...
    - crime:       deterrent, rehabilitation, recidivism, incarceration...
    - family:      nuclear family, upbringing, cohabitation, fertility rate...
    - media:       censorship, propaganda, fake news, regulation, bias...
    - science:     breakthrough, peer review, genetic engineering, hypothesis...

    COLLOCATIONS (từ Mindset L3 + Pauline Cullen):
    - have a significant impact on
    - play a crucial role in
    - be closely linked to
    - raise awareness of
    - tackle the problem of
    - contribute to
    - lead to / result in

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

    Example:
        >>> enrich_vocabulary(
        ...     "Technology is very good for people. It helps people do many things. "
        ...     "People use technology every day. Technology is important.",
        ...     topic="technology"
        ... )
        {
            "overused_words": ["technology (4x)", "people (3x)", "good", "important"],
            "suggestions": {
                "good": [
                    {"word": "beneficial",   "meaning_vi": "có lợi",           "example": "Technology is highly beneficial for modern society.", "register": "formal"},
                    {"word": "advantageous", "meaning_vi": "có lợi thế",       "example": "Online learning is advantageous for remote students.",  "register": "formal"},
                    {"word": "valuable",     "meaning_vi": "có giá trị",       "example": "Digital skills are increasingly valuable in the workplace.", "register": "neutral"},
                ],
                "people": [
                    {"word": "individuals",  "meaning_vi": "các cá nhân",      "example": "Technology enables individuals to work from anywhere.", "register": "formal"},
                    {"word": "the public",   "meaning_vi": "công chúng",       "example": "The public has embraced digital banking rapidly.",      "register": "neutral"},
                    {"word": "society",      "meaning_vi": "xã hội",           "example": "Technology has transformed how society communicates.",  "register": "formal"},
                ],
                "important": [
                    {"word": "crucial",      "meaning_vi": "cực kỳ quan trọng","example": "Digital literacy is crucial in the 21st century.",      "register": "formal"},
                    {"word": "essential",    "meaning_vi": "thiết yếu",        "example": "Internet access is now essential for education.",       "register": "formal"},
                    {"word": "significant",  "meaning_vi": "đáng kể",          "example": "Technology plays a significant role in modern life.",   "register": "formal"},
                ]
            },
            "topic_words": [
                {"word": "innovation",    "meaning_vi": "đổi mới sáng tạo", "example": "Technological innovation has transformed daily life."},
                {"word": "connectivity",  "meaning_vi": "khả năng kết nối", "example": "The internet has improved global connectivity enormously."},
                {"word": "automation",    "meaning_vi": "tự động hoá",      "example": "Automation is replacing many manual jobs."},
            ],
            "collocations": [
                "Technology plays a crucial role in modern society.",
                "Digital tools have had a significant impact on education.",
                "Technology is closely linked to economic growth.",
            ],
            "improved_text": "Technology is highly beneficial for modern society. It enables individuals to accomplish many tasks more efficiently. Digital tools are now an essential part of daily life, playing a crucial role in communication, education, and commerce.",
            "explanation": "Từ 'technology' bị lặp 4 lần — dùng 'digital tools', 'it', hoặc 'such innovation' để thay thế. "
                           "Từ 'people' nên đổi thành 'individuals' hoặc 'society' cho học thuật hơn. "
                           "Thêm collocations như 'play a crucial role in' để câu tự nhiên và học thuật hơn."
        }

    Reference: references/vocabulary_by_topic.md (12 topics × 20-22 words),
               references/linking_words.md (collocations section),
               references/sentence_structures.md
    """
    pass


# ---------------------------------------------------------------------------
# Tool registry (cho ADK agent)
# ---------------------------------------------------------------------------

TOOLS = [
    classify_essay_type,
    paraphrase_prompt,
    guide_essay_section,
    suggest_sentence_structures,
    enrich_vocabulary,
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
        "Hướng dẫn viết từng phần cụ thể: introduction, body1, body2, conclusion. "
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
}


if __name__ == "__main__":
    # Quick sanity check — print tool names and signatures
    import inspect
    for tool in TOOLS:
        sig = inspect.signature(tool)
        print(f"✅ {tool.__name__}{sig}")
    print(f"\nTotal tools: {len(TOOLS)}")
