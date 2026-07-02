"""
Essay Writing Coach — ADK Agent
=================================
Agent: IELTS Writing Task 2 Coach
Framework: Google ADK v2.3.0
Model: Gemini 2.5 Flash

Entry point:
    python3 agent.py                # runs built-in demo flow
    adk web Capstone/               # opens ADK dev UI (optional)

Session: InMemoryRunner (no persistence, sufficient for capstone demo)
Tools: imported from tools.py (5 tools, no modification)
"""

import asyncio
import os
import sys
import time

# Ensure the Capstone directory is on the path so `import tools` works
sys.path.insert(0, os.path.dirname(__file__))

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
from google.genai.types import GenerateContentConfig, ThinkingConfig

from tools import TOOLS  # the 5 implemented tool functions


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an IELTS Writing Task 2 coach helping Vietnamese learners at level A2-B1.
Your role is to guide users through writing a complete essay, step by step.
All explanations and feedback to the user MUST be in Vietnamese.
English is used ONLY for example sentences, templates, and essay content.

## MANDATORY WORKFLOW — follow this exact sequence every session

### Step 1 — Classify and paraphrase (when user gives an essay prompt)
1. Call `classify_essay_type` with the full prompt text.
2. Tell the user in Vietnamese which essay type was detected and why (use the `explanation` field).
3. Immediately call `paraphrase_prompt` with the same prompt and the user's level (A2 or B1; default B1 if unknown).
4. Present all 3 paraphrase options to the user in Vietnamese (show `text` + `technique` for each).
5. Ask the user which paraphrase they want to use, or offer to proceed with the first one.

### Step 2 — Guide introduction
1. Call `guide_essay_section` with:
   - section = "introduction"
   - essay_type = the type from Step 1
   - context = { "prompt": <original prompt>, "paraphrase": <chosen paraphrase>,
                 "thesis": <user's stated opinion if any>, "level": <user's level> }
2. Present to the user in Vietnamese:
   - `instructions` (numbered steps)
   - `template` (show as a fill-in-the-blank frame)
   - `example` (show as an example introduction)
   - `useful_phrases` (bullet list)
   - `common_errors` (warn the user clearly)
   - `checklist` (ask the user to self-check before continuing)
3. Ask the user to write their introduction draft.

### Step 3 — Guide body paragraphs and conclusion
After the user submits a draft or asks to move on:
1. Check the `next_section` field from the last `guide_essay_section` call.
2. Call `guide_essay_section` with the next section name and updated context
   (include user's draft in `user_draft` so feedback is personalised).
3. Present the same structured guidance as in Step 2.
4. Repeat until section = "conclusion" is complete.

### Step 4 — Sentence and vocabulary help (can occur at any time)
- If the user writes a sentence that repeats the same structure (S+V+O 2+ times in a row),
  or the user asks "how to make this sentence better":
  → Call `suggest_sentence_structures` with their sentence and their level.
  → Show each `variation` with its `pattern` and explain in Vietnamese.
- If the user repeats the same word multiple times, or asks for synonyms / vocabulary help:
  → Call `enrich_vocabulary` with their text (and `topic` if the essay topic is known).
  → Show `overused_words`, each entry in `suggestions`, any `topic_words`, and `collocations`.
  → Show `improved_text` as a before/after comparison.

## STRICT RULES

1. ALL user-facing explanations must be in Vietnamese. Never switch to English for explanations.
2. NEVER invent guidance — base every response strictly on what the tools return.
3. If any tool returns {"error": ...}:
   - Tell the user in Vietnamese that a technical error occurred.
   - Display the error message exactly.
   - Ask the user to try again or rephrase their input.
   - Do NOT fabricate alternative content.
4. Ask for the user's level (A2 or B1) early if not provided; default to B1.
5. Guide one section at a time — do not skip ahead or summarise future sections.
6. Use only the 5 provided tools. Do not attempt to use any other tools or external resources.
7. Keep your responses structured and easy to read:
   use numbered steps, bullet points, and clear Vietnamese headers (e.g. "📌 Hướng dẫn:", "✏️ Mẫu câu:", "⚠️ Lỗi thường gặp:").

## SCOPE GUARD — từ chối lịch sự khi yêu cầu ngoài phạm vi

Bạn CHỈ hỗ trợ IELTS Writing Task 2 bằng tiếng Anh thông qua 5 công cụ đã định nghĩa.
Nếu người dùng yêu cầu việc NGOÀI phạm vi này (ví dụ: dịch bài sang ngôn ngữ khác,
viết thay hộ essay, hỏi về Task 1, hỏi về Speaking/Listening/Reading, hoặc bất kỳ
chủ đề không liên quan đến IELTS Writing Task 2), hãy:
- Từ chối lịch sự bằng tiếng Việt
- Giải thích ngắn gọn phạm vi hỗ trợ của bạn
- Mời người dùng quay lại đúng luồng (ví dụ: "Bạn có muốn tiếp tục với bài essay không?")
- KHÔNG gọi bất kỳ tool nào, KHÔNG tự ý thực hiện yêu cầu ngoài phạm vi
"""


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="essay_writing_coach",
    model="gemini-2.5-flash-lite",
    instruction=SYSTEM_PROMPT,
    tools=TOOLS,
    description=(
        "IELTS Writing Task 2 coach for Vietnamese learners at A2-B1 level. "
        "Guides users through classify → paraphrase → introduction → body → conclusion."
    ),
    # thinking_budget=0: safeguard against thinking-only responses that cause
    # ADK to raise "model output must contain either output text or tool calls".
    generate_content_config=GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_budget=0),
    ),
)


# ---------------------------------------------------------------------------
# Runner helpers
# ---------------------------------------------------------------------------

def create_runner() -> InMemoryRunner:
    """Create a fresh InMemoryRunner for the agent."""
    return InMemoryRunner(agent=root_agent, app_name="essay_writing_coach")


async def ensure_session(runner: InMemoryRunner, user_id: str, session_id: str) -> None:
    """Ensure a session exists in the runner's session service.

    create_session is async in ADK v2.3.0 — must be awaited.
    Calls create_session idempotently (ignores AlreadyExists-style errors).

    Args:
        runner:     The InMemoryRunner instance.
        user_id:    User identifier.
        session_id: Session identifier.
    """
    try:
        await runner.session_service.create_session(
            app_name="essay_writing_coach",
            user_id=user_id,
            session_id=session_id,
        )
    except Exception:
        # Session already exists — safe to ignore
        pass


async def run_turn(
    runner: InMemoryRunner,
    session_id: str,
    user_id: str,
    message: str,
) -> str:
    """Send one user message and collect the full agent response text.

    Calls ensure_session() before the first turn so the session exists.
    Reuse the same runner and session_id across multiple turns to maintain
    conversation history.

    Args:
        runner:     The InMemoryRunner instance (reuse across turns).
        session_id: Stable string ID for this conversation thread.
        user_id:    Stable string ID for the user.
        message:    The user's message text.

    Returns:
        The agent's complete response as a single string.
    """
    # Ensure session exists (idempotent — safe to call every turn)
    await ensure_session(runner, user_id, session_id)

    msg = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )
    chunks: list[str] = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=msg,
    ):
        if event.content and event.content.parts:
            chunks.extend(
                p.text for p in event.content.parts if hasattr(p, "text") and p.text
            )
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Demo / test script
# ---------------------------------------------------------------------------

# Delay (seconds) between turns to stay under the 5 RPM free-tier limit.
_TURN_DELAY_S = 15
# Retry delay (seconds) when a 429 is hit despite the sleep.
_RETRY_DELAY_S = 20


def _sleep_with_message(seconds: int) -> None:
    """Sleep for `seconds` while printing a visible countdown message."""
    print(f"⏳ Đang chờ {seconds}s để tránh rate limit...", flush=True)
    time.sleep(seconds)


async def _run_turn_with_retry(
    runner: InMemoryRunner,
    session_id: str,
    user_id: str,
    message: str,
) -> str:
    """Wrap run_turn with one automatic retry on 429 ResourceExhausted.

    If the first attempt hits a 429, waits _RETRY_DELAY_S seconds then
    tries once more before re-raising.
    """
    try:
        return await run_turn(runner, session_id, user_id, message)
    except Exception as exc:
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            print(f"⚠️  Rate limit hit — thử lại sau {_RETRY_DELAY_S}s...", flush=True)
            _sleep_with_message(_RETRY_DELAY_S)
            return await run_turn(runner, session_id, user_id, message)
        raise


async def _demo() -> None:
    """Run a 3-turn demo flow using the Cam14-T3 Opinion test case.

    Sleeps _TURN_DELAY_S seconds between turns to stay safely under the
    5 RPM free-tier quota for gemini-2.5-flash.
    """
    print("=" * 70)
    print("IELTS Writing Coach — Demo Flow (Cam14-T3 Opinion)")
    print("=" * 70)

    # ── Setup ──────────────────────────────────────────────────────────────
    runner     = create_runner()
    user_id    = "demo_user"
    session_id = "demo_session_001"
    turn_count = 0
    errors: list[str] = []

    # ── Turn 1: provide essay prompt ───────────────────────────────────────
    ESSAY_PROMPT = (
        "Some people say that music is a good way of bringing people of "
        "different cultures and ages together. "
        "To what extent do you agree or disagree with this opinion?"
    )
    print(f"\n[TURN 1] User:\n{ESSAY_PROMPT}\n")
    print("-" * 70)

    try:
        response1 = await _run_turn_with_retry(runner, session_id, user_id, ESSAY_PROMPT)
        turn_count += 1
        print(f"[Agent response — turn {turn_count}]")
        print(response1 or "(no text output)")
    except Exception as exc:
        errors.append(f"Turn 1 error: {exc}")
        print(f"❌ Turn 1 failed: {exc}")

    # ── Turn 2: ask to write introduction ─────────────────────────────────
    _sleep_with_message(_TURN_DELAY_S)
    print(f"\n[TURN 2] User:\nTôi muốn viết phần introduction. Level của tôi là B1.\n")
    print("-" * 70)

    try:
        response2 = await _run_turn_with_retry(
            runner, session_id, user_id,
            "Tôi muốn viết phần introduction. Level của tôi là B1."
        )
        turn_count += 1
        print(f"[Agent response — turn {turn_count}]")
        print(response2 or "(no text output)")
    except Exception as exc:
        errors.append(f"Turn 2 error: {exc}")
        print(f"❌ Turn 2 failed: {exc}")

    # ── Turn 3: submit a simple draft and ask for sentence improvement ──────
    _sleep_with_message(_TURN_DELAY_S)
    DRAFT = "Music is good. It helps people. People like music everywhere."
    print(f"\n[TURN 3] User:\n{DRAFT}\nCó thể giúp tôi cải thiện câu này không?\n")
    print("-" * 70)

    try:
        response3 = await _run_turn_with_retry(
            runner, session_id, user_id,
            f"{DRAFT}\nCó thể giúp tôi cải thiện câu này không?"
        )
        turn_count += 1
        print(f"[Agent response — turn {turn_count}]")
        print(response3 or "(no text output)")
    except Exception as exc:
        errors.append(f"Turn 3 error: {exc}")
        print(f"❌ Turn 3 failed: {exc}")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"Demo complete — total turns: {turn_count}/3")
    if errors:
        print(f"Errors encountered ({len(errors)}):")
        for err in errors:
            print(f"  ❌ {err}")
    else:
        print("✅ All turns completed without errors.")
    print("=" * 70)


if __name__ == "__main__":
    # Make sure GEMINI_API_KEY is loaded from env.
    # ADK also reads GOOGLE_API_KEY — forward it here so both tools.py and ADK find it.
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print(
            "⚠️  GEMINI_API_KEY not found in environment.\n"
            "Run: source ~/.zshrc  (or export GEMINI_API_KEY=...)\n"
            "then re-run this script."
        )
        sys.exit(1)

    # ADK uses GOOGLE_API_KEY internally — forward the value
    os.environ.setdefault("GOOGLE_API_KEY", api_key)

    asyncio.run(_demo())
