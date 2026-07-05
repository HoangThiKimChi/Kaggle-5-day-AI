# GEMINI.md — Essay Writing Coach Capstone

> File này được Antigravity tự động đọc mỗi khi mở project `Capstone/`.
> Mục đích: giữ context nền xuyên suốt các phiên làm việc, không cần Chi giải thích lại từ đầu.

---

## Bối cảnh dự án

AI agent hướng dẫn người Việt viết IELTS Writing Task 2, target level A2-B1.
Capstone cho khóa Kaggle × Google 5-Day AI Agents Intensive.
Deadline: **06/07/2026 nửa đêm PT**. Track: Agents for Good (Education).

Vấn đề đang giải quyết: người học có ý trong đầu nhưng không biết diễn đạt —
không biết paraphrase đề, cấu trúc câu đơn điệu, từ vựng nghèo, không biết
bắt đầu từng phần essay. Khác Grammarly (chỉ sửa lỗi) và ChatGPT (trả lời 1 cú)
ở chỗ hướng dẫn từng bước, bằng tiếng Việt.

---

## Nguyên tắc bất di bất dịch (KHÔNG tự ý thay đổi)

- **Single-agent architecture** — không đề xuất chuyển sang multi-agent.
- **Mọi giải thích/hướng dẫn trả về cho end-user PHẢI bằng tiếng Việt.**
  Ví dụ câu, thuật ngữ kỹ thuật giữ nguyên tiếng Anh.
- **Framework bắt buộc: Google ADK + Gemini API.** Không đề xuất đổi sang
  provider khác. Đổi *model* trong cùng hệ Gemini thì được (đã làm 2 lần
  vì lý do cụ thể — xem "Model đang dùng" bên dưới), nhưng luôn phải xác
  nhận tên model bằng `client.models.list()`, không đoán tên.
- **Không tự thêm feature ngoài 4 chức năng đã chốt**: paraphrase đề bài,
  hướng dẫn từng phần essay, gợi ý cấu trúc câu, làm giàu từ vựng.
- **Không login/auth, không multi-user.** Single-user demo cho capstone.
- **Agent không tự viết hộ essay** — chỉ hướng dẫn. User tự gõ vào UI.
  Đây là định vị cốt lõi: coach, không phải ghostwriter.
- **Cá nhân hóa hội thoại & Chẩn đoán trình độ:** Bắt buộc chẩn đoán điểm mạnh/yếu của học viên trong các câu viết nháp đầu tiên (Student Profiling), theo dõi sự tiến bộ giữa các lượt chat (Progress Tracking) để động viên hoặc sửa lỗi lặp, và gợi ý chuyển đổi trình độ linh hoạt (B1 xuống A2 nếu viết quá yếu; A2 lên B1 nếu viết rất vững).

---

## Model đang dùng

**`gemini-2.5-flash`** (đã nâng cấp lên gói PRO có hạn mức cao hơn từ ngày 03/07/2026 sau khi nạp tiền prepaid credit). Nếu cần đổi model lần nữa, LUÔN xác nhận tên chính xác qua `client.models.list()` trước, không đoán.

## Quy ước quota — MOCK_GEMINI

Free tier, không có billing. Để tránh lặp lại việc tốn quota vào debug:

- **Mặc định mọi lần code/test/debug dùng `MOCK_GEMINI=1`** — `_call_gemini()`
  trong `tools.py` trả response giả cố định, không gọi API thật.
- **Chỉ dùng request thật khi Chi yêu cầu rõ ràng** ("chạy test thật",
  "verify thật") — vì mỗi request thật là tài nguyên giới hạn trong ngày.
- Trước khi dùng request thật, nên tính toán trước cần bao nhiêu request,
  báo cho Chi biết con số đó để quyết định.
- **KHÔNG ping thử trước khi chạy verify** — mỗi lần ping tốn 1 request.
- **KHÔNG đổi model qua lại giữa các lần thử** — giữ nguyên model đang dùng.
- **Nếu 503 (server quá tải)** → đợi 5-10 phút rồi thử lại đúng file đó, KHÔNG chuyển sang model khác (vì model khác có thể đã hết quota riêng).
- **Mỗi request thật phải có mục đích rõ ràng**, tránh lãng phí quota.

---

## Cấu trúc file trong project

```
Capstone/
├── tools.py          ← 5 tools, có mock layer (MOCK_GEMINI=1)
├── agent.py          ← LlmAgent chính, import TOOLS từ tools.py
├── app.py            ← Streamlit UI (đang code, xem ui_spec.md)
├── test_streamlit_integration.py  ← Test 3 điểm chặn cứng cho UI
├── ui_spec.md         ← Spec đầy đủ cho app.py — ĐỌC trước khi sửa UI
├── full_spec_audit.md ← Rà soát gap, đọc cùng ui_spec.md
├── eval_cases.json    ← 5 eval case dạng EDD
├── references/        ← Chỉ tài liệu tĩnh (.md). KHÔNG đặt code vào đây.
├── Tài liệu/
├── checklist.md        ← Checklist tổng, cập nhật khi có tiến độ mới
└── Requirement.md
```

---

## Quy ước làm việc với Chi

- **Luôn đề xuất cấu trúc/approach trước khi code toàn bộ.** Chờ Chi xác
  nhận rõ ràng rồi mới thực thi.
- **Khi lỗi do thư viện/API bên ngoài** — nói rõ đây là vấn đề ngoài code,
  đừng tự "sửa" bằng cách đoán mò hoặc workaround che giấu vấn đề gốc.
- **Ưu tiên test bằng eval case cụ thể** trước khi báo "done" — không chỉ
  dựa vào "code chạy không lỗi". Mock PASS ≠ verified thật — luôn nói rõ
  đang test bằng mock hay request thật.
- **In output đầy đủ, dễ đọc khi test** — không chỉ raw JSON/dict.
- **Không chạy lệnh có rủi ro** mà không hỏi trước.
- **Không để lộ giá trị API key** trong output/log hiển thị cho Chi xem —
  từng xảy ra 1 lần, đã fix, cần tránh lặp lại.

---

## Trạng thái hiện tại (cập nhật 03/07/2026 chiều)

- ✅ `tools.py`, `agent.py` — hoàn thành, đã cấu hình mô hình linh hoạt (mặc định flash, tự động fallback flash-lite khi 429/503).
- ✅ Giai đoạn 1 (3 điểm chặn cứng cho UI) — PASS bằng cả Mock và Live API.
- ✅ Giai đoạn 2 (`app.py`, `test_level_flows.py` và `verify_real_level_flows.py`) — hoàn thành, phân luồng B1 và A2 hoạt động trơn tru.
- ✅ Giai đoạn 3 (IELTS Essay Evaluator) — hoàn thành, chấm điểm từ 1.0 đến 6.5 chuẩn IELTS, tích hợp cache, quota fallback, và cập nhật giao diện 3 tab trên Streamlit Cloud.
- ⏳ Chưa làm: quay video demo, điền các link demo/video vào Writeup và submit bài viết chính thức lên Kaggle.

Không bao giờ dùng git push -f lên bất kỳ remote nào, kể cả khi push thường bị reject — dừng và báo lại.

