# SPEC: Tính năng Chấm điểm IELTS Writing Task 2 (Essay Evaluator)

Trạng thái: Đã chốt thiết kế, sẵn sàng implement.
Phạm vi điểm số: **chỉ dùng Overall Band 1.0 – 6.5 (bước 0.5). Không có Display Score / thang 10.**

---

## 1. Tool mới trong `tools.py`

### 1.1. Signature

```python
def evaluate_essay(essay_text: str, essay_type: str) -> dict:
```

- `essay_text` (str, required): toàn bộ bài luận đã gộp từ 4 phần nháp trong UI.
- `essay_type` (str, required): một trong các giá trị enum sau (phải khớp với lựa chọn ở UI, xem mục 2.3):
  `"opinion"`, `"discussion"`, `"problem_solution"`, `"advantages_disadvantages"`, `"two_part_question"`

### 1.2. Rubric source

- Đọc file `ielts_scoring_rubric.json` (đã có sẵn) làm reference cho prompt. Không hardcode lại mô tả band trong code — load từ file mỗi lần gọi, hoặc cache ở module-level nếu muốn tránh đọc file lặp lại (an toàn để cache vì file rubric không đổi trong runtime).

### 1.3. Gemini API call — cấu hình bắt buộc

- Dùng **structured output** (`response_mime_type: "application/json"` + `response_schema`), KHÔNG chỉ prompt "trả JSON" bằng lời — để tránh model trả sai format hoặc band ngoài lưới 0.5.

**response_schema (Gemini structured output schema):**

```python
EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "task_response": {
            "type": "object",
            "properties": {
                "band": {"type": "number", "enum": [1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5]},
                "feedback": {"type": "string"},
                "suggestions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["band", "feedback", "suggestions"]
        },
        "coherence_cohesion": { "...same shape as task_response..." },
        "lexical_resource": { "...same shape as task_response..." },
        "grammatical_range": { "...same shape as task_response..." }
    },
    "required": ["task_response", "coherence_cohesion", "lexical_resource", "grammatical_range"]
}
```

(4 tiêu chí lặp lại đúng shape: `band`, `feedback` bằng tiếng Việt, `suggestions` là list 1-3 gợi ý hành động cụ thể để nâng band, bằng tiếng Việt.)

- Model: dùng model chính hiện tại của project (flash), có fallback sang flash-lite khi gặp lỗi quota/503 — xem mục 1.5.

### 1.4. Prompt template (gộp system + rubric + essay)

Prompt cần chứa:
1. Vai trò: giám khảo chấm IELTS Writing Task 2, quen với band 1.0–6.5 (không chấm band 7-9).
2. Toàn bộ nội dung rubric tương ứng (có thể nhúng cả object JSON rubric vào prompt, hoặc rút gọn phần liên quan — nhúng cả object là an toàn hơn vì bảo đảm model bám sát mô tả band thấp/cao đã định nghĩa).
3. `essay_type` để model hiểu dạng đề khi đánh giá Task Response.
4. `essay_text` cần chấm.
5. Yêu cầu rõ: chỉ chọn band trong lưới 0.5 từ 1.0 đến 6.5; feedback và suggestions viết bằng tiếng Việt, ngắn gọn, cụ thể, không dùng thuật ngữ trừu tượng.

### 1.5. Xử lý lỗi & retry

- Bọc API call trong `try/except`.
- Nếu lỗi 503 (transient, thường gặp ở flash-lite) → retry tối đa 3 lần với exponential backoff (vd: 2s, 4s, 8s).
- Nếu vượt quota (lỗi rate limit trên flash) → fallback tự động sang flash-lite; nếu flash-lite cũng lỗi → trả về dict lỗi rõ ràng để UI hiển thị thông báo thân thiện (KHÔNG để Streamlit crash):
  ```python
  {"error": True, "message": "Hệ thống đang quá tải, vui lòng thử lại sau ít phút."}
  ```

### 1.6. Post-processing bắt buộc (Python, sau khi nhận JSON từ Gemini)

**a) Validate/clamp band:** dù đã ép response_schema, vẫn nên validate lại — nếu band nào ngoài lưới 0.5 hoặc ngoài [1.0, 6.5], clamp về giá trị hợp lệ gần nhất, không crash.

**b) Tính Overall Band — dùng round-half-up, KHÔNG dùng `round()` mặc định của Python** (Python round() là banker's rounding, sai với chuẩn IELTS):

```python
import math

def ielts_round(avg: float) -> float:
    """Round-half-up to nearest 0.5, theo chuẩn IELTS."""
    return math.floor(avg * 2 + 0.5) / 2

overall_band = ielts_round(
    (task_response_band + coherence_cohesion_band + lexical_resource_band + grammatical_range_band) / 4
)
```

### 1.7. Return schema đầy đủ của `evaluate_essay`

```python
{
    "overall_band": 5.5,
    "criteria": {
        "task_response": {"band": 5.5, "feedback": "...", "suggestions": ["...", "..."]},
        "coherence_cohesion": {"band": 5.0, "feedback": "...", "suggestions": ["...", "..."]},
        "lexical_resource": {"band": 6.0, "feedback": "...", "suggestions": ["...", "..."]},
        "grammatical_range": {"band": 5.5, "feedback": "...", "suggestions": ["...", "..."]}
    },
    "essay_type": "opinion",
    "word_count": 267,
    "error": False
}
```

Khi lỗi: `{"error": True, "message": "..."}` — không có các field khác.

### 1.8. Cache theo nội dung bài viết

- Cache key: `hash(essay_text + essay_type)` (dùng `hashlib.sha256`).
- Lưu cache trong session state của Streamlit (không cần persistent storage), map `cache_key -> kết quả evaluate_essay`.
- Khi user bấm "Chấm điểm bài viết" hoặc "Chấm điểm lại": tính cache_key trước, nếu đã có trong cache → trả kết quả cũ ngay, KHÔNG gọi API. Chỉ gọi API khi cache_key mới (tức bài đã thay đổi nội dung).

---

## 2. UI trong `app.py`

### 2.1. Cấu trúc tab (cột phải)

Đổi từ 2 tab thành 3 tab: `💡 Hướng dẫn`, `📝 Bài viết`, `📊 Chấm điểm`.

### 2.2. Điều kiện bấm nút chấm điểm

- Nút "📊 Chấm điểm bài viết" chỉ **active** khi tổng số từ của bài viết (gộp từ 4 phần nháp) **≥ 50 từ**. Dưới 50 từ: nút disable + hiển thị dòng chú thích nhỏ "Cần tối thiểu 50 từ để chấm điểm (hiện tại: X từ)".

### 2.3. Chọn dạng đề (essay_type) — bổ sung bắt buộc

- Tab "📝 Bài viết" cần có 1 selectbox để user chọn dạng đề Task 2 trước khi viết, map đúng 5 giá trị enum ở mục 1.1:
  - "Quan điểm cá nhân (Opinion)" → `opinion`
  - "Thảo luận hai quan điểm (Discussion)" → `discussion`
  - "Vấn đề - Giải pháp (Problem - Solution)" → `problem_solution`
  - "Lợi ích - Bất lợi (Advantages - Disadvantages)" → `advantages_disadvantages`
  - "Câu hỏi hai phần (Two-part question)" → `two_part_question`
- Giá trị này được truyền vào `evaluate_essay(essay_text, essay_type)`.

### 2.4. Trạng thái chưa chấm điểm (Tab 📊)

- Text: "Hãy gõ hoặc hoàn thành bài viết của bạn bên tab 'Bài viết' rồi nhấn nút dưới đây để nhận đánh giá chi tiết."
- Nút "📊 Chấm điểm bài viết" (theo điều kiện mục 2.2).
- Khi click: gộp bài, tính cache_key, nếu cache miss → gọi `evaluate_essay` kèm `st.spinner("Hệ thống đang chấm điểm bài viết của bạn...")`.
- Nếu kết quả trả `error: True` → hiển thị `st.error(message)`, không phá layout.

### 2.5. Trạng thái đã có kết quả (Dashboard)

- **Overall Band Score**: badge nổi bật, format `"{overall_band} / 6.5"` (ví dụ `5.5 / 6.5`).
- **Progress bar band tổng**: `st.progress(overall_band / 6.5)` — thang trực quan bám đúng phạm vi 1.0–6.5, KHÔNG quy đổi sang thang 10.
- **4 tiêu chí thành phần**: biểu đồ cột hoặc list hiển thị band riêng từng tiêu chí (Task Response / Coherence & Cohesion / Lexical Resource / Grammatical Range), mỗi cái cũng có thể có progress bar riêng (band_tieu_chi / 6.5).
- **Feedback chi tiết**: mỗi tiêu chí 1 `st.expander` chứa `feedback` + danh sách `suggestions` (bullet points), bằng tiếng Việt.
- **Nút "🔄 Chấm điểm lại"**: tính lại cache_key từ nội dung bài hiện tại — nếu bài đã sửa (cache miss) → gọi API mới; nếu bài không đổi (cache hit) → trả kết quả cũ, có thể hiện toast nhỏ "Bài viết chưa thay đổi, hiển thị kết quả gần nhất."

---

## 3. Ghi chú test (do đang bị giới hạn quota Gemini)

- Khi test E2E giao diện/luồng, dùng **mock function** trả về 1 JSON kết quả giả cố định (đúng schema mục 1.7) thay cho gọi `evaluate_essay` thật, để không tốn quota.
- Chỉ gọi API thật ở vòng test cuối cùng để xác nhận tích hợp hoạt động đúng với Gemini thật (bao gồm test cả nhánh lỗi 503/quota để chắc retry + fallback hoạt động).

---

## 4. Checklist bàn giao cho Antigravity

- [ ] Thêm `evaluate_essay()` vào `tools.py` theo mục 1 (signature, schema, prompt, rounding, cache, retry).
- [ ] Thêm `ielts_round()` helper — KHÔNG dùng `round()` mặc định.
- [ ] Thêm selectbox chọn `essay_type` ở tab "📝 Bài viết".
- [ ] Thêm tab "📊 Chấm điểm" với 2 trạng thái (chưa chấm / đã chấm) theo mục 2.
- [ ] Ngưỡng từ tối thiểu: 50 từ.
- [ ] Cache theo hash nội dung bài viết trong session state.
- [ ] Xử lý lỗi API không làm crash UI (`st.error` thân thiện).
- [ ] Không có bất kỳ chỗ nào tính hoặc hiển thị "Display Score / thang 10" — chỉ Overall Band 1.0–6.5.
