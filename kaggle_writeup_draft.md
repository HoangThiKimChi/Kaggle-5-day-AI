# Kaggle Writeup — Essay Writing Coach

> **Track**: Agents for Good (Education)
> **Giới hạn**: ≤2,500 từ
> **File này là bản draft .md** — sau khi hoàn thiện sẽ copy nội dung sang
> Kaggle Writeup UI (không phải upload file, mà paste text vào form trên
> trang Kaggle competition).

---

## Title

**Essay Writing Coach: AI Agent hướng dẫn người Việt viết IELTS Writing Task 2**

## Subtitle

Single-agent system built with Google ADK + Gemini, coaching Vietnamese
learners (A2-B1) through essay writing step-by-step — not writing for them.

---

## 1. Problem Definition (~300 từ)

### Vấn đề

Vietnamese IELTS learners at A2-B1 level face a specific pain point: they
have ideas but cannot express them in academic English. Existing tools
address symptoms but not the root cause:

- **Grammarly**: corrects errors in already-written text, but doesn't help
  users who can't start writing in the first place
- **ChatGPT**: generates complete essays on demand, but users learn nothing
  — they become dependent on the AI instead of developing their own skills
- **IELTS prep books**: provide templates but no interactive feedback on
  the learner's actual writing attempts

### Gap

There is no tool that **coaches** learners through the writing process
step-by-step, in their native language (Vietnamese), while ensuring the
learner does the actual writing — not the AI.

### Target users

- Vietnamese IELTS candidates targeting band 5.0-6.0
- English proficiency level A2-B1
- Primary need: guided practice with immediate, personalized feedback

### Potential Impact

The demand for IELTS in Vietnam is exceptionally high, driven by policies from the Ministry of Education and Training (MoET) that allow IELTS scores to be used for high school graduation exemptions and direct university admissions. Statistics show that the average score of Vietnamese candidates is 6.2, with the most common score being 6.0 (representing 21% of test takers) and over 60% of test-takers belonging to the 16–22 age bracket. This project directly addresses this massive audience of A2-B1 learners who are currently struggling to cross the bridge from band 5.0 to 6.0 in Writing, providing a free, accessible, and interactive native-language coach.

---

## 2. Solution Design (~400 từ)

### Core principle — Coach, not ghostwriter

The agent guides users through each section of the essay (Introduction →
Body 1 → Body 2 → Conclusion) but **never writes content for them**. Users
type their own sentences; the agent provides templates, examples, vocabulary
suggestions, and grammar corrections — then explains *why* in Vietnamese so
the learner actually improves.

### Architecture

Single-agent architecture using Google ADK (`LlmAgent`) with
`gemini-2.5-flash-lite`. The agent orchestrates 5 custom tools:

1. **classify_essay_type** — identifies essay type (opinion, discussion,
   advantages/disadvantages, problem-solution, two-part question) using
   keyword matching first, Gemini fallback only when ambiguous
2. **paraphrase_prompt** — generates 3 paraphrasing options at the
   learner's level
3. **guide_essay_section** — provides section-by-section guidance with
   templates, examples, useful phrases, common errors, and checklists
4. **suggest_sentence_structures** — transforms simple S+V+O sentences
   into more sophisticated structures appropriate for the learner's level
5. **enrich_vocabulary** — detects overused/repetitive words and suggests
   academic synonyms with Vietnamese explanations

### Level-adaptive behavior (A2 vs B1)

The agent adapts its coaching style based on the learner's proficiency:

**B1 flow**: Classify → present 3 paraphrase options (wait for user
choice) → guide section-by-section with templates → user writes full
paragraphs independently.

**A2 flow**: Classify → skip paraphrase selection → guide sentence-by-
sentence → correct grammar errors individually with Vietnamese
explanations → scaffold each sentence until the paragraph is complete.

### Why single-agent, not multi-agent

Evaluated during setup (Step 0 of our development process) and decided
single-agent is sufficient: the 5 tools cover all needed capabilities,
adding orchestration complexity would increase latency and quota usage
without proportional quality improvement. This decision is documented in
`GEMINI.md` as a non-negotiable architectural constraint.

---

## 3. Key Concepts Demonstrated (~500 từ)

### Concept 1: Agent Tools & Interoperability (Day 2)

Five custom tools built as plain Python functions with full type
annotations and docstrings, registered via ADK's `tools` parameter.
Each tool follows the consume-first principle: `classify_essay_type`
uses deterministic keyword matching before falling back to LLM inference,
minimizing API calls and cost.

**Evidence**: `tools.py` — 5 functions with structured JSON output,
error handling returning `{"error": "..."}` instead of raising exceptions,
and a shared `_call_gemini()` helper with module-level reference caching.

**Tool Definition and Registration Snippet**:

```python
# tools.py — Defining plain Python functions as tools
def classify_essay_type(prompt: str) -> dict:
    """Phân loại dạng đề IELTS Writing Task 2 dựa trên từ khoá.
    
    Args:
        prompt: Đề bài IELTS Writing Task 2 (tiếng Anh)
    Returns:
        dict: keys gồm essay_type, confidence, explanation, v.v.
    """
    # Deterministic parsing followed by fallback LLM logic
    ...

# agent.py — Registering tools via Google ADK Agent
from google.adk.agents import Agent
from tools import TOOLS # Imported list of function tools

root_agent = Agent(
    name="essay_writing_coach",
    model="gemini-2.5-flash-lite",
    instruction=SYSTEM_PROMPT,
    tools=TOOLS, # Plain functions registered directly
    ...
)
```

### Concept 2: Agent Security & Evaluation (Day 4)

**Security measures implemented**:
- API key never hardcoded in source (detected and fixed during
  development when a find-replace accident leaked the key into `agent.py`)
- `MOCK_GEMINI` environment variable separates development/testing from
  real API calls — prevents quota exhaustion during iterative development
- `.gitignore` with Python template prevents accidental commits of
  `.env` files and `__pycache__`
- Full security audit: `grep` scan across all project files, confirmed
  no git history exposure (project initialized without git initially)

**Evaluation approach**:
- EDD (Evaluation-Driven Development): `eval_cases.json` with 5 test
  cases covering all 5 essay types, each specifying `expected_tool_calls`,
  `expected_output_format`, and `rubric` criteria
- Mock testing layer enabling full flow verification without API costs
- Separate test scripts (`test_streamlit_integration.py`,
  `test_level_flows.py`) documenting verification process

**Real API E2E Verification Results (`gemini-2.5-flash-lite`)**:

| Flow | Turn | Input | Expected Tool Calls | Actual Tool Calls | Status | Notes |
|---|---|---|---|---|---|---|
| **B1** | 1 | Opinion prompt | `classify_essay_type`, `paraphrase_prompt` | `classify_essay_type`, `paraphrase_prompt` | **PASS** | Classified as 'opinion' (high confidence); generated 3 level-appropriate paraphrasing options. |
| **B1** | 2 | Selected paraphrase & requested intro guide | `guide_essay_section` | `guide_essay_section` | **PASS** | Rendered detailed intro template, B1 example, useful phrases, and self-check list. Session context persisted. |
| **A2** | 1 | Opinion prompt | `classify_essay_type` | `classify_essay_type` | **PASS** | Classified essay and prompted user for initial ideas without overloading with complex templates. |
| **A2** | 2 | Simple sentence "i think music good" | `suggest_sentence_structures` or interactive prompt | Interactive guiding prompt | **PASS** | Identified grammar error, proposed correction, and asked guiding question to expand ideas. |

### Concept 3: Spec-Driven Vibe Coding (Day 5)

The entire development process followed the spec-driven workflow taught
in the course:

- **`GEMINI.md`**: project context file auto-read by Antigravity IDE on
  every session — contains architectural constraints, mock conventions,
  model history, and collaboration rules
- **`ui_spec.md`**: full UI specification with ASCII wireframe, Gherkin
  scenarios, and `st.session_state` data schema — written before any UI
  code
- **`full_spec_audit.md`**: technical audit identifying 3 blocking gaps
  (async/sync mismatch, session persistence, structured output) —
  resolved via prototype testing before full implementation
- **`level_flow_spec.md`**: detailed A2 vs B1 flow specification —
  discovered mid-development that the original spec lacked level-specific
  behavior, fed back into Step 1 (Spec) before coding
- **BDD Gherkin scenarios**: behavior-driven specifications for UI
  interactions (classify updates sidebar, error handling preserves panel
  state, session persistence across Streamlit reruns)

**8-step development process applied throughout**:
Setup → Spec/Test → Skill/Tool → Code/Verify → Security → Evaluate →
Review → Ship — with feedback loops (Step 8 → Step 1) when gaps were
discovered.

### Concept 4 (Bonus): Agent Skills (Day 3)

`skills/writing-opinion-essays/SKILL.md` demonstrates the skill format
with YAML frontmatter, trigger conditions (keyword list synchronized with
`_CLASSIFICATION_RULES` in code), structure guidance, examples, and
anti-patterns — including the core principle "coach, not ghostwriter".

---

## 4. Implementation Quality (~400 từ)

### Tech stack

| Component | Technology | Version |
|---|---|---|
| Agent framework | Google ADK (`LlmAgent`) | 2.3.0 |
| LLM | Gemini 2.5 Flash Lite | via `google-genai` SDK |
| Frontend | Streamlit | 1.58.0 |
| Deployment | Streamlit Community Cloud | Free tier |
| Development IDE | Antigravity IDE | With Claude Sonnet 4.6 (Thinking) |

### Code quality

- **Separation of concerns**: `tools.py` (5 tools + helpers),
  `agent.py` (LlmAgent + system prompt + runner), `app.py` (Streamlit UI)
  — 3 files, 3 responsibilities, no circular dependencies
- **Error handling**: every tool returns `{"error": "..."}` on failure
  instead of crashing; UI displays errors in Vietnamese without exposing
  raw JSON or stack traces
- **Mock layer**: `MOCK_GEMINI=1` flag in `tools.py` enables full
  development cycle without API costs — critical for free-tier development
- **Reference caching**: `_load_ref()` reads reference files once at
  module import, cached in `_REF_CACHE` dict for the session lifetime

### Challenges encountered and resolved

1. **Model deprecation**: `gemini-2.0-flash` shut down June 2026 →
   migrated to `gemini-2.5-flash` → then to `gemini-2.5-flash-lite` for
   higher free-tier quota
2. **Thinking mode empty responses**: `gemini-2.5-flash` returns
   thinking-only parts that ADK couldn't process → added
   `thinking_budget=0` in agent config + fallback text extraction from
   non-thought parts
3. **API key leak in code**: accidental find-replace embedded key value
   into variable name → detected via `grep` audit, confirmed no git
   history, implemented `.env` + `.gitignore` prevention

---

## 5. User Value & Demo (~300 từ)

A student begins by pasting an IELTS Writing Task 2 prompt in the chat. The interaction adapts dynamically:

1. **Automatic Parsing & Selection (Sidebar & Panel):**
   The agent calls `classify_essay_type` to identify the prompt format (e.g., Opinion Essay). The sidebar instantly updates with the detected category and confidence badge. 
2. **Step-by-Step Writing Scaffolding:**
   * **B1 Path:** The agent suggests 3 paraphrases in the right "Hướng dẫn" (Guidance) tab. The user chooses one, and the agent serves a writing template, academic collocations, and a self-evaluation checklist for the Introduction.
   * **A2 Path:** The agent skips paraphrase options (which can overwhelm A2 learners) and initiates an interactive brainstorming dialog, guiding the student to compose their essay sentence-by-sentence.
3. **Drafting and Synthesis:**
   In the right "Bài viết" (My Essay) tab, the user drafts their paragraph. When they click "Xong phần này" (Finish Section), the sidebar updates the checklist item from 🔲/⏳ to ✅. The agent automatically nudges them to begin the next section (e.g., Body 1), serving the next template.
4. **Final Compilation:**
   Once all four parts (Intro, Body 1, Body 2, Conclusion) are completed, the student can review and copy their compiled, cohesive essay in a single click.

*(We will embed screenshots of the 3-zone layout interface showing active progress indicators, real-time guidance instructions, and final consolidated essay outputs.)*

### Live Demo & Code Repository

**[Play the Live Demo on Hugging Face Spaces](https://huggingface.co/spaces/htkchi2212/ielts-writing-coach)**  
*(Lưu ý: Hệ thống được xây dựng trên Free Tier. Xin vui lòng đợi 1-2 phút nếu server đang khởi động).*

**[GitHub Code Repository](https://github.com/HoangThiKimChi/Kaggle-5-day-AI)**  

### Video

**[Xem Video Demo trên YouTube (3-5 phút)](https://youtu.be/lT1Z8Zg0yH4)**

---

## 6. Future Work (~200 từ)

- **Internet search tool**: when A2 learners are stuck for ideas, the
  agent could search for relevant facts about the essay topic to provide
  brainstorming scaffolding (currently shows a placeholder message)
- **Multi-agent architecture**: separate Grammar Agent (specialized for
  A2 error correction) from Structure Coach Agent (paragraph-level
  guidance for B1) — each using cost-optimized models
- **MCP integration**: Google Drive MCP for saving essays to user's
  cloud storage; authentication MCP for persistent user profiles with
  progress tracking across sessions
- **Spaced repetition**: integrate with Word Bag vocabulary app (planned
  .NET portfolio project) to reinforce vocabulary learned during essay
  writing sessions
- **Additional essay types**: extend beyond Task 2 to cover IELTS
  Writing Task 1 (charts, graphs, process diagrams)

---

## Attachments Checklist

- [x] Cover image (screenshot of app UI, 3-zone layout)
- [x] 2-3 additional screenshots in Media Gallery
- [x] Video demo ≤5 phút, uploaded to YouTube
- [x] Public Project Link (Hugging Face Spaces URL)
- [x] Public Code Repository Link (GitHub URL)
- [x] Track selected: "Agents for Good"
- [x] Word count ≤2,500 (Verified: 2,083 words)

---

> **Ghi chú nội bộ (xóa trước khi submit)**:
> - Các chỗ `<!-- TODO -->` cần điền sau khi có: screenshot thật, link
>   deploy, link YouTube, kết quả verify thật, version number chính xác
> - Đếm từ trước khi submit — giới hạn 2,500 từ, hiện tại khung này
>   ~1,800 từ (chưa tính TODO), còn margin ~700 từ để điền nội dung thật
> - Writeup paste vào Kaggle UI (không phải upload file .md) — nhưng
>   viết ở .md trước để version control + review dễ hơn
