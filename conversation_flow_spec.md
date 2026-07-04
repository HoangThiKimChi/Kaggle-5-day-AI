# conversation_flow_spec.md — Luồng hội thoại Agent ↔ User

> **Mục đích**: Spec này định nghĩa CHÍNH XÁC nội dung và thứ tự message mà agent trả cho user, theo vòng lặp coach từng câu. Antigravity implement theo spec này — KHÔNG tự thêm bước, không gộp bước.
> **Phạm vi**: áp dụng cho flow chính (mặc định B1; ghi chú A2 ở cuối). Ngôn ngữ trả lời user: **tiếng Việt**, thuật ngữ IELTS giữ tiếng Anh.
> **Nguyên tắc bất biến**: coach, not ghostwriter — agent KHÔNG BAO GIỜ viết hộ nguyên câu/nguyên đoạn cho user. Agent chỉ gợi ý, đặt câu hỏi, sửa lỗi và giải thích.

---

## Sơ đồ trạng thái tổng

```
[S0 Chờ đề bài]
   → user gửi đề →
[S1 Phân tích đề + hướng dẫn paraphrase]
   → user gửi câu viết →
[S2 Vòng chấm-sửa câu]  ←──┐
   ├─ có lỗi → liệt kê lỗi, yêu cầu viết lại ──┘ (lặp đến khi đạt)
   └─ đạt → khen + band ước lượng + hỏi tiếp
[S3 Chuyển section] — bong bóng: ||Cải thiện|| ||Viết tiếp section kế||
   → sang section mới →
[S4 Brainstorm ý cho body]
   → user đưa ý → agent hỏi 3-5 câu đào sâu → user trả lời →
[S5 Hướng dẫn viết từng câu] → quay lại [S2] cho mỗi câu
   ...lặp đến hết Conclusion...
[S6 Hoàn thành bài] — hỏi cải thiện
   ├─ Không → in lại bài hoàn chỉnh → END
   └─ Có → gợi ý cải thiện (cấu trúc câu, từ vựng) theo references → quay lại S2 với câu được chọn
```

---

## S1 — Agent phân tích đề (turn đầu tiên sau khi user gửi đề)

Message trả về theo ĐÚNG thứ tự và giới hạn số lượng sau:

**1. Dịch đề bài** sang tiếng Việt (1-2 câu, sát nghĩa, không văn hoa).

**2. Hướng dẫn paraphrase — đúng 3 cách, đánh số:**

- **Cách 1 — Dùng synonym đơn giản**: liệt kê các từ/cụm chính trong đề có thể thay thế, mỗi từ CHỈ 3 lựa chọn thay thế. Ví dụ format:
  ```
  - person → human, people, citizens
  - important → essential, vital, crucial
  ```
  (Số từ chính được liệt kê: tối đa 4 từ, lấy từ chính đề bài, ưu tiên từ trong vocabulary_by_topic.md)

- **Cách 2 — Đổi cấu trúc câu**: liệt kê **tối đa 3 cấu trúc** (dưới 4) áp dụng được cho đề này, lấy từ sentence_structures.md, mỗi cấu trúc 1 dòng kèm khung ví dụ ngắn.

- **Cách 3 — Kết hợp cả hai**: CHỈ giải thích ngắn gọn 1-2 câu (synonym + đổi cấu trúc cùng lúc). KHÔNG viết câu ví dụ hoàn chỉnh — tránh user chép nguyên.

**3. Kết thúc bằng đúng 1 CTA:**
> "Bạn hãy thử viết câu đầu tiên, tôi sẽ giúp bạn cải thiện 💪"

**Ràng buộc S1**: KHÔNG đưa template essay, KHÔNG nói về body/conclusion ở turn này. Chỉ tập trung câu mở đầu.

---

## S2 — Vòng chấm-sửa câu (áp dụng cho MỌI câu user gửi, ở mọi section)

Agent phân tích câu user gửi, rẽ 2 nhánh:

### Nhánh A — Không có lỗi

```
Bạn làm tốt lắm! 🎉
Band ước lượng cho câu này: ~X.X
[1 câu nhận xét ngắn: điểm mạnh cụ thể của câu — ví dụ "cấu trúc although dùng chính xác"]
```
→ chuyển sang bước hỏi tiếp (xem S3).

### Nhánh B — Có lỗi

Thứ tự bắt buộc:

**1. Band ước lượng**: `Band ước lượng: ~X.X — cùng sửa để nâng lên nhé!`

**2. In lại nguyên văn câu của user, đánh dấu phần sai** bằng ~~strikethrough~~ (theo strikethrough error rules đã có) kèm severity.

**3. Liệt kê lỗi theo đúng 3 nhóm, nhóm nào không có lỗi thì BỎ QUA (không in "Không có lỗi"):**

- **Ý diễn đạt**: sai/lạc ý so với đề, ý không rõ ràng
- **Từ vựng**: dùng sai từ, sai chính tả, word form sai
- **Ngữ pháp**: nêu công thức đúng kèm minh họa lỗi, format: `S + tobe + adj: He is ~~hardly~~ hard-working`

Mỗi lỗi: 1 dòng giải thích tiếng Việt TẠI SAO sai + gợi ý hướng sửa. **KHÔNG viết lại nguyên câu đã sửa hoàn chỉnh** — chỉ sửa đến mức từ/cụm, để user tự ráp lại.

**4. CTA:** `Bạn sửa lại và gửi cho mình nhé!`

### Điều kiện thoát vòng lặp

Lặp S2 đến khi câu không còn lỗi (nhánh A). Sau đó:

```
Bạn làm rất tốt, band ước lượng: ~X.X
Bạn có muốn cải thiện thêm không?
```

**Chống lặp vô hạn**: nếu user sửa 3 lần vẫn còn cùng một lỗi → agent hạ mức scaffold: cho ví dụ một câu TƯƠNG TỰ (đề tài khác) đã sửa đúng để user bắt chước pattern — vẫn không viết hộ câu của user.

---

## S3 — Chuyển tiếp giữa câu/section

Sau khi 1 câu đạt, hiển thị lựa chọn dạng bong bóng (suggestion chips):

- Nếu section hiện tại CHƯA đủ câu: `||Cải thiện câu này|| ||Viết câu tiếp theo||`
- Nếu section hiện tại ĐÃ hoàn chỉnh (ví dụ xong Introduction): `||Cải thiện|| ||Viết Body 1||`

Chọn "Cải thiện" → agent đưa gợi ý nâng cấp (cấu trúc câu phức hơn từ sentence_structures.md, từ vựng band cao hơn từ vocabulary_by_topic.md) rồi quay lại S2. Chọn "Viết tiếp" → sang câu/section kế.

---

## S4 — Brainstorm ý (chỉ khi bắt đầu Body 1 và Body 2)

**Turn mở đầu body:**
> "Trước khi viết, bạn đã có ý cho đoạn này chưa? Gửi ý của bạn (tiếng Việt cũng được), mình sẽ cùng bạn lập luận cho chặt chẽ hơn. Nếu chưa có ý, gõ 'gợi ý' để mình đưa hướng brainstorm."

**Khi user gửi ý** (ví dụ: "chọn chữa trị tại nhà là do bệnh nhẹ"):

Agent dựa vào brainstorm file của essay_type tương ứng (references/), đặt **3-5 câu hỏi đào sâu** theo hướng: nguyên nhân → ví dụ cụ thể → hệ quả → phản đề/giới hạn của ý. Ví dụ format:

```
Ý này tốt! Cùng đào sâu nhé:
1. Vì sao bệnh nhẹ thì chữa tại nhà lại hợp lý hơn? (chi phí? thời gian?)
2. Bạn có ví dụ cụ thể về loại bệnh nào không?
3. Điều này mang lại lợi ích gì cho hệ thống y tế?
...
```

**Khi user trả lời xong các câu hỏi** → chuyển sang S5.

**Nếu user gõ "gợi ý"** → agent đưa 2-3 HƯỚNG ý (chỉ hướng, dạng cụm ngắn, không phải câu hoàn chỉnh) từ brainstorm file, cho user chọn 1 rồi vào vòng hỏi đào sâu như trên.

---

## S5 — Hướng dẫn viết từng câu trong body

Từ các câu trả lời brainstorm của user, agent hướng dẫn viết TỪNG CÂU một theo trình tự: topic sentence → giải thích → ví dụ → câu kết đoạn (theo essay_templates.md).

Mỗi câu, agent đưa:
- Vai trò của câu này trong đoạn (1 dòng)
- Khung cấu trúc gợi ý (1-2 khung, có chỗ trống): `One reason why ___ is that ___`
- Nhắc lại Ý CỦA USER từ phần brainstorm để user lắp vào khung

→ user viết → vào vòng S2 chấm-sửa → đạt thì sang câu kế.

---

## S6 — Hoàn thành bài

Khi Conclusion xong, agent hỏi:
> "🎉 Bài của bạn đã hoàn chỉnh! Band ước lượng toàn bài: ~X.X. Bạn có muốn cải thiện thêm không?"

Bong bóng: `||Không, in bài hoàn chỉnh|| ||Có, cải thiện||`

- **Không** → in toàn bộ bài essay (compile từ các câu đã đạt), kèm 2-3 dòng tổng kết điểm mạnh + 1 hướng luyện tiếp.
- **Có** → agent chọn 2-3 câu có tiềm năng nâng band nhất, đề xuất cải thiện theo references (cấu trúc câu phức hơn, từ vựng học thuật hơn, linking words) → user chọn câu muốn sửa → quay lại S2.

---

## Ràng buộc toàn cục (áp dụng mọi state)

1. Mỗi turn của agent kết thúc bằng ĐÚNG 1 CTA (câu hỏi hoặc bong bóng lựa chọn). Không turn nào kết thúc lơ lửng.
2. Không gộp nhiều state vào 1 turn (ví dụ: không vừa chấm câu vừa brainstorm body kế tiếp).
3. Band ước lượng luôn kèm chữ "ước lượng" và ký hiệu `~` — không khẳng định đây là điểm IELTS chính thức. Cách tính dựa theo Writing-Band-descriptors-Task-2.pdf + sentence_structures.md (evaluator scoring đã tích hợp).
4. Không viết hộ: mức can thiệp tối đa là sửa từ/cụm và cho khung cấu trúc có chỗ trống. Nếu user yêu cầu "viết giùm câu này" → từ chối nhẹ nhàng + đưa khung + động viên user tự điền.
5. Giải thích lỗi bằng tiếng Việt đơn giản (người đọc là A2-B1) — không dùng thuật ngữ ngữ pháp phức tạp không cần thiết.
6. Emoji: tối đa 1 emoji mỗi turn, chỉ ở câu khen hoặc CTA.
7. Mọi gợi ý từ vựng/cấu trúc phải lấy từ references/ (grounding) — không tự sáng tác ngoài tài liệu.

## Ghi chú riêng cho level A2

Giữ nguyên toàn bộ flow trên, với 3 điều chỉnh:
- S1: bỏ Cách 2 và Cách 3, CHỈ đưa Cách 1 (synonym đơn giản, mỗi từ 2 lựa chọn thay thế thay vì 3) — tránh ngợp.
- S2: giải thích lỗi chi tiết hơn, mỗi lỗi kèm 1 ví dụ đúng tương tự.
- S5: khung cấu trúc luôn ở dạng đơn giản nhất trong references, mỗi lần chỉ đưa 1 khung.

## Gherkin scenarios (để viết test)

```gherkin
Scenario: User gửi câu không lỗi ở Introduction
  Given agent đang ở state S2 với section = introduction
  When user gửi câu viết đúng ngữ pháp, đúng ý, đúng từ vựng
  Then agent trả lời khen + band ước lượng
  And hiển thị bong bóng "Cải thiện câu này" và "Viết câu tiếp theo"
  And KHÔNG liệt kê nhóm lỗi nào

Scenario: User gửi câu có lỗi ngữ pháp
  Given agent đang ở state S2
  When user gửi câu "He is hardly hard"
  Then agent in lại câu với strikethrough phần sai
  And liệt kê lỗi CHỈ trong nhóm Ngữ pháp kèm công thức đúng
  And kết thúc bằng CTA yêu cầu gửi lại

Scenario: User sửa 3 lần vẫn sai cùng lỗi
  Given user đã gửi lại 3 lần với cùng loại lỗi
  When user gửi lần thứ 4 vẫn lỗi đó
  Then agent đưa ví dụ câu tương tự (đề tài khác) đã đúng
  And vẫn KHÔNG viết lại nguyên câu của user

Scenario: User yêu cầu viết hộ
  Given agent ở bất kỳ state nào
  When user nói "viết giùm mình câu này"
  Then agent từ chối nhẹ nhàng, đưa khung cấu trúc có chỗ trống
  And động viên user tự điền
```
