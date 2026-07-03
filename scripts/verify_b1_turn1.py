"""
verify_b1_turn1.py — Verify B1 Flow, Turn 1 (1 request)
Gửi đề bài Opinion → xác nhận agent gọi classify + paraphrase

Chạy: source ~/.zshrc && python3 verify_b1_turn1.py
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
sid = f"b1_t1_{int(time.time())}"
uid = "verify_user"

msg = "[Level: B1] Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?"

print("=" * 60)
print("VERIFY B1 — Turn 1: Gửi đề bài Opinion")
print("=" * 60)
print(f"User: {msg[12:]}")  # bỏ prefix [Level: B1]

result = run_turn_structured(runner, sid, uid, msg)

print(f"\nAgent response ({len(result['text'])} ký tự):")
print(result["text"])

if result["tool_calls"]:
    print(f"\nTool Calls ({len(result['tool_calls'])}):")
    for tc in result["tool_calls"]:
        print(f"  • {tc['tool']} → keys: {list((tc.get('result') or {}).keys())}")

# Tự đánh giá
has_classify = any(tc["tool"] == "classify_essay_type" for tc in result["tool_calls"])
has_paraphrase = any(tc["tool"] == "paraphrase_prompt" for tc in result["tool_calls"])
has_text = len(result["text"]) > 50

print(f"\n{'✅' if has_classify else '❌'} classify_essay_type được gọi")
print(f"{'✅' if has_paraphrase else '❌'} paraphrase_prompt được gọi")
print(f"{'✅' if has_text else '❌'} Agent trả lời có nội dung ({len(result['text'])} ký tự)")
print(f"\n{'✅ B1 TURN 1 PASS' if all([has_classify, has_paraphrase, has_text]) else '❌ B1 TURN 1 FAIL'}")
