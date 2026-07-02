# Essay Writing Coach — Đặc tả tổng thể (Full Technical Design)

> Mục đích file này: nhìn lại toàn bộ hệ thống một lượt theo chuẩn spec đầy
> đủ, để lộ ra chỗ nào còn thiếu trước khi tiếp tục code UI. Không phải spec
> viết lại từ đầu — là bản audit dựa trên những gì đã build.

---

## 1. Why — vấn đề đang giải quyết

Người Việt ôn IELTS Writing Task 2 (target 5.0-6.0, level A2-B1) có ý trong
đầu nhưng không biết diễn đạt: không biết paraphrase đề, cấu trúc câu đơn
điệu, từ vựng nghèo, không biết bắt đầu từng phần essay.

**Khác biệt cốt lõi so với công cụ khác** — đây là nguyên tắc chi phối mọi
quyết định thiết kế phía sau:
- Grammarly: chỉ sửa lỗi câu đã viết, không dạy cách viết từ đầu
- ChatGPT: trả lời 1 cú, không dẫn dắt từng bước
- **Essay Writing Coach: coach, không phải ghostwriter** — hướng dẫn từng
  bước bằng tiếng Việt, KHÔNG viết hộ essay. Đây là lý do UI bắt buộc phải
  có ô để user tự gõ (không phải agent tự điền).

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                      app.py (Streamlit)                  │
│   - Nhận input user qua chat box                          │
│   - Quản lý st.session_state (essay_type, level,          │
│     sections_status, essay_draft...)                      │
│   - Hiển thị sidebar + chat + panel kết quả                │
└───────────────────────┬───────────────────────────────────┘
                         │ gọi run_turn(message) — ASYNC
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      agent.py (Google ADK)                │
│   - root_agent: LlmAgent, model=gemini-2.5-flash           │
│   - SYSTEM_PROMPT điều hướng flow                          │
│   - InMemoryRunner + ensure_session (async)                │
└───────────────────────┬───────────────────────────────────┘
                         │ agent tự quyết định gọi tool nào
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      tools.py (5 functions)                │
│   classify_essay_type │ paraphrase_prompt │                │
│   guide_essay_section │ suggest_sentence_structures │       │
│   enrich_vocabulary                                        │
│        │                                                    │
│        ├──► _call_gemini() ──► Gemini API (service ngoài)   │
│        └──► _load_ref() ──► references/*.md (cache 1 lần)   │
└─────────────────────────────────────────────────────────┘
```

**Luồng dữ liệu 1 turn**: User gõ trong Streamlit → `app.py` gọi
`run_turn()` (async, cần `asyncio.run()` hoặc event loop wrapper vì
Streamlit chạy sync) → `agent.py` route qua ADK → ADK tự chọn gọi 1+ tool
trong `tools.py` → tool gọi Gemini API + đọc `references/` → trả JSON có
cấu trúc → agent tổng hợp thành câu trả lời tiếng Việt → `app.py` nhận text
+ cập nhật `session_state` (essay_type, sections_status...) → re-render UI.

**⚠️ Điểm chưa rõ — cần làm rõ trước khi code `app.py`**: `run_turn()` hiện
là `async def`. Streamlit chạy đồng bộ (sync) theo mặc định. Cần quyết định:
dùng `asyncio.run(run_turn(...))` mỗi lần gọi (đơn giản nhưng tạo event loop
mới mỗi lần, có thể chậm), hay dùng `st.session_state` giữ 1 event loop
sống xuyên suốt session. **Đây là rủi ro kỹ thuật chưa test qua** — nên
prototype thử trước khi viết full `app.py`.

---

## 3. Use case chính

| # | Use case | Actor | Trigger |
|---|---|---|---|
| UC1 | Nộp đề bài, nhận phân loại | User | Gõ đề bài lần đầu |
| UC2 | Xin paraphrase đề bài | User | Sau khi có essay_type |
| UC3 | Xin hướng dẫn từng section | User | "tôi muốn viết introduction" |
| UC4 | Xin gợi ý cấu trúc câu cho 1 ý | User | Dán câu đơn giản, hỏi cách viết hay hơn |
| UC5 | Xin làm giàu từ vựng cho đoạn đã viết | User | Dán đoạn văn, hỏi từ đồng nghĩa |
| UC6 | Xem lại essay đang ghép dần | User | Chuyển sang tab "Bài viết" |
| UC7 (edge) | Gemini API lỗi/hết quota | Hệ thống | Tool trả `{"error": ...}` |
| UC8 (edge) | User hỏi việc ngoài phạm vi (ví dụ "dịch bài này sang tiếng Pháp") | User | Agent phải từ chối lịch sự, nhắc lại phạm vi hỗ trợ |

**UC8 chưa có trong bất kỳ spec nào từ trước đến giờ** — cần bổ sung vào
`SYSTEM_PROMPT` của `agent.py`: rõ ràng giới hạn phạm vi, tránh agent cố
trả lời việc ngoài 5 tool đã định nghĩa.

---

## 4. State design (đã có trong `ui_spec.md`, nhắc lại tóm tắt)

`st.session_state` là nguồn dữ liệu duy nhất, không dùng SQLite cho v0.
Chi tiết đầy đủ xem `ui_spec.md` mục 4.

**Câu hỏi chưa trả lời**: `agent.py` (ADK `InMemoryRunner`) có **session
riêng của nó** (`adk_session_id`) — khác với `st.session_state` của
Streamlit. Cần đồng bộ 2 cái này: mỗi lần Streamlit rerun (xảy ra liên tục
do cách Streamlit hoạt động), có tạo lại ADK session mới không, hay giữ
nguyên 1 ADK session xuyên suốt? **Nếu tạo lại mỗi lần rerun → agent mất
trí nhớ hội thoại giữa các turn — lỗi nghiêm trọng.** Cần test kỹ điểm này
khi code `app.py`.

---

## 5. API contract — UI ↔ Agent

Chưa được định nghĩa chính thức. Cần chốt trước khi code:

```python
# Input mong đợi
run_turn(
    runner: InMemoryRunner,
    session_id: str,
    user_id: str,
    message: str
) -> str  # trả về text thuần, không phải dict

# UI cần biết THÊM: tool nào vừa được gọi, để cập nhật đúng panel/sidebar
# → HIỆN TẠI run_turn() KHÔNG trả thông tin này, chỉ trả text.
```

**Gap cần xử lý**: `run_turn()` hiện tại chỉ trả về chuỗi text tổng hợp,
nhưng UI cần biết **tool nào vừa chạy** (để cập nhật sidebar/panel đúng chỗ)
và **dữ liệu structured** (để hiển thị template/example riêng biệt, không
phải nhét hết vào 1 khối text). Cần sửa `run_turn()` (hoặc viết hàm mới)
để trả về:

```python
{
    "text": "...",                    # câu trả lời tổng hợp cho chat
    "tool_calls": [                   # tool nào vừa chạy, để UI biết cập nhật gì
        {"tool": "guide_essay_section", "result": {...}}
    ]
}
```

Đây là **thay đổi cần làm trong `agent.py` trước khi code `app.py`** —
không phát hiện ra nếu chỉ nhìn UI spec riêng lẻ.

---

## 6. Tool/library versions (Visual Aid)

Cần Antigravity xác nhận version cụ thể đang cài (chưa có sẵn):

| Library | Version dùng | Ghi chú |
|---|---|---|
| `google-genai` | ? (đã cài, chưa ghi version) | Cần `pip show google-genai` để biết |
| `google-adk` | ? (đã cài, chưa ghi version) | API đã đổi giữa version (session auto-create) — version rất quan trọng |
| `streamlit` | Chưa cài | Cần chọn version, khuyến nghị bản mới nhất ổn định |
| `python-dotenv` | Đề xuất thêm (chưa xác nhận đã làm) | Để load `.env` thay vì phụ thuộc `~/.zshrc` |

**Việc cần làm**: yêu cầu Antigravity chạy `pip freeze | grep -E "google|streamlit|dotenv"` để có bảng version chính xác, ghi vào `requirements.txt`.

---

## 7. Scenario — good / wrong / edge (bổ sung so với `ui_spec.md`)

```gherkin
Scenario: [GOOD] Full flow từ đề bài đến introduction hoàn chỉnh
  Given user mở app lần đầu
  When user dán đề bài Opinion vào chat
  And agent trả lời classify + paraphrase
  And user chọn 1 trong 3 paraphrase và xin hướng dẫn introduction
  Then panel phải hiển thị đầy đủ guidance
  And sidebar cập nhật essay_type + progress
  And session vẫn nhớ context khi user gửi tin nhắn tiếp theo

Scenario: [WRONG] Agent bị hỏi việc ngoài phạm vi
  Given user đang trong luồng viết essay
  When user hỏi "dịch bài này sang tiếng Pháp giúp tôi"
  Then agent từ chối lịch sự bằng tiếng Việt
  And agent nhắc lại phạm vi hỗ trợ (chỉ IELTS Writing Task 2 tiếng Anh)
  And KHÔNG tự ý gọi Gemini để dịch (tránh lệch scope, tốn quota)

Scenario: [EDGE] Streamlit rerun làm mất session ADK
  Given user đang giữa luồng hội thoại (đã qua introduction)
  When Streamlit tự rerun (do user tương tác với widget khác, ví dụ đổi level)
  Then ADK session_id phải được giữ nguyên (lưu trong st.session_state)
  And agent KHÔNG được "quên" những gì đã trao đổi trước đó

Scenario: [EDGE] User bỏ trống ô nhập rồi bấm gửi
  Given ô chat input đang trống
  When user bấm nút gửi (hoặc Enter)
  Then UI không gọi run_turn() với message rỗng
  And không có gì xảy ra (không lỗi, không tin nhắn rỗng xuất hiện trong chat)
```

---

## 8. Tổng hợp — những điểm cần xử lý trước khi code `app.py`

Sắp theo mức độ ưu tiên:

1. **[Chặn cứng]** `run_turn()` cần trả thêm `tool_calls` structured data,
   không chỉ text — nếu không UI không thể tách hiển thị panel/sidebar
2. **[Chặn cứng]** Xác định cách giữ ADK session sống xuyên suốt Streamlit
   session (tránh mất trí nhớ hội thoại mỗi lần rerun)
3. **[Chặn cứng]** Giải quyết async/sync mismatch giữa `run_turn()` (async)
   và Streamlit (sync) — cần prototype nhỏ test trước
4. **[Nên có]** Thêm scope guard vào `SYSTEM_PROMPT` cho UC8 (từ chối việc
   ngoài phạm vi)
5. **[Nên có]** Ghi `requirements.txt` với version cụ thể
6. **[Đã đủ]** Data schema, wireframe, use case chính — không cần sửa thêm

**Khuyến nghị**: giải quyết 3 điểm "chặn cứng" bằng 1 prototype nhỏ
(script test riêng, không phải `app.py` đầy đủ) trước — xác nhận
async+session hoạt động đúng, rồi mới viết `app.py` hoàn chỉnh. Tránh
trường hợp code hết 200 dòng `app.py` rồi mới phát hiện session bị mất.
