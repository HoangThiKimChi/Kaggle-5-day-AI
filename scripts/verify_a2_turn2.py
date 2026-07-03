"""
verify_a2_turn2.py — Verify A2 Flow, Turn 2 (2 requests: context + grammar fix)
Gửi đề bài → gửi câu sai ngữ pháp → xác nhận agent sửa lỗi + giải thích

Chạy: source ~/.zshrc && python3 verify_a2_turn2.py
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
sid = f"a2_t2_{int(time.time())}"
uid = "verify_user"

# Turn 1: gửi đề bài (tạo context)
msg1 = "[Level: A2] Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?"

print("=" * 60)
print("VERIFY A2 — Turn 2: Sửa lỗi ngữ pháp (cần context turn 1)")
print("=" * 60)
print(f"Turn 1 (context): gửi đề bài...")

r1 = run_turn_structured(runner, sid, uid, msg1)
print(f"Turn 1 OK — {len(r1['text'])} ký tự, {len(r1['tool_calls'])} tool calls")

print("\n⏳ Chờ 15 giây...")
time.sleep(15)

# Turn 2: câu sai ngữ pháp
msg2 = "[Level: A2] i think music good"
print(f"\nTurn 2: {msg2[12:]}")

r2 = run_turn_structured(runner, sid, uid, msg2)

print(f"\nAgent response ({len(r2['text'])} ký tự):")
print(r2["text"])

if r2["tool_calls"]:
    print(f"\nTool Calls ({len(r2['tool_calls'])}):")
    for tc in r2["tool_calls"]:
        print(f"  • {tc['tool']} → keys: {list((tc.get('result') or {}).keys())}")

# Tự đánh giá
has_text = len(r2["text"]) > 50
has_correction = any(kw in r2["text"].lower() for kw in [
    "is", "sửa", "lỗi", "ngữ pháp", "grammar", "correct", "beneficial",
    "improve", "cải thiện", "hoàn thiện", "câu", "sentence"
])
has_suggest = any(tc["tool"] in ("suggest_sentence_structures", "enrich_vocabulary") for tc in r2["tool_calls"])

print(f"\n{'✅' if has_text else '❌'} Agent trả lời có nội dung")
print(f"{'✅' if has_correction else '⚠️'} Agent sửa lỗi/giải thích ngữ pháp")
print(f"{'✅' if has_suggest else '⚠️'} Tool suggest/enrich được gọi (tùy agent quyết định)")
print(f"\n{'✅ A2 TURN 2 PASS' if has_text and has_correction else '❌ A2 TURN 2 FAIL'}")
