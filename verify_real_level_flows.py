"""
verify_real_level_flows.py
==========================
Chạy thử nghiệm E2E thật (4 turns, 6 API requests thật)
Sử dụng chính thức model 'gemini-2.5-flash-lite' từ agent.py và tools.py.

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

from app import run_turn_structured, create_runner

def run_turn_with_delay(runner, session_id, user_id, prefixed_msg):
    print("⏳ Đang gửi request tới Gemini (gemini-2.5-flash-lite)...")
    result = run_turn_structured(runner, session_id, user_id, prefixed_msg)
    return result

def run_session_simulation(level: str, turns: list[str]) -> None:
    print("\n" + "=" * 80)
    print(f"VERIFY REAL API: LEVEL {level} FLOW (gemini-2.5-flash-lite)")
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
