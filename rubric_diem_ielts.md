# Thang đo chấm điểm IELTS Writing Task 2 (Beginner → cận B2)

> Xây dựng dựa trên bảng band descriptors chính thức IELTS Writing Task 2, rút gọn và chuyển thành các mô tả **quan sát được** (actionable) để agent chấm bài dễ áp dụng, thay vì ngôn ngữ trừu tượng của bản gốc.

## 1. Bảng ánh xạ tổng quan

| Cấp độ | CEFR | IELTS Band | Display Score (1–10) |
|---|---|---|---|
| Sơ cấp (Beginner) | Dưới A2 | 1.0 – 3.5 | 1.0 – 4.5 |
| Tiền trung cấp (Elementary) | A2 | 4.0 – 4.5 | 5.0 – 6.5 |
| Trung cấp (Intermediate) | B1 | 5.0 – 5.5 | 7.0 – 8.5 |
| Cận trung-cao (Upper-Int approaching) | B1+ / cận B2 | 6.0 – 6.5 | 9.0 – 10.0 |

**Công thức quy đổi Display Score:**
```
display_score = round((band_score - 1.0) / 5.5 * 9 + 1, 1)
```
- Band 1.0 → 1.0 điểm | Band 6.5 → 10.0 điểm (thang tuyến tính)
- Dùng để hiển thị UI đơn giản cho user, band gốc vẫn giữ lại để đối chiếu chuẩn IELTS thật.

**Quy tắc chọn band lẻ (0.5) trong mỗi cấp độ:**
Mỗi cấp độ có 2 mốc (band thấp / band cao). Đếm số tiêu chí (trong 4 tiêu chí TR/CC/LR/GRA) đạt mô tả "mốc cao" — nếu ≥3/4 tiêu chí đạt mốc cao → chọn band cao của cấp độ; ngược lại chọn band thấp.

---

## 2. Chi tiết theo từng cấp độ

### 🔹 Cấp 1 — Sơ cấp (Beginner) | Band 1.0–3.5

| Tiêu chí | Mốc thấp (Band 1.0–2.0) | Mốc cao (Band 2.5–3.5) |
|---|---|---|
| **Task Response** | Lạc đề hoặc không trả lời được yêu cầu; không có luận điểm; bài quá ngắn (<80 từ) | Có cố gắng trả lời đề nhưng chỉ nêu 1-2 ý rời rạc, không phát triển; nhiều đoạn lạc hướng |
| **Coherence & Cohesion** | Không chia đoạn hoặc chỉ 1 đoạn duy nhất; câu rời rạc, gần như không có từ nối | Có chia đoạn nhưng không theo logic rõ; dùng rất ít từ nối cơ bản (and, but) |
| **Lexical Resource** | Từ vựng cực kỳ hạn chế, lặp từ liên tục; lỗi chính tả nhiều làm khó hiểu nghĩa | Từ vựng cơ bản (basic words), vẫn lặp nhiều; lỗi chính tả/word formation gây cản trở |
| **Grammatical Range** | Câu gần như không có cấu trúc hoàn chỉnh; lỗi chia động từ/mạo từ nghiêm trọng, sai lệch nghĩa | Chỉ dùng được câu đơn; lỗi ngữ pháp cơ bản dày đặc nhưng bắt đầu tạo được câu có nghĩa |

### 🔹 Cấp 2 — Tiền trung cấp (Elementary/A2) | Band 4.0–4.5

| Tiêu chí | Mốc thấp (Band 4.0) | Mốc cao (Band 4.5) |
|---|---|---|
| **Task Response** | Trả lời đề ở mức tối thiểu; 1 luận điểm chính, thiếu ví dụ/lập luận cụ thể; ~120-150 từ | Trả lời đủ các phần đề bài nhưng phát triển ý còn sơ sài; có 1-2 ví dụ đơn giản; ~150-200 từ |
| **Coherence & Cohesion** | Có chia đoạn (intro/body/conclusion) nhưng sắp xếp chưa hợp lý; linking words lặp lại máy móc | Chia đoạn rõ hơn, mỗi đoạn có 1 ý; dùng thêm linking words cơ bản (also, because, so) dù đôi khi sai chỗ |
| **Lexical Resource** | Từ vựng cơ bản, đôi khi dùng sai nghĩa/không hợp văn phong | Từ vựng cơ bản nhưng chọn từ chính xác hơn; bắt đầu có collocation đơn giản đúng (make a decision) |
| **Grammatical Range** | Câu đơn chủ đạo, thử câu ghép (and/but/because) nhưng lỗi nhiều | Câu ghép dùng ổn định hơn; bắt đầu thử câu phức đơn giản (relative clause cơ bản), lỗi vẫn phổ biến nhưng không luôn cản trở nghĩa |

### 🔹 Cấp 3 — Trung cấp (Intermediate/B1) | Band 5.0–5.5

| Tiêu chí | Mốc thấp (Band 5.0) | Mốc cao (Band 5.5) |
|---|---|---|
| **Task Response** | Đề cập đủ các phần yêu cầu; có quan điểm nhưng chưa nhất quán xuyên suốt; ý còn hạn chế, ít ví dụ cụ thể; ~200-220 từ | Quan điểm rõ ràng và giữ nhất quán; luận điểm có ví dụ hỗ trợ dù chưa phát triển sâu; đạt ~250 từ |
| **Coherence & Cohesion** | Có tổ chức tổng thể nhưng progression chưa rõ; referencing (this/that/it) đôi khi gây khó hiểu | Tổ chức mạch lạc hơn, mỗi đoạn 1 ý chính rõ ràng; dùng đa dạng hơn linking words (however, in addition, for example) dù đôi khi hơi máy móc |
| **Lexical Resource** | Từ vựng đủ dùng cho chủ đề nhưng còn hẹp; một số lỗi spelling/word formation không đáng kể | Bắt đầu thử từ vựng ít phổ biến hơn (less common words); collocation đúng nhiều hơn; lỗi chính tả hiếm |
| **Grammatical Range** | Kết hợp câu đơn và câu phức nhưng câu phức còn lỗi nhiều hơn câu đơn | Câu phức dùng tự nhiên hơn, tỷ lệ lỗi giảm rõ; một số lỗi ngữ pháp/dấu câu nhưng hiếm khi gây hiểu lầm |

### 🔹 Cấp 4 — Cận trung-cao (Upper-Int approaching / cận B2) | Band 6.0–6.5

| Tiêu chí | Mốc thấp (Band 6.0) | Mốc cao (Band 6.5) |
|---|---|---|
| **Task Response** | Đề cập đầy đủ, phát triển ý khá kỹ với ví dụ liên quan; đôi lúc lập luận hơi tổng quát nhưng vẫn bám đề | Luận điểm phát triển tốt, ví dụ cụ thể và liên quan chặt chẽ; giữ trọng tâm xuyên suốt bài |
| **Coherence & Cohesion** | Progression rõ ràng toàn bài; cohesive devices dùng hiệu quả dù đôi chỗ hơi cứng | Chuyển ý tự nhiên, referencing chính xác; cấu trúc đoạn văn chặt chẽ, gần như không gây khó hiểu |
| **Lexical Resource** | Từ vựng khá đa dạng, collocation chính xác phần lớn; dùng synonym để tránh lặp | Vốn từ linh hoạt hơn, một số từ ít phổ biến dùng đúng ngữ cảnh; lỗi chính tả/word formation hiếm gặp |
| **Grammatical Range** | Đa dạng cấu trúc phức (mệnh đề quan hệ, điều kiện, bị động); phần lớn câu không lỗi | Kiểm soát ngữ pháp và dấu câu tốt, chỉ còn lỗi nhỏ/lẻ tẻ; linh hoạt chuyển đổi giữa các loại câu |

---

## 3. Ghi chú khi dùng cho app

- Thang này **dừng ở band 6.5** vì phạm vi target user là zero → cận B2 (không cần mô tả band 7-9, vốn dành cho advanced/native-like).
- Với mỗi bài viết, agent nên chấm riêng 4 tiêu chí trước (mỗi tiêu chí ra 1 band lẻ 0.5), sau đó tính trung bình cộng 4 tiêu chí rồi làm tròn theo quy tắc IELTS chuẩn (làm tròn 0.25 lên) để ra band tổng.
- Display Score chỉ nên dùng cho hiển thị nhanh (progress bar, badge cấp độ); band số lẻ 0.5 vẫn là số liệu chính để feedback chi tiết.
