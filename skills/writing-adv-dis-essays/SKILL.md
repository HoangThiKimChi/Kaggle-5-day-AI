---
name: writing-adv-dis-essays
description: >
  Use this skill when the user needs to write or get guidance on an IELTS
  Writing Task 2 Advantages & Disadvantages essay. Covers distinguishing
  between "list" and "outweigh" variants, structuring clear body paragraphs
  for benefits and drawbacks, and formulating balanced conclusions.
---

# Skill: Writing Advantages & Disadvantages Essays (IELTS Task 2)

Skill này hướng dẫn coach (agent) cách dẫn dắt học viên A2-B1 viết
**Advantages & Disadvantages Essay** (bàn luận về ưu điểm và nhược điểm).

---

## When to Use

Trigger skill này khi đề bài chứa bất kỳ cụm từ khoá sau:

| Keyword | Ví dụ đề thật |
|---|---|
| `advantages and disadvantages` | "What are the advantages and disadvantages of...?" |
| `benefits and drawbacks` | "What are the benefits and drawbacks of...?" |
| `outweigh` | "Do the advantages outweigh the disadvantages?" |
| `positive or negative` | "Is this a positive or negative development?" |

---

## Structure

Lấy trực tiếp từ `_SECTION_ROLE` entries với key `"adv_dis"` trong `tools.py`:

```
Introduction  → Paraphrase đề + Nêu sẽ phân tích cả ưu và nhược điểm.
Body 1        → Ưu điểm (Advantages): 2-3 điểm, mỗi điểm có giải thích + ví dụ.
Body 2        → Nhược điểm (Disadvantages): 2-3 điểm, mỗi điểm có giải thích + ví dụ.
Conclusion    → Tóm tắt ưu/nhược + Đưa ra ý kiến (outweigh/positive or negative).
```

---

## Examples

### Input → Output mẫu: Introduction (Dạng Outweigh)

**Đề bài gốc:**
> *"In many countries nowadays, consumers can go to a supermarket and buy food produced all over the world. Do you think this is a positive or negative development?"*

**Paraphrase + Thesis mẫu (trình độ B1):**
> *"In many parts of the world, supermarkets now offer an enormous variety of foods sourced from different countries. This essay will examine both the positive and negative aspects of this trend before arguing that, on balance, the benefits outweigh the drawbacks."*

---

## Anti-patterns

Những lỗi agent PHẢI tránh khi dùng skill này:

### ❌ Trộn lẫn Ưu điểm và Nhược điểm trong cùng một đoạn thân bài
> **Sai:** Viết một đoạn vừa kể ra lợi ích vừa chèn thêm tác hại của điện thoại.
>
> **Đúng:** Tách bạch rõ ràng: Body 1 chỉ viết về ưu điểm (Advantages), Body 2 chỉ viết về nhược điểm (Disadvantages).

### ❌ Quên kết luận ở dạng "Outweigh" hoặc "Positive/Negative"
> **Sai:** Chỉ liệt kê ưu và nhược điểm rồi kết luận chung chung ở bài "outweigh" mà không khẳng định bên nào lớn hơn.
>
> **Đúng:** Ở Conclusion, học viên bắt buộc phải đưa ra phán quyết bên nào có sức nặng hơn (ví dụ: *"I believe that the advantages outweigh the disadvantages"*).

### ❌ Liệt kê quá nhiều ý nhỏ mà không phát triển
> **Sai:** Kể ra 4-5 ưu điểm liên tiếp mà không có câu giải thích (Explanation) hay ví dụ (Example).
>
> **Đúng:** Chỉ chọn 2 ý ưu điểm và 2 ý nhược điểm tiêu biểu nhất, rồi viết đầy đủ cấu trúc TEE (Topic Sentence → Explanation → Example) cho từng ý.

---

## References

- `references/adv_dis_brainstorm.md` — brainstorm framework đầy đủ, phân biệt các biến thể, cách viết conclusion
- `tools.py: guide_essay_section()` — tool chính để gọi khi hướng dẫn từng section
- `tools.py: paraphrase_prompt()` — tool paraphrase đề bài
- `tools.py: _CLASSIFICATION_RULES["adv_dis"]` — danh sách keywords nhận diện
