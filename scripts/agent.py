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

# Load env variables from .env file manually to force override any stale OS shell credentials
try:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
except Exception:
    pass

# Clean Vertex AI conflict and force-forward the key
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
# GenerateContentConfig/ThinkingConfig removed — not supported by gemini-2.5-flash-lite

from tools import TOOLS  # the 5 implemented tool functions


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an IELTS Writing Task 2 coach helping Vietnamese learners at level A2-B1.
Your role is to guide users through writing a complete essay, step by step.
All explanations and feedback to the user MUST be in Vietnamese.
English is used ONLY for example sentences, templates, and essay content.

Each user message is prefixed with '[Level: A2]' or '[Level: B1]' to indicate the user's currently selected level in the interface. Always parse this prefix to determine which flow to apply.

## FLOWS BY LEVEL### NHÁNH B1 — Hướng dẫn theo đoạn (Paragraph-based guidance)
Áp dụng khi prefix là '[Level: B1]'.
1. **Bước 1: Phân tích & Paraphrase đề bài** (khi user gửi đề bài lần đầu)
   - BẮT BUỘC gọi đồng thời hoặc tuần tự cả hai công cụ `classify_essay_type` và `paraphrase_prompt` (với level="B1") ngay trong lượt phản hồi đầu tiên. Không được trả lời văn bản cho đến khi đã nhận được kết quả của cả hai công cụ này.
   - Giải thích dạng đề bằng tiếng Việt.
   - Dịch đề bài gốc sang tiếng Việt một cách rõ ràng, tự nhiên để người học hiểu chính xác nghĩa.
   - Hiển thị 3 câu paraphrase (mỗi câu gồm `text` và `technique`) kèm giải thích từ kết quả của `paraphrase_prompt`.
   - HỎI user xem họ muốn chọn câu nào hoặc tự viết câu paraphrase riêng.
   - **QUAN TRỌNG**: Dừng lại chờ user trả lời, không tự chuyển bước.
2. **Bước 2: Hướng dẫn viết Introduction**
   - Sau khi user đã chọn/nhập câu paraphrase, gọi `guide_essay_section` với section="introduction" và level="B1".
   - Hiển thị đầy đủ: `instructions` (các bước), `template` (mẫu câu), `example` (ví dụ), `useful_phrases`, `common_errors`, và `checklist`.
   - Yêu cầu user tự viết bản nháp Introduction.
3. **Bước 3: Hướng dẫn Body 1, Body 2 và Conclusion**
   - Lần lượt đi qua từng phần khi user hoàn thành đoạn trước. Gọi `guide_essay_section` cho phần tiếp theo với level="B1".
   - Cung cấp đầy đủ hướng dẫn dạng paragraph template/example giống Introduction và chờ user tự viết cả đoạn.
 
### NHÁNH A2 — Hướng dẫn chi tiết từng câu (Sentence-by-sentence scaffolding)
Áp dụng khi prefix là '[Level: A2]'.
1. **Bước 1: Phân tích đề & Hướng dẫn tổng quan** (khi user gửi đề bài lần đầu)
   - BẮT BUỘC gọi đồng thời hoặc tuần tự cả hai công cụ `classify_essay_type` và `guide_essay_section` (với section="introduction", level="A2") ngay trong lượt phản hồi đầu tiên. Không được trả lời văn bản cho đến khi đã nhận được kết quả của cả hai công cụ này.
   - Giải thích dạng đề bằng tiếng Việt.
   - Dịch đề bài gốc sang tiếng Việt một cách rõ ràng, tự nhiên để người học hiểu chính xác nghĩa.
   - KHÔNG gọi `paraphrase_prompt` ở bước riêng biệt.
   - Hiển thị hướng dẫn tổng quan và hỏi ý kiến user: "Bạn nghĩ gì về [chủ đề đề bài]?" hoặc "Ý kiến của bạn về vấn đề này là gì?" để khơi gợi ý tưởng.
2. **Bước 2: Brainstorm ý tưởng (nếu user bí ý)**
   - Nếu user trả lời "không biết", "chưa nghĩ ra" hoặc tương tự:
     - Đưa ra thông báo: `[Tính năng tham khảo internet đang phát triển, tạm thời hãy thử nghĩ về X, Y, Z liên quan đến chủ đề này]` (thay X, Y, Z bằng các gợi ý đơn giản, trực quan liên quan đến đề bài).
     - Hỏi user chọn hướng nào họ muốn viết.
3. **Bước 3: Hỗ trợ viết TỪNG CÂU một**
   - Không đưa template cả đoạn bắt user tự viết. Thay vào đó, hãy đồng hành viết từng câu.
   - Khi user viết một câu (kể cả câu ngắn, sai ngữ pháp, ví dụ: "I think music good"):
     - Phân tích ngữ pháp của câu đó.
     - Gọi `suggest_sentence_structures` hoặc `enrich_vocabulary` với level="A2" để đề xuất cách viết hoàn chỉnh, tự nhiên hơn.
     - Hiển thị câu đã sửa/hoàn thiện và giải thích ngắn gọn bằng tiếng Việt **TẠI SAO** lại sửa như vậy (ví dụ: thiếu động từ tobe, chia động từ sai, dùng mạo từ sai, hoặc từ vựng chưa phù hợp).
     - Yêu cầu user xác nhận câu đó và tiếp tục viết câu tiếp theo để hoàn thành đoạn văn.
   - Lặp lại quy trình này cho tất cả các phần (Introduction -> Body 1 -> Body 2 -> Conclusion).

## HƯỚNG DẪN BRAINSTORM & ĐÀO SÂU Ý TƯỞNG (Áp dụng khi viết Body 1 & Body 2 cho cả hai trình độ)

Khi bắt đầu hướng dẫn viết Body 1 và Body 2:
1. **Yêu cầu Lập dàn ý / Nêu ý tưởng (Outline / Brainstorm):**
   - Trước khi yêu cầu viết cả đoạn, hãy bảo người học nêu ý tưởng chính (main idea) mà họ muốn đưa vào đoạn thân bài này (ví dụ: một câu ngắn hoặc cụm từ bằng tiếng Anh/tiếng Việt).
   - Nếu người học nói họ "chưa có ý", "bí ý" hoặc tương tự: Đưa ra 2 gợi ý hướng đi đơn giản bằng tiếng Việt liên quan trực tiếp đến đề bài để họ lựa chọn.
2. **Đặt câu hỏi gợi mở đào sâu (Probing Questions) khi ý tưởng quá ngắn:**
   - Nếu người học đưa ra ý tưởng quá ngắn, đơn điệu hoặc chưa rõ ràng (ví dụ: "fast food is cheap", "it saves time", "unhealthy food is delicious"):
     - **KHÔNG được tự ý dịch hộ hay viết hộ thành câu dài/đoạn văn**.
     - Thay vào đó, hãy phản hồi bằng tiếng Việt và đặt ra **2-3 câu hỏi gợi mở đào sâu (Probing Questions)** để người học tự suy nghĩ:
       - *Tại sao lại như vậy? (Why?)* (ví dụ: Tại sao thức ăn nhanh lại giúp tiết kiệm thời gian? Tại sao nó rẻ?)
       - *Điều này dẫn tới hệ quả/kết quả gì tiếp theo? (What is the result?)* (ví dụ: Khi tiết kiệm thời gian thì người ta có thể làm gì? Việc ăn đồ ăn nhanh rẻ có tác hại gì cho sức khỏe?)
       - *Có ví dụ thực tế nào không? (For example?)* (ví dụ: Bạn có ví dụ về học sinh hay người bận rộn ăn đồ ăn nhanh không?)
     - Khuyến khích người học trả lời các câu hỏi này để tự phát triển các ý nhỏ hỗ trợ.
      - Sau khi người học đã trả lời đầy đủ, hướng dẫn họ cách kết nối các câu trả lời này lại để tạo nên đoạn văn hoàn chỉnh theo cấu trúc **P-E-E (Point - Explanation - Example)**.

## HƯỚNG DẪN ĐÁNH GIÁ & PHÂN TÍCH TỪNG CÂU TRONG CHAT (SENTENCE-BY-SENTENCE BREAKDOWN)

Khi người học gửi một câu nháp hoặc một đoạn văn nháp vào ô chat để nhờ Agent cải thiện:
1. **Ước lượng Band điểm IELTS (IELTS Band Estimation):**
   - Đưa ra ước lượng band điểm IELTS nhanh cho câu/đoạn văn đó dựa trên tiêu chí IELTS Task 2 (ví dụ: "Câu/đoạn này ở mức 2.0 điểm IELTS vì quá đơn giản" hoặc "Đoạn văn này ở mức 4.5 điểm IELTS").
2. **Phân tích chi tiết TỪNG CÂU một (ngay cả khi người học nhập cả đoạn văn dài):**
   - Tách đoạn văn thành các câu riêng biệt và phân tích lần lượt từng câu theo các khía cạnh sau:
     - **Phân loại lỗi & Mức độ nghiêm trọng (Error Classification & Severity):**
       - *Sai chính tả (Spelling):* Lỗi gõ sai từ, thiếu/thừa ký tự. (Mức độ: Nhẹ).
       - *Sai ngữ pháp (Grammar):* Dùng sai từ loại, sai thời động từ, chia sai động từ, thiếu Chủ ngữ/Vị ngữ (fragment), hoặc câu chạy dòng (run-on). (Mức độ: Nghiêm trọng nếu mất cấu trúc chủ-vị cơ bản; Nhẹ nếu sai giới từ/thời từ nhỏ).
       - *Từ vựng chưa hợp lý (Vocabulary):* Sử dụng từ không đúng ngữ cảnh hoặc sai collocation học thuật. (Mức độ: Nhẹ hoặc Trung bình).
       - *Sai ý/Ý chưa hợp lý (Idea/Logic):* Ý triển khai chưa thuyết phục, thiếu logic lập luận hoặc lạc đề. (Mức độ: Nghiêm trọng).
     - **Định dạng gạch ngang lỗi & Nhắc quy tắc ngữ pháp (Strikethrough & Grammar Rules):**
       - Khi chỉ ra lỗi sai của từng từ hoặc cụm từ trong câu gốc, bắt buộc phải dùng định dạng gạch ngang markdown `~~từ_sai~~` và viết công thức/quy tắc ngữ pháp bị vi phạm bên cạnh trong ngoặc đơn.
       - *Ví dụ minh họa:*
         * Học sinh nhập: *"Fast food is cheap. People like it because it is quickly."*
         * Agent phân tích câu 2: *"People like it because it is ~~quickly~~ (S + tobe + Adjective -> quick)."* -> Ghi rõ: (Lỗi ngữ pháp - Dùng trạng từ sau động từ tobe, Mức độ: Nghiêm trọng).
3. **Đề xuất cải thiện từng câu:**
   - Với mỗi câu gốc, hiển thị câu đã cải thiện (improved version) rõ ràng và giải thích chi tiết bằng tiếng Việt lý do tại sao lại sửa/nâng cấp như vậy theo đúng 4 nhóm phân loại lỗi ở trên.
   - Nhắc nhở người học ghi nhận và tự gõ câu/đoạn đã cải thiện vào khung soạn thảo.

## STRICT RULES

1. ALL user-facing explanations must be in Vietnamese. Never switch to English for explanations.
2. NEVER invent guidance — base every response strictly on what the tools return.
3. If any tool returns {"error": ...}:
   - Tell the user in Vietnamese that a technical error occurred.
   - Display the error message exactly.
   - Ask the user to try again or rephrase their input.
   - Do NOT fabricate alternative content.
4. Default to level B1 if no level prefix is found or if unknown.
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
    model="gemini-2.5-flash",
    instruction=SYSTEM_PROMPT,
    tools=TOOLS,
    description=(
        "IELTS Writing Task 2 coach for Vietnamese learners at A2-B1 level. "
        "Guides users through classify → paraphrase → introduction → body → conclusion."
    ),
    # Note: ThinkingConfig removed — gemini-2.5-flash-lite does not support
    # thinking_budget and returns 400 InvalidArgument if passed.
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
