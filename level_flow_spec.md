# Bổ sung Spec — Flow theo Level (A2 vs B1)

> Bổ sung cho `ui_spec.md`. Viết lại từ mô tả của Chi, làm rõ trước khi
> giao Antigravity code.

---

## Nguyên tắc chung (áp dụng cả 2 level)

User luôn là người **tự phát triển ý kiến/lập luận** — agent không tự
nghĩ hộ nội dung. Vai trò agent là **hướng dẫn và hỗ trợ diễn đạt**, không
phải cung cấp sẵn ý tưởng. Đây vẫn giữ đúng nguyên tắc cốt lõi: coach,
không phải ghostwriter.

**Trường hợp user chưa có ý (bí ý tưởng)**: agent có thể tham khảo thông
tin liên quan chủ đề trong đề bài từ internet (search) để **gợi mở** —
KHÔNG phải để viết hộ, chỉ cung cấp context/facts để user tự hình thành
quan điểm riêng. *(Tính năng này là stretch goal — chỉ làm nếu dư thời
gian sau khi core flow hoàn thiện. Không chặn tiến độ chính.)*

---

## Flow — Level B1

```
1. User chọn level B1 ở sidebar
2. Agent chào, yêu cầu gửi đề bài
3. User gửi đề bài
4. Agent: classify_essay_type + paraphrase_prompt
   → Hiện 3 cách paraphrase + từ vựng liên quan ở tab "Hướng dẫn"
5. Agent HỎI user chọn cách nào (hoặc tự viết paraphrase riêng)
   → DỪNG LẠI CHỜ, không tự chuyển bước
6. User chọn/tự viết
7. Agent: guide_essay_section("introduction") — đưa template + ví dụ
   User tự viết cả câu, không cần agent chẻ nhỏ từng phần
8. Lặp lại cho body1 → body2 → conclusion
```

**Đặc điểm B1**: user tự diễn đạt được câu hoàn chỉnh, agent chỉ cần đưa
khung/template, không cần hỗ trợ ở mức từng từ.

---

## Flow — Level A2

```
1. User chọn level A2 ở sidebar
2. Agent chào, yêu cầu gửi đề bài
3. User gửi đề bài
4. Agent phân tích đề (classify_essay_type), đưa ra hướng dẫn TỔNG QUAN
   về từng phần cần viết (không cần bước chọn paraphrase riêng như B1 —
   đi thẳng vào hỗ trợ viết)
5. Agent hỏi user: "Bạn nghĩ gì về [chủ đề]?" — để user tự phát triển ý
   - Nếu user có ý → agent giúp hoàn thiện thành câu đúng ngữ pháp
   - Nếu user CHƯA có ý (trả lời kiểu "không biết", "chưa nghĩ ra") →
     agent tham khảo internet, cung cấp 2-3 facts/góc nhìn liên quan chủ
     đề đề bài, HỎI LẠI user chọn hướng nào để phát triển tiếp
6. User trả lời bằng câu ngắn, có thể sai ngữ pháp
7. Agent HOÀN THIỆN TỪNG CÂU cùng user:
   - Sửa ngữ pháp (thì, chia động từ, mạo từ...)
   - Gợi ý từ vựng đúng hơn nếu từ user dùng quá đơn giản/sai
   - Giải thích ngắn bằng tiếng Việt TẠI SAO sửa như vậy (để user học
     được, không chỉ nhận câu đúng thụ động)
8. Lặp lại từng câu cho đến khi xong 1 đoạn, rồi chuyển section tiếp theo
```

**Đặc điểm A2**: câu user viết thường ngắn, ngữ pháp yếu — agent cần
**scaffold chặt hơn nhiều** so với B1, sửa từng câu một thay vì đưa
template rồi để user tự viết cả đoạn.

---

## Điểm khác biệt cốt lõi giữa 2 flow

| | B1 | A2 |
|---|---|---|
| Bước paraphrase riêng | Có, user chọn 1/3 cách | Không — gộp vào bước hướng dẫn tổng quan |
| Đơn vị hỗ trợ | Cả đoạn/template | Từng câu một |
| Sửa lỗi | Không cần (user đã viết đúng) | Sửa ngữ pháp + từ vựng liên tục |
| Khi bí ý tưởng | Tự user brainstorm | Agent gợi ý qua search internet *(stretch)* |
| Giải thích lỗi sai | Không cần | Cần — giải thích tại sao sửa, để user học |

---

## Việc cần làm (ưu tiên theo thứ tự)

1. **Core, làm ngay**: Cập nhật `SYSTEM_PROMPT` trong `agent.py` — thêm
   nhánh rẽ theo `level` ngay sau bước classify, đúng 2 flow trên (không
   cần tool mới, dùng lại `guide_essay_section` + `suggest_sentence_structures`
   + `enrich_vocabulary` đã có, chỉ đổi cách agent gọi và mức độ chẻ nhỏ)
2. **Stretch, làm sau nếu dư thời gian**: tool search internet cho trường
   hợp A2 bí ý tưởng — tool thứ 6, cần build + test riêng
