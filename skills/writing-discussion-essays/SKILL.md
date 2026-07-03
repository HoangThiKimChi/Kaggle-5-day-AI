---
name: writing-discussion-essays
description: >
  Use this skill when the user needs to write or get guidance on an IELTS
  Writing Task 2 Discussion essay (discuss both views and give your opinion).
  Covers objective body paragraph structuring, balance, and transitional
  phrases specific to discussion essays.
---

# Skill: Writing Discussion Essays (IELTS Task 2)

Skill này hướng dẫn coach (agent) cách dẫn dắt học viên A2-B1 viết
**Discussion Essay** (bàn luận hai quan điểm và đưa ra ý kiến cá nhân).

---

## When to Use

Trigger skill này khi đề bài chứa bất kỳ cụm từ khoá sau:

| Keyword | Ví dụ đề thật |
|---|---|
| `discuss both views` | "Discuss both views and give your opinion." |
| `discuss both these views` | "Discuss both these views and give your own opinion." |
| `discuss both` | "Discuss both sides of this argument." |

**Không trigger** nếu đề bài chỉ yêu cầu đồng ý hay không đồng ý (Opinion essay) hoặc phân tích nguyên nhân/giải pháp (Problem-Solution).

---

## Structure

Lấy trực tiếp từ `_SECTION_ROLE` entries với key `"discussion"` trong `tools.py`:

```
Introduction  → Paraphrase đề + Nêu 2 phía tranh luận + Báo sẽ xem xét cả hai.
Body 1        → Quan điểm A: trình bày + giải thích + ví dụ từ nhóm ủng hộ View A.
Body 2        → Quan điểm B: trình bày + giải thích + ví dụ từ nhóm ủng hộ View B + nêu ý kiến cá nhân.
Conclusion    → Kết luận — tóm tắt 2 quan điểm + khẳng định lại ý kiến cá nhân.
```

---

## Examples

### Input → Output mẫu: Introduction

**Đề bài gốc:**
> *"Some people think that competition at work, school and daily life is a good thing. Others believe that we should try to cooperate more rather than competing. Discuss both these views and give your own opinion."*

**Paraphrase + Thesis mẫu (trình độ B1):**
> *"There is ongoing debate about whether competition or cooperation leads to better outcomes in work and education. While some argue that a competitive environment drives individuals to excel, others contend that collaboration produces superior results. This essay will examine both perspectives before explaining why I believe cooperation is more beneficial."*

---

## Anti-patterns

Những lỗi agent PHẢI tránh khi dùng skill này:

### ❌ Chỉ viết một phía
> **Sai:** Chỉ phân tích lợi ích của sự hợp tác (Cooperation) và bỏ qua lập luận của sự cạnh tranh (Competition).
>
> **Đúng:** Body 1 viết riêng về sự cạnh tranh, Body 2 viết về sự hợp tác. Cần cân bằng lượng từ và ý cho cả hai phía.

### ❌ Thiếu ý kiến cá nhân (Thesis Statement)
> **Sai:** Chỉ tóm tắt hai phía mà không nêu rõ mình thiên về phía nào ở Mở bài và Kết bài.
>
> **Đúng:** Luôn có câu "I believe/In my opinion..." để làm rõ lập trường cá nhân.

### ❌ Dùng đại từ cá nhân "I" quá nhiều trong Thân bài
> **Sai:** *"I think competition is good because it motivates me."*
>
> **Đúng:** Dùng các chủ ngữ khách quan: *"Supporters of competition argue that..."* hoặc *"It is believed that..."*. Lập trường cá nhân để dành cho Intro và Conclusion.

---

## References

- `references/discussion_brainstorm.md` — brainstorm framework đầy đủ, các cặp từ đối lập, lỗi thường gặp
- `tools.py: guide_essay_section()` — tool chính để gọi khi hướng dẫn từng section
- `tools.py: paraphrase_prompt()` — tool paraphrase đề bài
- `tools.py: _CLASSIFICATION_RULES["discussion"]` — danh sách keywords nhận diện
