---
name: writing-two-part-essays
description: >
  Use this skill when the user needs to write or get guidance on an IELTS
  Writing Task 2 Two-Part Question essay. Covers identifying multiple distinct
  question prompts, structuring dedicated body paragraphs for each question,
  and summarizing both responses in the introduction and conclusion.
---

# Skill: Writing Two-Part Question Essays (IELTS Task 2)

Skill này hướng dẫn coach (agent) cách dẫn dắt học viên A2-B1 viết
**Two-Part Question Essay** (dạng đề có 2 câu hỏi riêng biệt).

---

## When to Use

Trigger skill này khi đề bài chứa 2 dấu chấm hỏi (?) hoặc có 2 câu hỏi rõ ràng (nhận diện qua `_is_two_part_question()` và `classify_essay_type` trong code):

| Ví dụ câu hỏi |
|---|
| "What are the reasons for this? Is this a positive or negative development?" |
| "Why is this the case? What effect does it have on young people?" |
| "To what extent do you agree? What can be done to solve the problem?" |

---

## Structure

Lấy trực tiếp từ `_SECTION_ROLE` entries với key `"two_part_question"` trong `tools.py`:

```
Introduction  → Paraphrase đề + báo sẽ trả lời cả 2 câu hỏi.
Body 1        → Trả lời Câu hỏi 1: Topic sentence → Giải thích → Ví dụ.
Body 2        → Trả lời Câu hỏi 2: Topic sentence → Giải thích → Ví dụ.
Conclusion    → Kết luận — tóm tắt câu trả lời cho cả 2 câu hỏi ngắn gọn.
```

---

## Examples

### Input → Output mẫu: Introduction

**Đề bài gốc:**
> *"In many countries, the number of people choosing to live alone is increasing. What are the reasons for this? Is this a positive or negative development?"*

**Paraphrase + Thesis mẫu (trình độ B1):**
> *"An increasing number of people in modern societies are choosing to live independently rather than with family members. This essay will explore the main reasons behind this trend before arguing that, on balance, it represents a negative development."*

---

## Anti-patterns

Những lỗi agent PHẢI tránh khi dùng skill này:

### ❌ Bỏ quên một câu hỏi (Only answering one question)
> **Sai:** Chỉ trả lời lý do tại sao người ta thích sống một mình (Q1) và quên nhận định đó là xu hướng tích cực hay tiêu cực (Q2).
>
> **Đúng:** Luôn rà soát và kiểm tra kĩ xem học viên đã trả lời đủ cả 2 câu hỏi chưa.

### ❌ Dồn câu trả lời của 2 câu hỏi vào chung một đoạn thân bài
> **Sai:** Viết chung lý do (reasons) và tác động (effects) vào chung Body 1, để trống Body 2.
>
> **Đúng:** Chia rõ: Body 1 trả lời hoàn chỉnh câu hỏi 1, Body 2 trả lời hoàn chỉnh câu hỏi 2.

### ❌ Sự mất cân bằng giữa hai đoạn thân bài
> **Sai:** Viết Body 1 cực kỳ dài (150 từ) nhưng Body 2 chỉ có 1-2 câu ngắn (40 từ).
>
> **Đúng:** Phân bổ ý cân đối để hai đoạn thân bài có độ dài tương đương nhau, đảm bảo điểm Coherence and Cohesion tốt.

---

## References

- `references/two_part_question_brainstorm.md` — brainstorm framework đầy đủ, các biến thể câu hỏi, lỗi thường gặp
- `tools.py: guide_essay_section()` — tool chính để gọi khi hướng dẫn từng section
- `tools.py: paraphrase_prompt()` — tool paraphrase đề bài
- `tools.py: _is_two_part_question()` — hàm heuristic kiểm tra số dấu hỏi
