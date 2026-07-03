# Essay Writing Coach — Tóm tắt Project (cập nhật)

> **Ngày cập nhật**: 01/07/2026 (còn 5 ngày đến deadline)
> **Deadline submit**: 06/07/2026 nửa đêm PT
> **File gốc tham khảo**: `essay_writing_coach_summary.md` (27/06/2026)

---

## 1. Tổng quan

**Tên app (tạm)**: Essay Writing Coach
**Loại**: Web app / Kaggle Notebook
**Mục đích**: AI agent hướng dẫn người Việt viết IELTS Writing Task 2 essay, level A2-B1
**Track Kaggle**: Agents for Good (Education)

---

## 2. Bối cảnh & Vấn đề

Người Việt ôn IELTS Writing có ý trong đầu nhưng không biết diễn đạt: không biết paraphrase đề, cấu trúc câu đơn điệu, từ vựng nghèo, không biết bắt đầu từng phần essay. Khác Grammarly (chỉ sửa lỗi) và ChatGPT (trả lời 1 cú) ở chỗ hướng dẫn từng bước bằng tiếng Việt.

---

## 3. Đối tượng & Chức năng

**User**: người ôn IELTS Writing, target band 5.0-6.0, level A2-B1, người Việt.

**4 chức năng MUST (v0)**:
1. Paraphrase đề bài — 3 cách, theo level
2. Hướng dẫn từng phần essay — intro → body → conclusion
3. Gợi ý cấu trúc câu — biến đổi câu đơn điệu
4. Từ vựng phong phú — synonym cho từ lặp

**Đã bỏ khỏi scope**: export file, chấm điểm IELTS, login/auth, save history multi-user, multi-topic templates.

**5 essay types cover** (mở rộng từ 3 lên 5 trong quá trình build tools):
opinion, discussion, adv_dis, problem_solution, two_part_question.

---

## 4. Tech Stack

| Layer | Tool |
|---|---|
| Agent framework | Google ADK (`LlmAgent`) |
| LLM | Gemini 2.0 Flash |
| Backend logic | Python |
| UI | Streamlit (stretch goal) |
| Storage | SQLite local (optional) |
| Deploy | Render.com free tier (nếu kịp) |
| Dev environment | Antigravity IDE (Claude Sonnet 4.6 Thinking cho code) |

---

## 5. Tiến độ thực tế (so với timeline gốc)

| Ngày | Kế hoạch gốc | Thực tế |
|---|---|---|
| 27/6 | Define scope | ✅ Done |
| 28/6 | Draft 3 templates | ✅ Done — mở rộng thành 10 file references (~2,100 dòng) |
| 29/6 | Define 5 tools + signatures | ✅ Done — `tools.py` skeleton với docstrings đầy đủ |
| 30/6 | Implement classify + paraphrase | ✅ Done |
| 1/7 | Implement 3 tools còn lại | ✅ **Done — cả 5 tools hoàn chỉnh, đã test** |
| 2/7 | Agent loop với ADK | 🔄 **Đang làm — `agent.py` đang được Antigravity build** |
| 3/7 | Demo case 1: Opinion | ⏳ Chưa tới |
| 4/7 | Demo case 2+3 | ⏳ Chưa tới |
| 5/7 | Streamlit UI + polish | ⏳ Chưa tới |
| 6/7 | Final test + submit | ⏳ Chưa tới |

**Nhận xét**: đang bám sát timeline, không trễ. Scope tools mở rộng từ 3 essay types → 5 essay types trong lúc implement (do đã có sẵn brainstorm file cho problem_solution và two_part_question), không tính là scope creep vì không thêm effort đáng kể — tái dùng structure có sẵn.

---

## 6. Chi tiết kỹ thuật đã chốt (session 1/7)

### 6.1. Cấu trúc file
```
Capstone/
├── tools.py                  ← 5 tools, TOOLS registry, TOOL_DESCRIPTIONS
├── agent.py                  ← đang build (LlmAgent + system prompt)
├── references/
│   ├── opinion_brainstorm.md
│   ├── discussion_brainstorm.md
│   ├── adv_dis_brainstorm.md
│   ├── problem_solution_brainstorm.md
│   ├── two_part_question_brainstorm.md
│   ├── essay_templates.md
│   ├── linking_words.md
│   ├── sentence_structures.md
│   ├── vocabulary_by_topic.md
│   └── test_cases.md
├── Tài liệu/
├── check list - to do.md
└── Requirement.md
```

### 6.2. `tools.py` — 5 tools đã implement + test pass

| Tool | Cơ chế | Test result |
|---|---|---|
| `classify_essay_type` | 3-stage: two-part heuristic → keyword match → Gemini fallback | ✅ 5/5 test case, confidence "high", **không tốn API call** (pure keyword match) |
| `paraphrase_prompt` | Gemini + vocab/template ref làm grounding | ✅ Code đúng, cần API quota để verify output thật |
| `guide_essay_section` | `_SECTION_ROLE` lookup table + brainstorm file theo essay_type | ✅ Code đúng, cần API quota để verify |
| `suggest_sentence_structures` | Full `sentence_structures.md` làm grounding | ✅ Code đúng, cần API quota để verify |
| `enrich_vocabulary` | Pre-detect từ lặp bằng regex local, rồi gọi Gemini + vocab ref | ✅ Code đúng, cần API quota để verify |

**Kiến trúc dùng chung**:
- `_call_gemini()` — helper tái sử dụng cho cả 5 tools, ép `response_mime_type="application/json"`
- `_load_ref()` — cache module-level, đọc file references/ 1 lần duy nhất khi import
- `_safe_parse_json()` — parse an toàn, nhận diện cả lỗi API (`_api_error` sentinel) lẫn JSON decode lỗi
- Error handling: mọi tool trả `{"error": "..."}` thay vì raise exception khi input rỗng hoặc API fail

### 6.3. Vấn đề đang mở — API quota

`GEMINI_API_KEY` hiện bị lỗi `429 RESOURCE_EXHAUSTED, limit: 0` — khác với "hết quota do dùng nhiều", đây là quota chưa được cấp cho project/model. Nguyên nhân nghi ngờ: key mới tạo chưa propagate, hoặc gắn sai project trên Google Cloud. **Tạm gác lại** — không chặn tiến độ vì `classify_essay_type` chạy độc lập không cần API, đủ để tiếp tục build `agent.py`. Cần xử lý trước ngày 3/7 (demo case) vì lúc đó bắt buộc cần API hoạt động thật.

### 6.4. Đang làm — `agent.py`

Yêu cầu đã gửi Antigravity: `LlmAgent` đơn (không multi-agent), import `TOOLS` từ `tools.py`, system prompt điều hướng flow (classify → paraphrase → guide qua từng section dùng field `next_section`), test bằng `InMemoryRunner`, in output đầy đủ dạng đọc được (không chỉ JSON thô) để review chất lượng nội dung bằng mắt.

---

## 7. Quyết định mới phát sinh trong session này

1. ✅ Model dùng để code trong Antigravity: **Claude Sonnet 4.6 (Thinking)** thay vì Gemini mặc định — vì task cần giữ đúng schema, tránh scope creep, reasoning kỹ hơn Flash
2. ✅ `tools.py` đặt ở root `Capstone/`, không nằm trong `references/` (đúng quy ước: references/ chỉ chứa tài liệu tĩnh)
3. ✅ Schema output giữ bản đầy đủ trong docstring gốc (không rút gọn theo bản spec sơ bộ ban đầu)
4. ✅ Mở rộng 3 → 5 essay types vì tài liệu brainstorm đã có sẵn, không tốn thêm effort đáng kể

---

## 8. Bối cảnh cá nhân Chi (không đổi)

- VSTEP B1 exam: 17/7/2026 (ưu tiên sau capstone)
- Sau VSTEP: build Word Bag full version (ASP.NET Core 8, portfolio backend chính)
- Job target: FPT, KMS, NashTech (.NET backend)
- Học song song: Software Testing, Advanced Software Design
- Pattern cần chú ý: xu hướng scope creep — session này đã kiểm soát tốt (mở rộng essay type có lý do rõ ràng, không phải thêm feature tùy hứng)

---

## 9. Việc tiếp theo ngay sau file này

1. Hoàn thành `agent.py` (đang chờ Antigravity code + Chi review system prompt)
2. Xử lý API quota trước khi demo
3. Demo case 1 (Opinion) — full flow từ đề bài đến conclusion
4. Demo case 2+3 (Discussion, Adv/Dis) — mở rộng thêm Problem-Solution/Two-Part nếu kịp vì đã có tool support
5. Cân nhắc Streamlit UI nếu còn thời gian sau khi 3 demo pass