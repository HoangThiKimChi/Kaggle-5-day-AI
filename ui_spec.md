# UI Spec — Essay Writing Coach (Streamlit)

> Bước 1 (Spec) cho nhánh UI. Viết trước khi code, theo đúng nguyên tắc
> spec-driven: Full Technical Design + Scenario trước khi đụng code.

---

## 1. Layout tổng quan (3 vùng)

```
┌──────────────┬─────────────────────────┬──────────────────────────┐
│              │                         │  [Tab: Hướng dẫn] [Tab:  │
│   SIDEBAR    │      CHAT (center)      │        Bài viết]         │
│  (progress)  │                         │                          │
│              │  ┌───────────────────┐  │  ┌────────────────────┐  │
│  Essay type: │  │ Agent: Đề bài của │  │  │ instructions (VI)  │  │
│  [Opinion]   │  │ bạn là dạng Opinion│  │  │ • Bước 1: ...      │  │
│              │  │ Essay...          │  │  │ • Bước 2: ...      │  │
│  Level:      │  └───────────────────┘  │  │                    │  │
│  ( ) A2      │                         │  │ template:          │  │
│  (•) B1      │  ┌───────────────────┐  │  │ "It is often..."   │  │
│              │  │ User: tôi muốn    │  │  │                    │  │
│  Tiến độ:    │  │ viết introduction │  │  │ example:            │  │
│  ✅ Intro    │  └───────────────────┘  │  │ "..."               │  │
│  🔲 Body 1   │                         │  │                    │  │
│  🔲 Body 2   │  [Nhập tin nhắn...]  ➤  │  │ useful_phrases: [..]│  │
│  🔲 Conclu.  │                         │  │ common_errors: [..] │  │
│              │                         │  │ checklist: [ ] [ ]  │  │
└──────────────┴─────────────────────────┴──────────────────────────┘
```

**3 vùng cố định:**
1. **Sidebar (trái, cố định, width nhỏ)** — essay type đã classify, chọn level A2/B1, checklist tiến độ 4 section (intro/body1/body2/conclusion) với icon ✅/🔲
2. **Chat (giữa, chiếm nhiều không gian nhất)** — hội thoại tự do với agent, giống ChatGPT
3. **Panel kết quả (phải, có tab)** — cập nhật động mỗi khi agent gọi tool, tách 2 tab:
   - **Tab "Hướng dẫn"** — hiển thị structured output mới nhất từ `guide_essay_section`/`suggest_sentence_structures`/`enrich_vocabulary`
   - **Tab "Bài viết"** — essay đang ghép dần (xem mục 3)

---

## 2. Hành vi từng vùng — Gherkin scenarios

```gherkin
Scenario: Agent classify xong, sidebar cập nhật essay type
  Given user vừa gửi đề bài lần đầu trong chat
  When agent gọi tool classify_essay_type thành công
  Then sidebar hiển thị essay_type detect được (ví dụ "Opinion")
  And sidebar hiển thị confidence bằng badge màu (high=xanh, medium=vàng, low=đỏ)

Scenario: Agent trả guidance, panel phải tự cập nhật
  Given agent vừa gọi tool guide_essay_section cho section "introduction"
  When kết quả trả về thành công
  Then tab "Hướng dẫn" ở panel phải hiển thị đầy đủ: instructions, template,
    example, useful_phrases, common_errors, checklist
  And sidebar đánh dấu section "introduction" chuyển từ 🔲 sang ⏳ (đang làm)

Scenario: User hoàn thành 1 section, chuyển sang section tiếp theo
  Given user đã nhận guidance cho "introduction"
  When user gõ nội dung essay của mình vào ô nhập trong tab "Bài viết"
    và nhấn "Xong phần này"
  Then sidebar đánh dấu "introduction" chuyển sang ✅
  And agent tự động hỏi user có muốn tiếp tục sang "body1" không
  And tab "Bài viết" hiển thị đoạn user vừa viết trong khung essay đang ghép

Scenario: Tool trả lỗi (API fail hoặc quota)
  Given user gửi yêu cầu nhưng Gemini API trả về error
  When agent nhận {"error": "..."}
  Then chat hiển thị thông báo lỗi bằng tiếng Việt, không phải raw JSON
  And panel phải KHÔNG bị xóa trắng — giữ nguyên kết quả lần cuối thành công
  And có nút "Thử lại" trong chat
```

---

## 3. Tab "Bài viết" — essay đang ghép dần

Mỗi section (intro/body1/body2/conclusion) là 1 **text area editable**, xếp
theo thứ tự. User tự gõ/dán nội dung của mình vào (không phải agent tự viết
hộ — agent chỉ hướng dẫn). Có nút "Xem toàn bộ" gộp 4 phần thành 1 đoạn văn
liền mạch để user copy ra ngoài.

```
┌─────────────────────────────────────┐
│  📝 Bài viết của bạn                 │
├─────────────────────────────────────┤
│  Introduction ✅                     │
│  ┌─────────────────────────────────┐ │
│  │ It is often argued that music...│ │
│  └─────────────────────────────────┘ │
│                                       │
│  Body 1 ⏳ (đang làm)                 │
│  ┌─────────────────────────────────┐ │
│  │ [chưa viết]                     │ │
│  └─────────────────────────────────┘ │
│                                       │
│  Body 2 🔲          Conclusion 🔲    │
│                                       │
│  [📋 Copy toàn bộ essay]             │
└─────────────────────────────────────┘
```

---

## 4. Data schema — `st.session_state`

Không cần SQLite cho v0 (single-user, single-session demo) — dùng
`st.session_state` của Streamlit là đủ, đơn giản hơn nhiều so với maintain
1 database file. SQLite chỉ cần nếu sau này muốn **lưu lại giữa các lần mở
app** (persist qua session) — không phải yêu cầu bắt buộc của capstone.

```python
# Cấu trúc session_state
{
    "messages": [                      # lịch sử chat, dùng cho ADK session
        {"role": "user", "content": "..."},
        {"role": "agent", "content": "..."},
    ],
    "essay_type": "opinion" | None,
    "essay_type_confidence": "high" | "medium" | "low" | None,
    "level": "A2" | "B1",
    "current_section": "introduction" | "body1" | "body2" | "conclusion" | None,
    "sections_status": {
        "introduction": "pending" | "in_progress" | "done",
        "body1": "pending" | "in_progress" | "done",
        "body2": "pending" | "in_progress" | "done",
        "conclusion": "pending" | "in_progress" | "done",
    },
    "essay_draft": {                   # nội dung user tự gõ, KHÔNG phải agent viết
        "introduction": "",
        "body1": "",
        "body2": "",
        "conclusion": "",
    },
    "last_tool_result": {              # kết quả tool gần nhất, hiển thị ở panel phải
        "tool_name": "guide_essay_section",
        "data": { ... }
    },
    "adk_session_id": "uuid-...",      # map với session ADK runner
}
```

**Nếu sau này muốn persist (ngoài scope v0)**: 1 bảng SQLite duy nhất
`sessions(session_id, essay_type, level, sections_status_json,
essay_draft_json, updated_at)` — đủ dùng, không cần chuẩn hóa nhiều bảng
vì đây không phải multi-user.

---

## 5. Ràng buộc thiết kế (giữ đúng scope đã chốt)

- Không có trang login/auth — mở app là vào thẳng giao diện chính
- Không có multi-essay history — mỗi lần refresh trang = phiên mới
- Agent **không tự viết hộ essay** — chỉ hướng dẫn, user tự gõ vào tab
  "Bài viết". Đây là nguyên tắc cốt lõi của sản phẩm (coach, không phải
  ghostwriter)
- Panel phải chỉ hiển thị kết quả tool **gần nhất** — không cần lưu lịch sử
  tất cả các lần gọi tool trước đó
