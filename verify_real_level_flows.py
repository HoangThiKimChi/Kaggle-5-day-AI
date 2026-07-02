"""
verify_real_level_flows.py
==========================
Chạy thử nghiệm E2E (4 turns, 6 API requests thật)
Patch động để chạy bằng model 'gemini-2.5-flash' nhằm tránh lỗi 503 của flash-lite.
Giữ nguyên file agent.py và tools.py gốc dùng flash-lite.

Chạy:
    source ~/.zshrc && python3 verify_real_level_flows.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

# Tắt mock mode
os.environ["MOCK_GEMINI"] = "0"

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    print("⚠️  GEMINI_API_KEY không tìm thấy. Không thể test thật. Đang thoát...")
    sys.exit(1)
os.environ.setdefault("GOOGLE_API_KEY", API_KEY)

# ── PATCH ĐỘNG MODEL SANG GEMINI-2.5-FLASH ────────────────────────────────────
import agent
import tools

# Patch agent model
print("🔧 Patching agent model sang gemini-2.5-flash...")
agent.root_agent.model = "gemini-2.5-flash"

# Patch tools _call_gemini function to use gemini-2.5-flash instead of flash-lite
orig_call_gemini = tools._call_gemini

def patched_call_gemini(user_prompt: str, system_instruction: str = "") -> str:
    # We copy the exact same logic of _call_gemini but force model="gemini-2.5-flash"
    import json
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return ""
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_instruction}\n\n{user_prompt}" if system_instruction else user_prompt
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Forced to stable full model
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        if response.text:
            return response.text
        if response.candidates:
            cand = response.candidates[0]
            if cand.content and cand.content.parts:
                texts = [
                    p.text
                    for p in cand.content.parts
                    if p.text and not getattr(p, "thought", False)
                ]
                if texts:
                    return "".join(texts)
        return ""
    except Exception as exc:
        return json.dumps({"_api_error": type(exc).__name__, "_api_message": str(exc)[:300]})

tools._call_gemini = patched_call_gemini
print("🔧 Patching tools.py model call sang gemini-2.5-flash...")

# ─────────────────────────────────────────────────────────────────────────────
from app import run_turn_structured, create_runner

def run_turn_with_delay(runner, session_id, user_id, prefixed_msg):
    print("⏳ Đang gửi request tới Gemini...")
    result = run_turn_structured(runner, session_id, user_id, prefixed_msg)
    return result

def run_session_simulation(level: str, turns: list[str]) -> None:
    print("\n" + "=" * 80)
    print(f"VERIFY REAL API: LEVEL {level} FLOW (Using gemini-2.5-flash)")
    print("=" * 80)

    runner = create_runner()
    session_id = f"real_sim_{level.lower()}_{int(time.time())}"
    user_id = "real_user"

    for i, user_msg in enumerate(turns, 1):
        print(f"\n[Turn {i}] User: {user_msg}")
        prefixed_msg = f"[Level: {level}] {user_msg}"

        result = run_turn_with_delay(runner, session_id, user_id, prefixed_msg)

        print(f"[Turn {i}] Agent response:")
        print(result["text"])

        if result["tool_calls"]:
            print(f"--- [Turn {i}] Tool Calls ({len(result['tool_calls'])}):")
            for tc in result["tool_calls"]:
                tool_name = tc.get("tool")
                args = tc.get("args", {})
                res = tc.get("result", {})
                print(f"  • {tool_name}({args})")
                if isinstance(res, dict):
                    print(f"    -> Result keys: {list(res.keys())}")
                else:
                    print(f"    -> Result: {str(res)[:150]}...")
        else:
            print(f"--- [Turn {i}] No tool calls triggered.")

        # Nghỉ 15 giây giữa các lượt để an toàn
        print("⏳ Chờ 15 giây để tránh rate limit...")
        time.sleep(15)

def main():
    # ── 1. B1 Simulation ──────────────────────────────────────────────────────
    b1_turns = [
        "Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?",
        "Tôi chọn cách 1. Hãy hướng dẫn tôi viết Introduction."
    ]
    run_session_simulation("B1", b1_turns)

    # Chờ 20 giây chuyển giao giữa 2 phiên
    print("\n⏳ Chờ 20 giây trước khi chuyển sang phiên test A2...")
    time.sleep(20)

    # ── 2. A2 Simulation ──────────────────────────────────────────────────────
    a2_turns = [
        "Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?",
        "i think music good"
    ]
    run_session_simulation("A2", a2_turns)

    print("\n" + "=" * 80)
    print("REAL VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
