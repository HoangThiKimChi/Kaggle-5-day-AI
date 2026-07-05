# essay_sync_and_scoring_spec.md — Auto-ghi Bài viết & Chấm điểm

> **Bối cảnh**: UI hiện có 3 tab trong panel "Kết quả": Hướng dẫn / Bài viết / Chấm điểm.
> Tab Bài viết: textarea trống, user tự paste. Tab Chấm điểm: đã tồn tại, có empty state
> ("Hãy viết bài essay trong tab Bài viết trước").
> **Mục tiêu**: (1) câu đã "đạt" trong vòng coach tự động ghi vào tab Bài viết;
> (2) tab Chấm điểm chấm toàn bài theo tiêu chí IELTS.
> **Ràng buộc deadline**: 06/07. Ưu tiên giải pháp ít chạm code nhất. Mọi thay đổi
> vượt phạm vi ghi trong spec → DỪNG, báo lại, không tự quyết.

---

## Phần A — Auto-ghi vào tab Bài viết

### A1. Điều kiện một câu được ghi (định nghĩa "đạt")

Một câu của user được coi là HOÀN THÀNH và tự động ghi vào tab Bài viết khi thỏa CẢ HAI:
1. Vòng chấm-sửa S2 kết thúc ở nhánh A (không còn lỗi nào)
2. User KHÔNG chọn cải thiện thêm — tức là chọn "viết câu tiếp theo" / "viết section kế",
   hoặc trả lời "không" khi được hỏi "có muốn cải thiện không"

Nếu user chọn "cải thiện" → câu CHƯA ghi; chỉ ghi phiên bản cuối cùng sau khi
vòng cải thiện kết thúc và user chuyển tiếp.

### A2. Cơ chế kỹ thuật — structured marker (chọn phương án ít rủi ro nhất)

Agent KHÔNG tự ghi vào đâu cả. Thay vào đó, khi một câu đạt điều kiện A1,
agent chèn vào CUỐI response một block marker máy-đọc-được:

```
<!--ESSAY_APPEND {"section": "introduction", "sentence": "<nguyên văn câu cuối cùng của user>"} -->
```

- `section` ∈ {"introduction", "body1", "body2", "conclusion"}
- `sentence` = nguyên văn câu ĐÃ ĐẠT của user (bản user gõ, không phải bản agent gợi ý)
- Marker là HTML comment → nếu frontend chưa parse, user không nhìn thấy gì lạ
  (degrade gracefully — giống nguyên tắc fallback text của bong bóng S3)

Frontend (App.tsx): parse marker trong response → append câu vào state bài viết
đúng section → render vào textarea tab Bài viết.

### A3. Quy tắc hiển thị trong tab Bài viết

- Trên cùng textarea: bộ đếm từ (word count) cập nhật realtime — đếm theo chuẩn
  IELTS (tách theo khoảng trắng). Hiển thị: `Số từ: N` (cảnh báo nhẹ màu cam nếu N < 250)
- 4 section cách nhau bằng MỘT dòng trống: Introduction ↵↵ Body 1 ↵↵ Body 2 ↵↵ Conclusion
- Không in nhãn section trong nội dung essay (bài IELTS thật không có heading) —
  nhãn chỉ dùng nội bộ để nhóm câu
- User VẪN sửa tay được trong textarea (auto-ghi không khóa quyền edit) —
  bản trong textarea là source of truth khi chấm điểm

### A4. Phạm vi code được chạm (Phần A)

- `agent.py` system prompt: thêm luật chèn ESSAY_APPEND marker khi điều kiện A1 thỏa
- `App.tsx`: parse marker + append state + word count + section spacing
- KHÔNG chạm: tools.py, server.py endpoints hiện có, schema API

---

## Phần B — Tab Chấm điểm

### B1. Kích hoạt

- User bấm nút ||Chấm điểm|| (trong tab Chấm điểm hoặc cuối tab Bài viết)
- Điều kiện: textarea Bài viết không rỗng. Nếu rỗng → giữ empty state hiện tại
- Input chấm = TOÀN BỘ nội dung textarea tab Bài viết (kể cả phần user sửa tay)

### B2. Format kết quả chấm (thứ tự bắt buộc)

```
📊 Band ước lượng: ~X.X
(dựa trên 4 tiêu chí IELTS Writing Task 2)

| Tiêu chí | Band | Nhận xét ngắn |
|---|---|---|
| Task Response (ý triển khai) | ~X.X | ... |
| Coherence & Cohesion | ~X.X | ... |
| Lexical Resource (từ vựng) | ~X.X | ... |
| Grammatical Range & Accuracy (ngữ pháp) | ~X.X | ... |

✅ Điểm mạnh:
- (2-3 gạch đầu dòng, trích cụ thể từ bài — ví dụ cụm từ tốt user đã dùng)

🔧 Điểm cần cải thiện:
- (2-3 gạch đầu dòng, mỗi ý kèm ví dụ CỤ THỂ từ bài + hướng sửa —
  không viết lại nguyên câu hộ user)
```

### B3. Grounding & ràng buộc

- Chấm dựa trên Writing-Band-descriptors-Task-2.pdf + sentence_structures.md
  (evaluator scoring đã tích hợp sẵn — TÁI DÙNG endpoint/logic chấm hiện có,
  không viết evaluator mới)
- Luôn kèm "ước lượng" và `~` — không khẳng định điểm IELTS chính thức
- Nhận xét bằng tiếng Việt đơn giản (A2-B1 đọc hiểu được)
- Nếu bài < 250 từ: vẫn chấm, nhưng thêm 1 dòng lưu ý phạt độ dài trong thi thật
- 1 lần bấm = 1 request chấm; disable nút trong lúc chờ kết quả (chống double-click
  đốt quota)

### B4. Phạm vi code được chạm (Phần B)

- Nếu backend đã có endpoint chấm điểm: CHỈ chỉnh format output theo B2
- Frontend: nút Chấm điểm + render kết quả trong tab (thay empty state)
- KHÔNG thêm tool mới vào tools.py

---

## Phân mức ưu tiên trước deadline 06/07

| Hạng mục | Mức rủi ro | Quyết định |
|---|---|---|
| B — Chấm điểm (format + nút) | Thấp (tab + evaluator đã có) | ✅ Làm — cần cho video demo |
| A3 — Word count + section spacing | Thấp (frontend thuần, cục bộ) | ✅ Làm |
| A2 — ESSAY_APPEND marker + parse | Trung bình (prompt + App.tsx, có fallback) | ⚠️ Làm nếu B xong sớm; marker vô hại nếu frontend chưa parse kịp |
| Bất kỳ thứ gì cần sửa server.py schema | Cao | 🛑 Hoãn sau deadline |

## Gherkin scenarios

```gherkin
Scenario: Câu đạt và user chuyển tiếp
  Given user vừa nhận nhánh A (không lỗi) cho câu introduction
  When user chọn "viết câu tiếp theo"
  Then response của agent chứa marker ESSAY_APPEND với section "introduction"
  And tab Bài viết hiển thị thêm câu đó
  And word count tăng tương ứng

Scenario: Câu đạt nhưng user muốn cải thiện
  Given user vừa nhận nhánh A cho một câu
  When user chọn "cải thiện câu này"
  Then response KHÔNG chứa marker ESSAY_APPEND
  And tab Bài viết không thay đổi

Scenario: Chấm điểm khi textarea rỗng
  Given tab Bài viết không có nội dung
  When user mở tab Chấm điểm
  Then hiển thị empty state hiện tại, không gọi API

Scenario: Chấm điểm bài hoàn chỉnh
  Given tab Bài viết có đủ 4 section
  When user bấm nút Chấm điểm
  Then hiển thị band ước lượng ~X.X + bảng 4 tiêu chí
  And có mục Điểm mạnh và Điểm cần cải thiện với ví dụ trích từ bài
```
