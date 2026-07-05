# Hướng dẫn Verify E2E — Chạy từng file, tiết kiệm quota

> Tổng cộng: **6 request thật** (không phải 4 như ước tính ban đầu,
> vì turn 2 cần context từ turn 1 nên mỗi file turn 2 tốn 2 request).
>
> Quota free tier: 20 request/ngày. Chạy hết 4 file tốn 6/20 request.

---

## Thứ tự chạy

Chạy **từng file 1**, cách nhau **tối thiểu 5 phút** (tránh RPM limit).
Không chạy liên tục 4 file cùng lúc.

### File 1 — B1 Turn 1 (1 request)
```bash
source ~/.zshrc && cd Capstone && python3 verify_b1_turn1.py
```
Kỳ vọng: `✅ B1 TURN 1 PASS` — classify + paraphrase được gọi.

**Đợi 5 phút**

### File 2 — B1 Turn 2 (2 request)
```bash
python3 verify_b1_turn2.py
```
Kỳ vọng: `✅ B1 TURN 2 PASS` — guide_essay_section được gọi, agent nhớ context.

**Đợi 5 phút**

### File 3 — A2 Turn 1 (1 request)
```bash
python3 verify_a2_turn1.py
```
Kỳ vọng: `✅ A2 TURN 1 PASS` — classify gọi, paraphrase KHÔNG gọi (đúng flow A2).

**Đợi 5 phút**

### File 4 — A2 Turn 2 (2 request)
```bash
python3 verify_a2_turn2.py
```
Kỳ vọng: `✅ A2 TURN 2 PASS` — agent sửa lỗi "i think music good", giải thích ngữ pháp.

---

## Nếu gặp lỗi

| Lỗi | Nguyên nhân | Xử lý |
|---|---|---|
| 429 quota | Hết request ngày | Đợi quota reset (~07:00 sáng VN) |
| 503 unavailable | Server quá tải | Đợi 5-10 phút, thử lại đúng file đó |
| Empty response | Thinking mode | Đã fix bằng thinking_budget=0, không nên xảy ra |

## Quy tắc quan trọng

- **KHÔNG ping thử** trước khi chạy file verify — mỗi lần ping tốn 1 request
- **KHÔNG đổi model** qua lại trong lúc verify — giữ nguyên `gemini-2.5-flash-lite`
- **KHÔNG chạy lại file đã PASS** — tốn quota vô ích
- Nếu 1 file FAIL do 503 → chỉ chạy lại **đúng file đó**, không chạy lại từ đầu
