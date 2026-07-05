# Kaggle Writeup — Essay Writing Coach

> **Track**: Agents for Good (Education)

---

## Title

**Essay Writing Coach: AI Agent hướng dẫn người Việt viết IELTS Writing Task 2**

## Subtitle

Single-agent system built with Google ADK + Gemini, coaching Vietnamese learners (A2–B1) through essay writing step-by-step — not writing for them.

---

## 1. Problem Definition

Vietnamese IELTS learners at A2–B1 level face a specific pain point: they have ideas but cannot express them in academic English. Existing tools address symptoms but not the root cause:

- **Grammarly**: corrects errors in already-written text, but doesn't help users who can't start writing in the first place
- **ChatGPT**: generates complete essays on demand, but users learn nothing — they become dependent on the AI instead of developing their own skills
- **IELTS prep books**: provide templates but no interactive feedback on the learner's actual writing attempts

**The gap**: There is no tool that **coaches** learners through the writing process step-by-step, in their native language (Vietnamese), while ensuring the learner does the actual writing — not the AI.

**Target users**: Vietnamese IELTS candidates targeting band 5.0–6.0, at English proficiency level A2–B1, whose primary need is guided practice with immediate, personalized feedback.

**Potential Impact**: The demand for IELTS in Vietnam is exceptionally high, driven by policies from the Ministry of Education and Training (MoET) that allow IELTS scores to be used for high school graduation exemptions and direct university admissions. The average score of Vietnamese candidates is 6.2, with the most common score being 6.0 (representing 21% of test-takers) and over 60% belonging to the 16–22 age bracket. This project directly addresses this massive audience of A2–B1 learners struggling to cross the bridge from band 5.0 to 6.0 in Writing, providing a free, accessible, and interactive native-language coach.

---

## 2. Solution Design

### Core principle — Coach, not ghostwriter

The agent guides users through each section of the essay (Introduction → Body 1 → Body 2 → Conclusion) but **never writes content for them**. Users type their own sentences; the agent provides templates, examples, vocabulary suggestions, and grammar corrections — then explains *why* in Vietnamese so the learner actually improves.

### Architecture

Single-agent architecture using Google ADK (`LlmAgent`) with `gemini-2.5-flash`. The agent orchestrates 6 custom tools:

1. **classify_essay_type** — identifies essay type (opinion, discussion, advantages/disadvantages, problem-solution, two-part question) using keyword matching first, Gemini fallback only when ambiguous
2. **paraphrase_prompt** — generates 3 paraphrasing options at the learner's level (B1 only)
3. **guide_essay_section** — provides section-by-section guidance with templates, examples, useful phrases, common errors, and checklists
4. **suggest_sentence_structures** — transforms simple S+V+O sentences into more sophisticated academic structures appropriate for the learner's level
5. **enrich_vocabulary** — detects overused or repetitive words and suggests academic synonyms with Vietnamese explanations
6. **evaluate_essay** — scores the completed essay against the 4 official IELTS criteria (Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy), producing band scores in 0.5 increments (1.0–6.5)

### Level-adaptive behavior (A2 vs B1)

The agent adapts its coaching style based on proficiency:

- **B1 flow**: Classify → present 3 paraphrase options (wait for user choice) → guide section-by-section with templates → user writes full paragraphs independently → evaluate complete essay
- **A2 flow**: Classify → skip paraphrase (too complex at this level) → guide sentence-by-sentence → correct grammar errors individually with Vietnamese explanations → scaffold each sentence until the paragraph is complete → evaluate

### Why single-agent, not multi-agent

Evaluated during setup (Step 0 of the development process) and decided single-agent is sufficient: the 6 tools cover all needed capabilities, and adding orchestration complexity would increase latency and quota usage without proportional quality improvement. This decision is documented in `GEMINI.md` as a non-negotiable architectural constraint.

---

## 3. Key Concepts Demonstrated

### Concept 1: Agent Tools & Interoperability (Day 2)

Six custom tools built as plain Python functions with full type annotations and docstrings, registered via ADK's `tools` parameter. Each tool follows the consume-first principle: `classify_essay_type` uses deterministic keyword matching before falling back to LLM inference, minimizing API calls and cost.

**Evidence**: `tools.py` — 6 functions with structured JSON output, error handling returning `{"error": "..."}` instead of raising exceptions, and a shared `GeminiServiceClient` helper with module-level reference caching.

```python
# tools.py — Tool definition with docstring (agent reads this to decide when to call)
def classify_essay_type(prompt: str) -> dict:
    """Classify an IELTS Task 2 prompt into one of 5 essay types.
    Uses keyword matching first (zero API cost), falls back to
    Gemini only when keywords are ambiguous.
    """
    return EssayTypeClassifier().classify(prompt)

# agent.py — Registering 6 tools via Google ADK
root_agent = Agent(
    name="essay_writing_coach",
    model="gemini-2.5-flash",
    instruction=SYSTEM_PROMPT,
    tools=TOOLS,  # List of 6 plain Python functions
)
```

### Concept 2: Agent Security & Evaluation (Day 4)

**Security measures implemented**:

- API key never hardcoded in source — loaded from `.env` via environment variables. Full `grep` audit across all source files confirmed zero leaks. Git history verified clean.
- `MOCK_GEMINI` environment variable separates development from real API calls — prevents quota exhaustion during iterative development
- `.gitignore` prevents accidental commits of `.env` files; `.env.example` provided for reviewer setup
- Input validation in every tool — malformed input returns error dict, never crashes

**Evaluation approach**:

- Mock testing layer enabling full flow verification without API costs (`MOCK_GEMINI=1`)
- Separate test scripts (`test_e2e_scenarios.py` for full flow, `verify_real_level_flows.py` for live API)
- Real API E2E verification results:

| Flow | Turn | Input | Expected Tool | Actual Tool | Status |
|------|------|-------|--------------|------------|--------|
| B1 | 1 | Discussion prompt | `classify_essay_type` | `classify_essay_type` | **PASS** |
| B1 | 2 | User writes intro | `guide_essay_section` | `guide_essay_section` | **PASS** |
| B1 | 3 | Complete essay | `evaluate_essay` | `evaluate_essay` | **PASS** |

### Concept 3: Spec-Driven Vibe Coding (Day 5)

The entire development process followed the spec-driven workflow taught in the course:

- **`GEMINI.md`**: project context file auto-read by Antigravity IDE on every session — contains architectural constraints, mock conventions, model history, and collaboration rules
- **`level_flow_spec.md`**: detailed A2 vs B1 flow specification — discovered mid-development that the original spec lacked level-specific behavior, fed back into Step 1 (Spec) before coding
- **`conversation_flow_spec.md`**: state machine S1→S6 defining the coaching conversation flow with branching logic for each section

**8-step development process applied throughout**: Setup → Spec/Test → Skill/Tool → Code/Verify → Security → Evaluate → Review → Ship — with feedback loops (Step 8 → Step 1) when gaps were discovered.

### Concept 4 (Bonus): Agent Skills (Day 3)

`skills/writing-opinion-essays/SKILL.md` demonstrates the skill format with YAML frontmatter, trigger conditions (keyword list synchronized with `_CLASSIFICATION_RULES` in code), structure guidance, examples, and anti-patterns — including the core principle "coach, not ghostwriter".

---

## 4. Implementation Quality

### Tech stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Agent framework | Google ADK (`LlmAgent`) | v2.3.0 |
| LLM | Gemini 2.5 Flash | Fallback to flash-lite on quota errors |
| Frontend | TypeScript + React | Deployed on Vercel |
| Backend | FastAPI + Uvicorn | REST API for headless deployment |
| Development IDE | Antigravity | With Claude Sonnet 4.6 (Thinking) |

### Code quality

- **Separation of concerns**: `tools.py` (6 tools + OOP classes + Gemini helper), `agent.py` (LlmAgent + system prompt + runner), frontend (TypeScript + React) — clear separation, no circular dependencies
- **Error handling**: every tool returns `{"error": "..."}` on failure instead of crashing; frontend displays errors in Vietnamese without exposing stack traces
- **Mock layer**: `MOCK_GEMINI=1` flag enables full development without API costs — critical for free-tier development
- **Reference caching**: `_load_ref()` reads scoring rubric and brainstorm files once, cached in `_REF_CACHE` for the session lifetime
- **Code comments**: all files contain implementation comments explaining design decisions and architectural rationale, per rubric requirements

### Challenges encountered and resolved

1. **Model deprecation**: `gemini-2.0-flash` shut down June 2026 → migrated to `gemini-2.5-flash` → then tested `gemini-2.5-flash-lite` for higher free-tier quota
2. **Thinking mode empty responses**: `gemini-2.5-flash` returns thinking-only parts that ADK couldn't process → added `thinking_budget=0` in agent config + fallback text extraction
3. **IELTS scoring precision**: standard rounding gives 5.3 → 5.0, but IELTS uses 0.5 increments → implemented custom `_ielts_round()` using `floor(avg * 2 + 0.5) / 2`

---

## 5. User Value & Demo

### Walkthrough

A student begins by pasting an IELTS Writing Task 2 prompt into the chat interface. The interaction follows a structured coaching flow:

**Step 1 — Classification**: The agent calls `classify_essay_type` to identify the prompt format (e.g., Discussion Essay) and translates the prompt to Vietnamese so the learner fully understands the requirements.

**Step 2 — Guided Introduction**: The agent provides a writing template with useful academic phrases and a self-evaluation checklist. The student writes their own Introduction. The agent checks for common issues: copying the prompt verbatim (asks to rephrase), grammar/spelling errors (corrects with Vietnamese explanations), missing thesis statement (prompts to add), or off-topic content (redirects to the original prompt).

**Step 3 — Body Paragraphs**: For each body paragraph, the agent provides brainstorming scaffolding (topic sentence → explanation → example structure), then reviews the student's draft for coherence, vocabulary range, and grammatical variety. Tools `suggest_sentence_structures` and `enrich_vocabulary` fire automatically to offer improvements.

**Step 4 — Conclusion**: The agent checks that the conclusion summarizes both perspectives and includes the student's personal opinion — the two requirements most commonly missed by A2–B1 writers.

**Step 5 — Scoring**: The student requests evaluation. The agent calls `evaluate_essay` to score across 4 IELTS criteria, producing band scores in 0.5 increments with detailed Vietnamese feedback on what to improve.

### Live demo

- **Live app**: [Vercel deployment](https://kaggle-5-day-ai.vercel.app) | [HF Spaces backend](https://huggingface.co/spaces/htkchi2212/ielts-writing-coach)
- **Video demo**: [YouTube (≤5 min)](https://youtu.be/lT1Z8Zg0yH4)
- **Source code**: [GitHub](https://github.com/HoangThiKimChi/Kaggle-5-day-AI)

---

## 6. Future Work

- **MCP integration**: Google Drive MCP for saving essays to user's cloud storage; authentication MCP for persistent user profiles with progress tracking across sessions
- **Multi-agent architecture**: separate Grammar Agent (specialized for A2 error correction) from Structure Coach Agent (paragraph-level guidance for B1) — each using cost-optimized models
- **Internet search tool**: when A2 learners are stuck for ideas, the agent could search for relevant facts about the essay topic to provide brainstorming scaffolding
- **Spaced repetition**: integrate with Word Bag vocabulary app to reinforce words learned during essay writing sessions
- **Task 1 coverage**: extend beyond Task 2 to cover IELTS Writing Task 1 (charts, graphs, process diagrams)