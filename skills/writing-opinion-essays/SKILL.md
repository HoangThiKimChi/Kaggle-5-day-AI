---
name: writing-opinion-essays
description: >
  Use this skill when the user needs to write or get guidance on an IELTS
  Writing Task 2 Opinion essay (agree/disagree, to what extent). Covers
  thesis statement construction, two-reason structure, and paraphrase
  techniques specific to opinion essays.
---

# Skill: Writing Opinion Essays (IELTS Task 2)

Skill này hướng dẫn coach (agent) cách dẫn dắt học viên A2-B1 viết
**Opinion Essay** — dạng phổ biến nhất trong IELTS Writing Task 2.

---

## When to Use

Trigger skill này khi đề bài chứa bất kỳ cụm từ khoá sau (lấy trực tiếp
từ `_CLASSIFICATION_RULES["opinion"]` trong `tools.py` để đảm bảo nhất quán):

| Keyword | Ví dụ đề thật |
|---|---|
| `agree or disagree` | "Do you agree or disagree?" |
| `to what extent` | "To what extent do you agree or disagree?" |
| `do you think` | "Do you think this is a positive development?" |
| `in your opinion` | "In your opinion, what should be done?" |
| `how far do you agree` | "How far do you agree with this statement?" |
| `give your own opinion` | "Give your own opinion and reasons." |

**Không trigger** nếu đề bài dùng "Discuss both views", "What are the
advantages and disadvantages", hay "What are the causes/solutions" — đó là
các dạng khác (discussion, adv_dis, problem_solution).

---

## Structure

Lấy trực tiếp từ `_SECTION_ROLE` entries với key `"opinion"` trong `tools.py`:

```
Introduction  → Paraphrase đề + nêu thesis (agree/disagree) + báo sẽ đưa ra 2 lý do.
Body 1        → Lý do 1 ủng hộ quan điểm: Topic sentence → Giải thích → Ví dụ cụ thể.
Body 2        → Lý do 2 ủng hộ quan điểm: Topic sentence → Giải thích → Ví dụ cụ thể.
Conclusion    → Tóm tắt 2 lý do + nhắc lại quan điểm cá nhân (không đưa ý mới).
```

### Flow hướng dẫn từng section

1. **Introduction**: Dùng `guide_essay_section(section="introduction", essay_type="opinion")`.
   Agent trình bày: template điền vào, ví dụ mẫu, 3 lỗi thường gặp.

2. **Body 1 & 2**: Dùng `guide_essay_section(section="body1"/"body2", essay_type="opinion")`.
   Nhấn mạnh cấu trúc **Topic Sentence → Explanation → Example** (TEE pattern).

3. **Conclusion**: Dùng `guide_essay_section(section="conclusion", essay_type="opinion")`.
   Nhắc: KHÔNG đưa ý mới, KHÔNG copy nguyên văn từ intro.

### Plan phù hợp trình độ A2-B1

> Khuyến nghị cho người mới: chọn **Plan 1 (Agree mạnh)** — đồng ý hoàn toàn,
> 2 lý do rõ ràng. Tránh "partly agree" vì khó kiểm soát structure.

| Plan | Cách tổ chức | Dùng khi |
|---|---|---|
| Plan 1 — Agree mạnh | Body1: lý do 1 đồng ý → Body2: lý do 2 đồng ý | Đồng ý hoàn toàn ✅ (khuyến nghị A2-B1) |
| Plan 2 — Balanced | Body1: lập luận đồng ý → Body2: lập luận phản đối | Đồng ý một phần |
| Plan 3 — Disagree | Body1: acknowledge opposing → Body2-3: lý do phản đối | Không đồng ý |

---

## Examples

### Input → Output mẫu: Introduction

**Đề bài gốc:**
> *"Some people say that music is a good way of bringing people of different
> cultures and ages together. To what extent do you agree or disagree?"*

**Paraphrase + Thesis mẫu (trình độ B1):**
> *"It is often argued that music serves as an effective means of uniting
> individuals from diverse cultural backgrounds and generations. I completely
> agree with this view for two main reasons."*

**Kỹ thuật paraphrase đã dùng:**
- `music` → *musical expression / melodies*
- `bringing people together` → *uniting individuals*
- `different cultures and ages` → *diverse cultural backgrounds and generations*
- `To what extent do you agree` → *I completely agree / strongly believe*

---

### Input → Output mẫu: Body 1

**Ý user muốn diễn đạt:** "âm nhạc có lời nên mọi người hiểu nhau dù khác ngôn ngữ"

**Topic sentence mẫu (B1):**
> *"Firstly, music transcends language barriers, allowing people from
> different countries to connect emotionally even without sharing the same
> language."*

**TEE pattern hoàn chỉnh:**
1. **Topic sentence**: nêu lý do rõ ràng
2. **Explanation**: giải thích cơ chế ("Because lyrics carry universal emotions...")
3. **Example**: ví dụ cụ thể ("For instance, K-pop has gained millions of fans worldwide...")

---

## Anti-patterns

Những lỗi agent PHẢI tránh khi dùng skill này:

### ❌ Viết hộ essay
> **Sai:** Agent tự sinh ra bài viết hoàn chỉnh khi user chưa viết gì.
>
> **Đúng:** Agent hướng dẫn từng bước, đưa template và ví dụ, rồi chờ user
> tự viết vào tab "Bài viết". Đây là nguyên tắc cốt lõi: **coach, không
> phải ghostwriter.**

### ❌ Skip sections
> **Sai:** User vừa gửi đề bài, agent nhảy thẳng vào hướng dẫn body1.
>
> **Đúng:** Luôn đi theo thứ tự: classify → paraphrase → introduction →
> body1 → body2 → conclusion. Không nhảy cóc dù user yêu cầu.

### ❌ Lặp từ từ đề bài trong mở bài
> **Sai:** *"Music is a good way of bringing people of different cultures and
> ages together."* (copy gần như nguyên văn)
>
> **Đúng:** Paraphrase ít nhất 3-4 từ chính, thay đổi cấu trúc câu, giữ
> nguyên nghĩa gốc.

### ❌ Đưa ý mới vào conclusion
> **Sai:** Kết bài đột ngột đề xuất "governments should fund music education".
>
> **Đúng:** Conclusion chỉ tóm tắt 2 lý do đã nêu + nhắc lại quan điểm.

### ❌ "Partly agree" không kiểm soát được
> **Sai (với A2-B1):** Đồng ý một phần, body1 đồng ý, body2 phản đối —
> nhưng conclusion không kết hợp được rõ ràng.
>
> **Đúng:** Khuyến nghị user chọn 1 phía rõ ràng (agree hoặc disagree
> hoàn toàn) để structure đơn giản và dễ kiểm soát.

---

## References

- `references/opinion_brainstorm.md` — brainstorm framework đầy đủ, 3 kiểu
  plan, ví dụ Cambridge thật
- `tools.py: guide_essay_section()` — tool chính để gọi khi hướng dẫn
  từng section
- `tools.py: paraphrase_prompt()` — tool paraphrase đề bài
- `tools.py: _CLASSIFICATION_RULES["opinion"]` — danh sách keywords nhận diện
- `tools.py: _SECTION_ROLE` — role description cho từng section
