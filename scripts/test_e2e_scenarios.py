import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

# Turn off mock mode to hit real API
os.environ["MOCK_GEMINI"] = "0"

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    print("⚠️  GEMINI_API_KEY not found in env.")
    sys.exit(1)
os.environ.setdefault("GOOGLE_API_KEY", API_KEY)
os.environ["GEMINI_API_KEY"] = API_KEY

from agent import create_runner
from server import _run_turn_structured_real
import asyncio

async def run_turn_with_delay(session_id, user_id, message):
    print(f"\n⏳ Sending request to Gemini...")
    result = await _run_turn_structured_real(session_id, user_id, message, [])
    return result

async def run_scenarios():
    print("=" * 80)
    print("E2E VERIFICATION: B1 REVISED SCENARIOS (7 STEPS)")
    print("=" * 80)

    session_id = f"e2e_sim_b1_{int(time.time())}"
    user_id = "e2e_test_user"

    turns = [
        # Step 1: Classify
        "[Level: B1] Some people think that the best way to reduce crime is to give longer prison sentences. Others, however, believe there are better alternative ways of reducing crime. Discuss both views and give your own opinion.",
        
        # Step 2a: Copy prompt exactly
        "[Level: B1] Some people think that the best way to reduce crime is to give longer prison sentences. Others, however, believe there are better alternative ways of reducing crime.",
        
        # Step 2b: Grammar/Spelling errors
        "[Level: B1] In nowsaday, crime is become more and more serous in the world. Some peoples think that long prision sentences is the good way to reducing crime but other believe diferent way is more better.",
        
        # Step 2c: Off-topic
        "[Level: B1] Education is very important for children in modern society. Schools should focus more on teaching practical skills rather than academic subjects.",
        
        # Step 2d: Incomplete
        "[Level: B1] In today's society, crime has become a major concern for many countries around the world.",
        
        # Step 2e: Complete Intro
        "[Level: B1] In today's society, the issue of crime and punishment has become a topic of great concern. While some argue that imposing longer prison sentences is the most effective way to reduce crime, others contend that alternative approaches may yield better results. This essay will discuss both perspectives before presenting my own viewpoint.",
        
        # Step 3: Brainstorm
        "[Level: B1] Em cần brainstorm ý cho body 1 và body 2",
        
        # Step 4: Body 1
        "[Level: B1] On the one hand, supporters of longer prison sentences argue that harsh penalties act as a strong deterrent. When potential criminals are aware that committing a crime could result in many years behind bars, they may think twice before breaking the law. For example, in countries like Singapore, strict punishments have contributed to remarkably low crime rates.",
        
        # Step 5: Body 2
        "[Level: B1] On the other hand, many experts believe that addressing the root causes of crime is more effective than simply locking people up. Investing in education programs and community support can help prevent individuals from turning to crime in the first place. Additionally, rehabilitation programs within the justice system can reduce reoffending rates significantly.",
        
        # Step 6: Conclusion
        "[Level: B1] In conclusion, while longer prison sentences may serve as a deterrent in some cases, I believe that a combination of preventive measures and rehabilitation programs would be more effective in reducing crime in the long term.",

        # Step 7: Scoring
        "[Level: B1] Chấm điểm bài viết của em"
    ]

    for i, user_msg in enumerate(turns, 1):
        clean_msg = user_msg.replace("[Level: B1] ", "")
        print(f"\n[Turn {i}] User: {clean_msg}")
        
        result = await run_turn_with_delay(session_id, user_id, user_msg)

        print(f"[Turn {i}] Agent response:")
        print(result["text"])

        if result["tool_calls"]:
            print(f"--- [Turn {i}] Tool Calls ({len(result['tool_calls'])}):")
            for tc in result["tool_calls"]:
                tool_name = tc.get("tool")
                args = tc.get("args", {})
                res = tc.get("result", {})
                print(f"  • {tool_name}(...)")
                if isinstance(res, dict) and "error" in res:
                    print(f"    -> ERROR: {res['error']}")
        else:
            print(f"--- [Turn {i}] No tool calls triggered.")

        print("⏳ Waiting 15 seconds to avoid rate limits...")
        await asyncio.sleep(15)
        
    print("\n" + "=" * 80)
    print("E2E VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_scenarios())
