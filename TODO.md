## Tổng quan — 7 Phase

```
Phase 0: Spec & Harness Setup        ← Day 1, 5
Phase 1: Tools Implementation         ← Day 2
Phase 2: Agent Core (Loop + Memory)   ← Day 1, 2, 3
Phase 3: Skills (Optional, nâng cao)  ← Day 3
Phase 4: Eval & Security              ← Day 3, 4
Phase 5: UI Layer                     ← Day 5
Phase 6: Deploy & Observability       ← Day 5
Phase 7: Capstone Submission          ← Day 5
```

## Phase 0 — Spec & Harness Setup (Day 1, 5)

**Mục tiêu**: Viết spec TRƯỚC khi code (inversion path).

- [ ] **0.1** Vẽ 6 flow chính (tra từ mới, tra từ cũ, extract unknown, review, grade, gợi ý từ liên quan)
- [ ] **0.2** Viết intent doc cho 6 flow (WHEN + MUST + MUST NOT + EDGE CASES)
- [ ] **0.3** Generate BDD Gherkin scenarios từ intent doc
- [ ] **0.4** Tạo `AGENTS.md` — identity, rules, tool selection priority
- [ ] **0.5** Tạo `GEMINI.md` (project-specific, prioritize hơn AGENTS.md cho Gemini CLI)
- [ ] **0.6** Setup repo structure: `/agent`, `/tools`, `/evals`, `/skills`, `/ui`, `/docs`
- [ ] **0.7** Setup dev harness: Python venv, `requirements.txt` (google-adk hoặc langgraph, gemini-api, streamlit, sqlite)
- [ ] **0.8** Setup `.env` cho GEMINI_API_KEY + `.gitignore`

## Phase 1 — Tools Implementation (Day 2)

**Mục tiêu**: 6-7 tools với function declarations chuẩn.

- [ ] **1.1** Define tool list + signature trong `tools.py` (chưa implement)
  - `dictionary_lookup(term)` — gọi Free Dictionary API
  - `query_user_history(term)` — check word trong bag
  - `save_lookup(term, meaning, example, tense)` — persist
  - `generate_example(term, user_level)` — Gemini sub-call
  - `extract_unknown_words(text)` — diff text vs bag
  - `get_due_reviews()` — query SM-2 due
  - `grade_review(word_id, quality)` — update SM-2 state
- [ ] **1.2** Viết tool docstring tốt (đây là phần Gemini đọc để chọn tool — quan trọng)
- [ ] **1.3** Implement từng tool kèm error handling
- [ ] **1.4** Test mỗi tool độc lập với pytest (unit test, chưa cần agent)
- [ ] **1.5** (Optional) Wrap database access bằng MCP server local — show interoperability

## Phase 2 — Agent Core (Day 1, 2, 3)

**Mục tiêu**: Agent loop chạy được end-to-end.

- [ ] **2.1** Chọn framework: Google ADK (khóa dạy) hoặc LangGraph
- [ ] **2.2** Init Gemini client + register tools
- [ ] **2.3** Implement main agent loop (think → tool call → observe → respond)
- [ ] **2.4** Implement short-term memory (conversation context window)
- [ ] **2.5** Implement long-term memory (SQLite — chính là Word Bag DB)
- [ ] **2.6** Schema DB: `Word`, `Lookup`, `ReviewState`, `Session`
- [ ] **2.7** Implement SM-2 algorithm trong service layer (testable riêng)
- [ ] **2.8** Implement context engineering: load user profile + recent activity vào system prompt
- [ ] **2.9** Add logging (mỗi turn log: input, tool calls, output, latency, tokens)

## Phase 3 — Skills (Day 3, nâng cao, optional cho v1)

**Mục tiêu**: Modular expertise loaded on-demand. Skip phase này nếu thiếu thời gian.

- [ ] **3.1** Xác định 2-3 skill candidates:
  - `vstep-vocab-skill` — danh sách từ VSTEP B1 + tips
  - `pronunciation-skill` — IPA + audio guidance
  - `etymology-skill` — gốc từ Latin/Greek cho dễ nhớ
- [ ] **3.2** Viết `SKILL.md` cho mỗi skill (description trigger phải chính xác)
- [ ] **3.3** Test trigger accuracy ≥ 90% trước khi ship (theo guidance Day 3)

## Phase 4 — Eval & Security (Day 3, 4)

**Mục tiêu**: Evidence-based quality + safety.

**Evaluation (Day 3 — Evaluation Toolkit)**:
- [ ] **4.1** Tạo Golden Dataset (`evals/golden.json`) — 15-20 cases
- [ ] **4.2** Implement Eval Runner (`run_evals.py`) — chạy golden, compare trajectory
- [ ] **4.3** Add Eval-as-Unit-Test (chạy mỗi commit)
- [ ] **4.4** LLM-as-Judge cho subjective output (chất lượng example sentence)
- [ ] **4.5** Adversarial cases — 5 negative cases (input lạ, prompt injection)
- [ ] **4.6** Tính `pass@1` và `pass^3` (Day 3 nhấn mạnh consistent success)

**Security (Day 4)**:
- [ ] **4.7** Sandbox: tool calls có timeout, không direct shell access
- [ ] **4.8** Policy: `policies.yaml` — block tool nguy hiểm, allow read-only by default
- [ ] **4.9** Input validation: sanitize user input trước khi cho vào DB
- [ ] **4.10** Guardrails: agent KHÔNG được tự ý delete word, KHÔNG được leak API key
- [ ] **4.11** PII consideration: app này lưu vocab cá nhân — note trong README

## Phase 5 — UI Layer (Day 5)

**Mục tiêu**: User chạm được, demo được.

- [ ] **5.1** Chọn UI framework: Streamlit (đơn giản nhất, đủ cho capstone)
- [ ] **5.2** 3 màn chính:
  - Chat interface (main lookup + conversational)
  - Word bag viewer (list, search, filter)
  - Review mode (flashcard với grade buttons)
- [ ] **5.3** Show agent trajectory cho transparency (debug + impress judge)
- [ ] **5.4** Show citation: "Definition from Free Dictionary API"

## Phase 6 — Deploy & Observability (Day 5)

**Mục tiêu**: Production-ready hoặc gần như vậy.

- [ ] **6.1** Containerize: `Dockerfile` cho app + `docker-compose.yml`
- [ ] **6.2** Deploy lên Render.com free tier (đã chốt)
- [ ] **6.3** Observability:
  - Structured logging (JSON logs)
  - Tracing mỗi agent turn (input → tools → output → cost → latency)
  - Cost tracking (tokens × Gemini price)
- [ ] **6.4** Health check endpoint
- [ ] **6.5** Error monitoring (Sentry free tier hoặc log file)

## Phase 7 — Capstone Submission (Day 5)

**Mục tiêu**: Đủ deliverables để submit Kaggle 6/7/2026.

- [ ] **7.1** Kaggle Notebook (yêu cầu bắt buộc của capstone):
  - Code agent đầy đủ, runnable
  - Markdown cells giải thích design decisions
  - Demo trajectory examples
- [ ] **7.2** Writeup (blog post / Medium):
  - Problem statement
  - Architecture diagram
  - Tool design rationale
  - Eval results
  - Lessons learned
- [ ] **7.3** Demo video 3-5 phút (record bằng OBS / Loom)
- [ ] **7.4** GitHub repo public với README chỉn chu
- [ ] **7.5** Submit form Kaggle track "Agents for Good"

---

## Timeline đề xuất (đến 6/7)

| Tuần | Phase | Việc chính |
|---|---|---|
| 25-28/6 (Tuần 1) | **0 + 1** | Spec + Tools (foundation) |
| 29/6 - 2/7 (Tuần 2 đầu) | **2 + 4** | Agent core + Eval (cùng lúc) |
| 3-5/7 (Tuần 2 cuối) | **5 + 6** | UI + Deploy |
| 6/7 (Submission day) | **7** | Writeup + submit |

**Bỏ qua trong v1 (capstone)**: Phase 3 Skills (làm sau, không bắt buộc cho capstone pass).

---

## Định lượng effort

| Phase | Effort (giờ) | Khó? |
|---|---|---|
| 0 - Spec | 4-6h | Dễ, chủ yếu suy nghĩ |
| 1 - Tools | 8-12h | Trung bình, nhiều I/O code |
| 2 - Agent core | 12-16h | Khó nhất, debug nhiều |
| 4 - Eval & Security | 6-8h | Trung bình |
| 5 - UI | 4-6h | Dễ với Streamlit |
| 6 - Deploy | 3-5h | Trung bình, lần đầu lâu |
| 7 - Submission | 4-6h | Dễ, chủ yếu viết |
| **Tổng** | **~40-60h** | ~3-5h/ngày × 12 ngày |

Khả thi nếu Chi tập trung, có thể overlap với học VSTEP buổi tối.

---

Chi muốn bắt đầu phase nào trước? Khuyên **Phase 0.1 — vẽ 6 flow** vì đây là output Chi sở hữu hoàn toàn, mọi phase sau dựa vào.

Hay Chi muốn mình tạo luôn **repo skeleton** (folder structure + file stubs + `AGENTS.md` + `requirements.txt`) để Chi bắt đầu code ngay?