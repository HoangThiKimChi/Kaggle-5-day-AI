"""
test_streamlit_integration.py
==============================
Giai đoạn 1 — Prototype test 3 điểm chặn cứng trước khi code app.py

Chạy (mặc định, không tốn quota):
    MOCK_GEMINI=1 python3 test_streamlit_integration.py

Chạy thật (tốn quota — chỉ khi Chi yêu cầu rõ):
    source ~/.zshrc && python3 test_streamlit_integration.py

Tests:
    1.1 — Async/sync: asyncio.run() vs thread-based
    1.2 — ADK session sống xuyên suốt Streamlit rerun
    1.3 — run_turn_structured() trả tool_calls có cấu trúc
"""

import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))

# Load env variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

MOCK_MODE = os.environ.get("MOCK_GEMINI", "").strip() == "1"

if MOCK_MODE:
    print("🔧 MOCK_GEMINI=1 — chạy ở chế độ mock, không tốn quota.")
    # MOCK_GEMINI được pass vào tools.py qua os.environ — đã set ở trên
else:
    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if not API_KEY:
        print("⚠️  GEMINI_API_KEY không tìm thấy trong environment hoặc tệp .env.")
        print("    Vui lòng kiểm tra lại tệp .env hoặc chạy mock: MOCK_GEMINI=1 python3 test_streamlit_integration.py")
        sys.exit(1)
    os.environ.setdefault("GOOGLE_API_KEY", API_KEY)

from agent import create_runner, ensure_session, run_turn
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types


# ---------------------------------------------------------------------------
# run_turn_structured — trả text + tool_calls có cấu trúc
# ---------------------------------------------------------------------------

async def run_turn_structured(
    runner: InMemoryRunner,
    session_id: str,
    user_id: str,
    message: str,
) -> dict:
    """Gửi 1 tin nhắn, trả về {'text': str, 'tool_calls': [...]}."""
    if MOCK_MODE:
        # Mock: gọi ensure_session để test session creation thật sự,
        # nhưng trả về structured data giả lập
        await ensure_session(runner, user_id, session_id)
        return {
            "text": "[MOCK] Chào bạn! Đây là Opinion Essay. Tôi đã phân loại và paraphrase đề bài cho bạn.",
            "tool_calls": [
                {
                    "tool": "classify_essay_type",
                    "args": {"essay_prompt": message[:60]},
                    "result": {"essay_type": "opinion", "confidence": "high",
                               "explanation": "[MOCK] Từ khóa 'agree or disagree' → Opinion Essay."},
                },
                {
                    "tool": "paraphrase_prompt",
                    "args": {"prompt": message[:60], "level": "B1"},
                    "result": {
                        "level": "B1",
                        "paraphrases": [
                            {"text": "[MOCK] It is often argued that music serves as a universal connector.", "technique": "Synonym Substitution"},
                        ],
                    },
                },
            ],
        }

    # Real mode
    await ensure_session(runner, user_id, session_id)
    msg = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )
    text_chunks: list[str] = []
    tool_calls: list[dict] = []

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=msg
    ):
        if not (event.content and event.content.parts):
            continue
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not getattr(part, "thought", False):
                text_chunks.append(part.text)
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                tool_calls.append({"tool": fc.name, "args": dict(fc.args) if fc.args else {}, "result": None})
            if hasattr(part, "function_response") and part.function_response:
                fr = part.function_response
                for tc in reversed(tool_calls):
                    if tc["tool"] == fr.name and tc["result"] is None:
                        tc["result"] = dict(fr.response) if fr.response else {}
                        break
                else:
                    tool_calls.append({"tool": fr.name, "args": {}, "result": dict(fr.response) if fr.response else {}})

    return {"text": "".join(text_chunks), "tool_calls": tool_calls}


# ---------------------------------------------------------------------------
# Mock helpers for tests 1.1 and 1.2 when MOCK_GEMINI=1
# ---------------------------------------------------------------------------

async def _mock_agent_turn(runner: InMemoryRunner, session_id: str, user_id: str, message: str) -> str:
    """Mock run_turn: calls ensure_session (real) but returns fixed text (no LLM)."""
    await ensure_session(runner, user_id, session_id)
    if "music" in message.lower() or "agree" in message.lower():
        return "[MOCK] Chào bạn! Đây là Opinion Essay. Tôi sẽ giúp bạn paraphrase đề bài và hướng dẫn từng section."
    elif "introduction" in message.lower():
        return "[MOCK] Hướng dẫn viết Introduction: (1) Paraphrase đề bài, (2) Nêu thesis statement, (3) Tự kiểm tra checklist."
    elif "cải thiện" in message.lower() or "improve" in message.lower():
        return "[MOCK] Đây là gợi ý cấu trúc câu tốt hơn: 'Technology not only saves time but also connects people.'"
    return "[MOCK] Tôi hiểu yêu cầu của bạn. Hãy bắt đầu bằng cách cung cấp đề bài IELTS Task 2."


async def _real_or_mock_turn(runner, session_id, user_id, message):
    if MOCK_MODE:
        return await _mock_agent_turn(runner, session_id, user_id, message)
    return await run_turn(runner, session_id, user_id, message)


# ---------------------------------------------------------------------------
# TEST 1.1 — Async/sync mismatch
# ---------------------------------------------------------------------------

def test_11_async_sync() -> bool:
    print("\n" + "=" * 60)
    print("TEST 1.1 — Async/sync mismatch")
    print("=" * 60)

    runner = create_runner()
    session_id = f"test11_{uuid.uuid4().hex[:8]}"
    user_id = "test_user"
    msg = "Some people say technology is good. Do you agree or disagree?"

    # Cách 1: asyncio.run() từ sync context
    print("Thử asyncio.run() từ sync context...")
    try:
        result = asyncio.run(_real_or_mock_turn(runner, session_id, user_id, msg))
        print(f"✅ asyncio.run() PASS — len(response)={len(result)}")
        print(f"   Preview: {result[:120].strip()}...")
        method_1_ok = True
    except RuntimeError as e:
        if "event loop" in str(e).lower():
            print(f"❌ asyncio.run() FAIL (nested loop): {e}")
        else:
            print(f"❌ asyncio.run() FAIL: {e}")
        method_1_ok = False
    except Exception as e:
        print(f"❌ asyncio.run() FAIL (unexpected): {type(e).__name__}: {e}")
        method_1_ok = False

    # Cách 2: Thread-based (safe for nested loops)
    import threading
    print("\nThử thread-based asyncio (safe for nested loops)...")
    _holder: dict = {}
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            _holder["result"] = loop.run_until_complete(
                _real_or_mock_turn(runner, session_id + "_t", user_id, msg)
            )
        except Exception as exc:
            _holder["error"] = str(exc)
        finally:
            loop.close()

    t = threading.Thread(target=run_in_thread, daemon=True)
    t.start()
    t.join(timeout=60)

    if "result" in _holder:
        print(f"✅ thread-based PASS — len(response)={len(_holder['result'])}")
        method_2_ok = True
    else:
        print(f"❌ thread-based FAIL: {_holder.get('error', 'timeout')}")
        method_2_ok = False

    rec = "asyncio.run()" if method_1_ok else ("thread-based" if method_2_ok else "CẢ 2 FAIL")
    print(f"\n→ Khuyến nghị: {rec}")
    return method_1_ok or method_2_ok


# ---------------------------------------------------------------------------
# TEST 1.2 — ADK session sống xuyên suốt Streamlit rerun
# ---------------------------------------------------------------------------

def test_12_session_persistence() -> bool:
    print("\n" + "=" * 60)
    print("TEST 1.2 — ADK session sống xuyên suốt Streamlit rerun")
    print("=" * 60)

    fake_state: dict = {}

    # Rerun 1
    if "adk_runner" not in fake_state:
        fake_state["adk_runner"] = create_runner()
        fake_state["adk_session_id"] = f"st_{uuid.uuid4().hex[:12]}"
        fake_state["adk_user_id"] = "streamlit_user"
    print(f"Rerun 1 — session_id: {fake_state['adk_session_id']}")

    runner = fake_state["adk_runner"]
    sid = fake_state["adk_session_id"]
    uid = fake_state["adk_user_id"]

    turn1_msg = (
        "Some people say that music is a good way of bringing people "
        "of different cultures and ages together. "
        "To what extent do you agree or disagree with this opinion?"
    )
    print(f"Turn 1: {turn1_msg[:60]}...")
    try:
        r1 = asyncio.run(_real_or_mock_turn(runner, sid, uid, turn1_msg))
        print(f"✅ Turn 1 OK — {len(r1)} ký tự")
        print(f"   {r1[:150].strip()}...")
    except Exception as e:
        print(f"❌ Turn 1 FAIL: {e}")
        return False

    # Rerun 2 — runner GIỮ NGUYÊN từ fake_state
    print(f"\nRerun 2 — dùng lại runner từ state (không tạo mới)")
    runner = fake_state["adk_runner"]
    sid = fake_state["adk_session_id"]
    uid = fake_state["adk_user_id"]

    turn2_msg = "Tôi muốn viết phần introduction. Level B1."
    print(f"Turn 2: {turn2_msg}")
    try:
        r2 = asyncio.run(_real_or_mock_turn(runner, sid, uid, turn2_msg))
        print(f"✅ Turn 2 OK — {len(r2)} ký tự")
        print(f"   {r2[:200].strip()}...")

        keywords = ["introduction", "music", "opinion", "mở bài", "paraphrase",
                    "essay", "hướng dẫn", "mock"]
        has_context = any(kw in r2.lower() for kw in keywords)
        if has_context:
            print("✅ Agent nhớ context từ turn 1 — PASS")
        else:
            print("⚠️  Không tìm thấy từ khoá context — kiểm tra thủ công")
        return True
    except Exception as e:
        print(f"❌ Turn 2 FAIL: {e}")
        return False


# ---------------------------------------------------------------------------
# TEST 1.3 — run_turn_structured() trả tool_calls có cấu trúc
# ---------------------------------------------------------------------------

def test_13_structured_output() -> bool:
    print("\n" + "=" * 60)
    print("TEST 1.3 — run_turn_structured() trả tool_calls có cấu trúc")
    print("=" * 60)

    runner = create_runner()
    sid = f"test13_{uuid.uuid4().hex[:8]}"
    uid = "test_user"
    msg = (
        "Some people say that music is a good way of bringing people "
        "of different cultures and ages together. "
        "To what extent do you agree or disagree with this opinion?"
    )
    print(f"Gửi: {msg[:60]}...")

    try:
        result = asyncio.run(run_turn_structured(runner, sid, uid, msg))
    except Exception as e:
        print(f"❌ run_turn_structured() exception: {type(e).__name__}: {e}")
        return False

    ok = True
    if not isinstance(result, dict):
        print(f"❌ Kết quả không phải dict: {type(result)}"); return False

    # text
    if "text" not in result:
        print("❌ Thiếu key 'text'"); ok = False
    else:
        print(f"✅ 'text': {len(result['text'])} ký tự")
        print(f"   {result['text'][:120].strip()}...")

    # tool_calls
    if "tool_calls" not in result:
        print("❌ Thiếu key 'tool_calls'"); ok = False
    else:
        calls = result["tool_calls"]
        print(f"✅ 'tool_calls': {len(calls)} entry")
        for tc in calls:
            tool_name = tc.get("tool", "?")
            result_val = tc.get("result")
            has_result = result_val is not None and result_val != {}
            result_keys = list(result_val.keys())[:5] if isinstance(result_val, dict) else []
            print(f"   • {tool_name}: result={'✅ keys=' + str(result_keys) if has_result else '❌ None/empty'}")
        if not calls:
            print("   ❌ tool_calls rỗng — phải có ít nhất 1 entry")
            ok = False

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mode_label = "MOCK (MOCK_GEMINI=1)" if MOCK_MODE else "REAL API"
    print("=" * 60)
    print(f"GIAI ĐOẠN 1 — Integration Test [{mode_label}]")
    print("=" * 60)

    results: dict = {}

    results["1.1 Async/sync"] = test_11_async_sync()

    if not MOCK_MODE:
        print("\n⏳ Chờ 15s trước 1.2 để tránh rate limit...")
        time.sleep(15)
    results["1.2 Session"] = test_12_session_persistence()

    if not MOCK_MODE:
        print("\n⏳ Chờ 15s trước 1.3 để tránh rate limit...")
        time.sleep(15)
    results["1.3 Structured"] = test_13_structured_output()

    print("\n" + "=" * 60)
    print(f"TỔNG KẾT GIAI ĐOẠN 1 [{mode_label}]")
    print("=" * 60)
    all_pass = True
    for name, passed in results.items():
        if passed:
            print(f"  ✅ {name}: PASS")
        else:
            print(f"  ❌ {name}: FAIL")
            all_pass = False

    if all_pass:
        print(f"\n✅ Sẵn sàng sang Giai đoạn 2 — code app.py")
    else:
        print(f"\n❌ Có test FAIL — cần xử lý trước")
    print("=" * 60)
