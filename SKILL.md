---
name: ielts-essay-writing-coach
description: >
  An IELTS Writing Task 2 writing coach agent for Vietnamese A2-B1 learners.
  Guides users step-by-step through essay classification, outline planning,
  introductory paraphrasing, paragraph-based guidance, and evaluation.
---

# Skill: IELTS Writing Task 2 Essay Coach

Skill này đóng vai trò là một người hướng dẫn viết luận IELTS Task 2 cho người Việt trình độ A2-B1, đồng hành từng phần thay vì viết hộ.

---

## 1. Directory Structure (Cấu trúc thư mục)

Dự án được cấu trúc theo chuẩn Agent Skill của khóa học Kaggle × Google:

```
Capstone/
├── SKILL.md                 # Tài liệu hướng dẫn & metadata của Skill
├── requirements.txt         # Các thư viện phụ thuộc
├── references/              # Dữ liệu tĩnh làm context chấm điểm & brainstorm
│   ├── ielts_scoring_rubric.json
│   ├── rubric_diem_ielts.md
│   ├── opinion_brainstorm.md
│   ├── discussion_brainstorm.md
│   ├── adv_dis_brainstorm.md
│   ├── problem_solution_brainstorm.md
│   └── two_part_question_brainstorm.md
├── scripts/                 # Mã nguồn thực thi chính
│   ├── agent.py             # Logic Agent chính (LlmAgent)
│   ├── tools.py             # 6 công cụ (Tools) bổ trợ
│   ├── app.py               # Giao diện web Streamlit UI
│   ├── test_level_flows.py  # Script kiểm thử Mock E2E
│   └── verify_real_level_flows.py  # Script chạy kiểm thử thực tế
└── assets/                  # Các tài liệu đặc tả thiết kế & specs
    ├── spec_evaluate_essay.md
    └── ui_spec.md
```

---

## 2. Core Capabilities (Năng lực cốt lõi)

1.  **Phân loại đề bài (Classify):** Nhận diện đề bài thuộc 1 trong 5 dạng IELTS Task 2.
2.  **Dịch đề bài:** Dịch tự nhiên sang tiếng Việt giúp học viên nắm rõ nghĩa của đề bài.
3.  **Tạo Paraphrase (Level B1):** Gợi ý 3 cách viết lại đề bài kèm phân tích kỹ thuật.
4.  **Hướng dẫn từng phần (Scaffolding):** Đưa ra template, ví dụ mẫu và checklist cho Introduction, Body 1/2, Conclusion.
5.  **Chấm điểm tự động (IELTS Evaluator):** Đánh giá bài luận hoàn chỉnh trên thang điểm 1.0 – 6.5 chuẩn IELTS dựa trên 4 tiêu chí của Rubric và tính Overall Band.

---

## 3. How to Run (Hướng dẫn khởi chạy)

Để chạy thử ứng dụng Streamlit locally:
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Chạy thử chế độ Mock (Không tốn quota)
MOCK_GEMINI=1 streamlit run scripts/app.py

# Chạy thật với Gemini API
streamlit run scripts/app.py
```
