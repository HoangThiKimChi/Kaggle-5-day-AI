---
name: writing-problem-solution-essays
description: >
  Use this skill when the user needs to write or get guidance on an IELTS
  Writing Task 2 Problem-Solution essay. Covers analyzing causes vs effects,
  matching solutions directly to identified causes, and defining responsible
  actors (e.g., government, companies, individuals).
---

# Skill: Writing Problem-Solution Essays (IELTS Task 2)

Skill này hướng dẫn coach (agent) cách dẫn dắt học viên A2-B1 viết
**Problem-Solution Essay** (bàn luận về nguyên nhân/vấn đề và đề xuất giải pháp).

---

## When to Use

Trigger skill này khi đề bài chứa bất kỳ cụm từ khoá sau:

| Keyword | Ví dụ đề thật |
|---|---|
| `what are the causes` | "What are the causes of this problem...?" |
| `what solutions` | "What solutions can you suggest?" |
| `how could this be solved` | "How could this problem be solved?" |
| `what can be done to solve` | "What can be done to solve this?" |
| `reasons for this` | "What are the reasons for this?" |
| `how could this problem be tackled` | "How could this problem be tackled?" |

---

## Structure

Lấy trực tiếp từ `_SECTION_ROLE` entries với key `"problem_solution"` trong `tools.py`:

```
Introduction  → Paraphrase đề + Nêu sẽ phân tích nguyên nhân và đề xuất giải pháp.
Body 1        → Nguyên nhân/Vấn đề: 2-3 nguyên nhân chính, mỗi cái có giải thích.
Body 2        → Giải pháp: 2-3 giải pháp thực tế, mỗi cái có giải thích tại sao hiệu quả.
Conclusion    → Tóm tắt nguyên nhân và giải pháp + Kêu gọi hành động/Khuyến nghị.
```

---

## Examples

### Input → Output mẫu: Introduction

**Đề bài gốc:**
> *"Traffic congestion is a major problem in many cities. What are the causes of this problem, and what measures could be taken to reduce it?"*

**Paraphrase + Thesis mẫu (trình độ B1):**
> *"Traffic congestion has become one of the most pressing urban challenges in cities around the world. This essay will examine the main reasons why this problem has developed and suggest practical measures that could be taken to address it."*

---

## Anti-patterns

Những lỗi agent PHẢI tránh khi dùng skill này:

### ❌ Giải pháp không tương ứng với Nguyên nhân đã nêu (Lack of Logical Fit)
> **Sai:** Body 1 nêu nguyên nhân kẹt xe là do "xe cá nhân quá nhiều", nhưng Body 2 lại chỉ đề xuất giải pháp là "xây thêm công viên giải trí".
>
> **Đúng:** Đảm bảo mỗi giải pháp đưa ra ở Body 2 phải giải quyết trực tiếp một nguyên nhân đã phân tích ở Body 1 (ví dụ: giải pháp đánh thuế xe cá nhân hoặc nâng cấp giao thông công cộng).

### ❌ Giải pháp quá mơ hồ hoặc chung chung
> **Sai:** *"The government should solve the problem."* hoặc *"People should stop using cars."*
>
> **Đúng:** Đề xuất hành động cụ thể và có tính khả thi: *"Governments could invest in underground metro systems..."* hoặc *"Schools should educate children about green transport options..."*.

### ❌ Nhầm lẫn giữa dạng bài Problem-Solution và Adv/Dis
> **Sai:** Viết về "lợi ích" và "tác hại" của kẹt xe.
>
> **Đúng:** Tập trung hoàn toàn vào câu hỏi **Tại sao (Why)** nó xảy ra và **Làm thế nào (How)** để khắc phục.

---

## References

- `references/problem_solution_brainstorm.md` — brainstorm framework đầy đủ, các biến thể bài viết, các ý tưởng theo chủ đề (traffic, obesity, work stress)
- `tools.py: guide_essay_section()` — tool chính để gọi khi hướng dẫn từng section
- `tools.py: paraphrase_prompt()` — tool paraphrase đề bài
- `tools.py: _CLASSIFICATION_RULES["problem_solution"]` — danh sách keywords nhận diện
