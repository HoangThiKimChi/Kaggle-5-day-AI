"""
verify_b1_turn2.py — Verify B1 Flow, Turn 2 (2 requests: context + guide)
Gửi đề bài → chọn paraphrase → xác nhận guide_essay_section được gọi

Chạy: source ~/.zshrc && python3 verify_b1_turn2.py
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
os.environ["MOCK_GEMINI"] = "0"

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    print("⚠️ GEMINI_API_KEY không tìm thấy. Chạy: source ~/.zshrc")
    sys.exit(1)
os.environ.setdefault("GOOGLE_API_KEY", API_KEY)

from app import run_turn_structured, create_runner

runner = create_runner()
sid = f"b1_t2_{int(time.time())}"
uid = "verify_user"

# Turn 1: gửi đề bài (tạo context)
msg1 = "[Level: B1] Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?"

print("=" * 60)
print("VERIFY B1 — Turn 2: Guide Introduction (cần context turn 1)")
print("=" * 60)
print(f"Turn 1 (context): gửi đề bài...")

r1 = run_turn_structured(runner, sid, uid, msg1)
print(f"Turn 1 OK — {len(r1['text'])} ký tự, {len(r1['tool_calls'])} tool calls")

print("\n⏳ Chờ 15 giây...")
time.sleep(15)

# Turn 2: chọn paraphrase + xin hướng dẫn introduction
msg2 = "[Level: B1] Tôi chọn cách 1. Hãy hướng dẫn tôi viết Introduction."
print(f"\nTurn 2: {msg2[12:]}")

r2 = run_turn_structured(runner, sid, uid, msg2)

print(f"\nAgent response ({len(r2['text'])} ký tự):")
print(r2["text"])

if r2["tool_calls"]:
    print(f"\nTool Calls ({len(r2['tool_calls'])}):")
    for tc in r2["tool_calls"]:
        print(f"  • {tc['tool']} → keys: {list((tc.get('result') or {}).keys())}")

# Tự đánh giá
has_guide = any(tc["tool"] == "guide_essay_section" for tc in r2["tool_calls"])
has_text = len(r2["text"]) > 50
remembers = any(kw in r2["text"].lower() for kw in ["introduction", "music", "opinion", "mở bài", "paraphrase"])

print(f"\n{'✅' if has_guide else '❌'} guide_essay_section được gọi")
print(f"{'✅' if has_text else '❌'} Agent trả lời có nội dung")
print(f"{'✅' if remembers else '⚠️'} Agent nhớ context từ turn 1")
print(f"\n{'✅ B1 TURN 2 PASS' if all([has_guide, has_text]) else '❌ B1 TURN 2 FAIL'}")
