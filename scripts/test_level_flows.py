"""
test_level_flows.py
===================
Simulates B1 and A2 level workflows using MOCK_GEMINI=1 and logs outputs.
Helps verify prompt logic and mock integration without calling the real API.

Run with:
    MOCK_GEMINI=1 python3 test_level_flows.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Enable mock mode
os.environ["MOCK_GEMINI"] = "1"

from app import run_turn_structured, create_runner


def run_session_simulation(level: str, turns: list[str]) -> None:
    print("\n" + "=" * 80)
    print(f"SIMULATION: LEVEL {level} FLOW")
    print("=" * 80)

    runner = create_runner()
    session_id = f"sim_{level.lower()}"
    user_id = "test_user"

    for i, user_msg in enumerate(turns, 1):
        print(f"\n[Turn {i}] User: {user_msg}")

        # Mimic app.py level prefixing
        prefixed_msg = f"[Level: {level}] {user_msg}"

        # Get response
        result = run_turn_structured(runner, session_id, user_id, prefixed_msg)

        # Print agent response
        print(f"[Turn {i}] Agent response:")
        print(result["text"])

        # Print tool calls
        if result["tool_calls"]:
            print(f"--- [Turn {i}] Tool Calls ({len(result['tool_calls'])}):")
            for tc in result["tool_calls"]:
                tool_name = tc.get("tool")
                args = tc.get("args", {})
                res = tc.get("result", {})
                print(f"  • {tool_name}(...) -> result keys: {list(res.keys()) if res else 'None'}")
        else:
            print(f"--- [Turn {i}] No tool calls triggered.")


def main():
    # ── 1. B1 Simulation ──────────────────────────────────────────────────────
    b1_turns = [
        # Turn 1: Essay prompt
        "Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?",
        # Turn 2: User chooses paraphrase 1
        "Tôi chọn cách 1. Bắt đầu hướng dẫn mở bài.",
        # Turn 3: User writes intro draft
        "It is widely believed that music brings people of all ages and backgrounds together. I fully support this view because music is a universal language."
    ]
    run_session_simulation("B1", b1_turns)

    # ── 2. A2 Simulation ──────────────────────────────────────────────────────
    a2_turns = [
        # Turn 1: Essay prompt
        "Some people say that music is a good way of bringing people of different cultures and ages together. To what extent do you agree or disagree with this opinion?",
        # Turn 2: Stuck / Brainstorming
        "Tôi chưa nghĩ ra ý gì cả, tôi phải viết thế nào?",
        # Turn 3: User attempts a short sentence with grammatical error
        "i think music good"
    ]
    run_session_simulation("A2", a2_turns)

    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
