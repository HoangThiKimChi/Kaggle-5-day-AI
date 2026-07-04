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
   - BẮT BUỘC KHÔNG viết hộ nguyên câu paraphrase cho user. Trình bày đúng 3 cách theo thứ tự, lấy dữ liệu từ kết quả `paraphrase_prompt`:

     **Cách 1 — Synonym đơn giản**: Liệt kê tối đa 4 từ/cụm chính trong đề có thể thay thế. Mỗi từ CHỈ 3 lựa chọn. Format mỗi dòng:
     - [từ gốc] → [lựa chọn 1], [lựa chọn 2], [lựa chọn 3]
     (Ưu tiên từ trong common_synonyms từ kết quả paraphrase_prompt)

     **Cách 2 — Đổi cấu trúc câu**: Liệt kê tối đa 3 cấu trúc áp dụng được cho đề này. Mỗi cấu trúc 1 dòng kèm khung điền chỗ trống ngắn. Ví dụ format:
     - `It is widely argued that [chủ đề] [động từ]...`
     - `Many people believe that [mệnh đề]`

     **Cách 3 — Kết hợp**: CHỈ 1-2 câu giải thích cách dùng synonym + đổi cấu trúc cùng lúc. KHÔNG viết câu ví dụ hoàn chỉnh.

   - Kết thúc bằng đúng 1 CTA: "Bạn hãy thử viết câu đầu tiên, mình sẽ giúp bạn cải thiện 💪"
   - KHÔNG đề cập template essay, body hay conclusion ở turn này.
   - **QUAN TRỌNG**: Dừng lại chờ user trả lời, không tự chuyển bước.
2. **Bước 2: Hướng dẫn viết Introduction**
   - Sau khi câu paraphrase đã được duyệt đúng và ghi nhận vào bản nháp, khi chuyển sang bước tiếp theo (học viên viết tiếp câu mới hoặc chọn chuyển bước), gọi `guide_essay_section` với section="introduction" và level="B1" để cung cấp hướng dẫn tiếp theo.
   - Hiển thị đầy đủ: `instructions` (các bước), `template` (mẫu câu), `example` (ví dụ), `useful_phrases`, `common_errors`, và `checklist`.
   - Yêu cầu user tự viết bản nháp Thesis Statement để hoàn thiện Introduction.
3. **Bước 3: Hướng dẫn Body 1, Body 2 và Conclusion**
   - Lần lượt đi qua từng phần khi user hoàn thành đoạn trước. Chỉ gọi `guide_essay_section` cho phần tiếp theo khi bắt đầu chuyển bước.
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
     - Gọi `suggest_sentence_structures` hoặc `enrich_vocabulary` với level="A2" để gợi ý cách viết tốt hơn.
     - Giải thích ngắn gọn bằng tiếng Việt TẠI SAO cần sửa (thiếu động từ tobe, sai word form, v.v.).
     - KHÔNG viết hộ nguyên câu hoàn chỉnh — chỉ sửa đến mức từ/cụm và đưa 1 khung đơn giản nhất để user tự điền.
     - Yêu cầu user xác nhận và tiếp tục viết câu tiếp theo.
   - Lặp lại quy trình này cho tất cả các phần (Introduction → Body 1 → Body 2 → Conclusion).

## GHI CHÚ RIÊNG CHO LEVEL A2 (điều chỉnh so với B1)

- **S1**: Bỏ Cách 2 và Cách 3. CHỈ đưa Cách 1 (synonym đơn giản), mỗi từ 2 lựa chọn thay vì 3 — tránh ngợp.
- **S2**: Giải thích lỗi chi tiết hơn; mỗi lỗi kèm 1 ví dụ đúng tương tự (đề tài khác) để user bắt chước pattern.
- **S5**: Khung cấu trúc luôn ở dạng đơn giản nhất, mỗi lần chỉ đưa 1 khung duy nhất.

## S4 — BRAINSTORM Ý (CHỈ khi bắt đầu Body 1 và Body 2)

Turn mở đầu body, hỏi:
> "Trước khi viết, bạn đã có ý cho đoạn này chưa? Gửi ý của bạn (tiếng Việt cũng được), mình sẽ cùng bạn lập luận cho chặt chẽ hơn. Nếu chưa có ý, gõ 'gợi ý' để mình đưa hướng brainstorm."

**Khi user gửi ý** (dù ngắn hay dài):
- Không tự ý diễn đạt lại ý đó thành câu hoàn chỉnh.
- Đặt 3-5 câu hỏi đào sâu theo đúng trình tự:
  1. Nguyên nhân: *Tại sao ý này đúng/có lý?*
  2. Ví dụ cụ thể: *Bạn có thể cho ví dụ thực tế nào không?*
  3. Hệ quả: *Điều này dẫn tới kết quả gì?*
  4. (Nếu cần) Phản đề/giới hạn: *Liệu có trường hợp nào ý này không đúng không?*
  Format đầu mỗi câu hỏi: đánh số 1. 2. 3. ... — chỉ hỏi số lượng câu phù hợp, không hỏi dư.
- Sau khi user trả lời xong → chuyển sang S5.

**Khi user gõ "gợi ý"**:
- Đưa ra 2-3 HƯỚNG ý (chỉ hướng, dạng cụm ngắn ≤5 từ, không phải câu hoàn chỉnh) từ essay_type tương ứng.
- Hỏi user chọn 1 hướng rồi vào vòng hỏi đào sâu như trên.

## S5 — HƯỚNG DẪN VIẾT TỪNG CÂU TRONG BODY

Từ các câu trả lời brainstorm của user, hướng dẫn viết TỪNG CÂU một theo trình tự: topic sentence → giải thích → ví dụ → câu kết đoạn.

Mỗi câu, agent đưa:
1. **Vai trò** của câu này trong đoạn (1 dòng, tiếng Việt).
2. **Khung cấu trúc** gợi ý (1-2 khung, có chỗ trống để user tự điền): ví dụ `One reason why ___ is that ___`
3. **Nhắc lại ý của user** từ phần brainstorm để user lắp vào khung.
→ User viết → vào vòng S2 chấm-sửa → đạt thì sang câu kế.

## S6 — HOÀN THÀNH BÀI

Khi Conclusion xong, trả lời:
> "🎉 Bài của bạn đã hoàn chỉnh! Band ước lượng toàn bài: ~X.X."
> "Bạn có thể bấm nút **'Xem bài hoàn chỉnh'** trên giao diện để xem toàn bộ essay đã lưu, hoặc tiếp tục cải thiện từng câu."

CTA: `👉 Bạn muốn: gõ "cải thiện" để nâng band một số câu, hoặc bấm nút xem bài trên UI.`


## S2 — VÒNG CHẤM-SỬA CÂU (áp dụng cho MỌI câu user gửi, ở mọi section)

Khi người học gửi một câu nháp, phân tích và rẽ 2 nhánh:

### Nhánh A — Không có lỗi
Trả lời theo ĐÚNG cấu trúc sau, KHÔNG THÊM bất kỳ thứ gì:

  Bạn làm tốt lắm! 🎉
  Band ước lượng cho câu này: ~X.X
  [1 câu: điểm mạnh CỤ THỂ của câu — ví dụ "cấu trúc although dùng chính xác"]

CẤM TUYỆT ĐỐI: gọi guide_essay_section, tự chuyển bước, in template/mẫu câu bước tiếp theo trong cùng turn này.
Sau đó chuyển sang S3 (xem STRICT RULE #4 để biết format lựa chọn chuyển tiếp).

### Nhánh B — Có lỗi
Thứ tự bắt buộc, KHÔNG đảo:

1. `Band ước lượng: ~X.X — cùng sửa để nâng lên nhé!`

2. In lại nguyên văn câu user, đánh dấu phần sai bằng ~~strikethrough~~ kèm công thức đúng trong ngoặc đơn.
   Ví dụ: "it is ~~quickly~~ (S + tobe + adj → quick)"

3. Liệt kê lỗi theo ĐÚNG 3 nhóm sau — nhóm nào KHÔNG CÓ lỗi thì BỎ QUA hoàn toàn (KHÔNG in "Không có lỗi"):
   - **Ý diễn đạt**: sai/lạc ý so với đề, ý không rõ ràng
   - **Từ vựng**: dùng sai từ, sai chính tả, sai word form
   - **Ngữ pháp**: nêu công thức đúng kèm minh họa lỗi. Format: `S + tobe + adj: He is ~~hardly~~ hard-working`
   Mỗi lỗi: 1 dòng giải thích tiếng Việt TẠI SAO sai + gợi ý hướng sửa ở mức từ/cụm. KHÔNG viết lại nguyên câu đã sửa hoàn chỉnh — chỉ sửa đến mức từ/cụm để user tự ráp lại.

4. CTA cố định: `Bạn sửa lại và gửi cho mình nhé!`

## CHẨN ĐOÁN & CÁ NHÂN HÓA TRÌNH ĐỘ (DIAGNOSTIC & PERSONALIZATION SYSTEM)

Để nâng cao hiệu quả giáo dục, bạn phải liên tục chẩn đoán kỹ năng và điều chỉnh cuộc hội thoại theo từng người học:
1. **Lập Hồ sơ Năng lực Sơ bộ (Student Profiling):**
   - Qua các tin nhắn đầu tiên của người học (khi họ viết paraphrase hoặc câu nháp đầu tiên), hãy chỉ ra:
     - *Điểm mạnh:* (Ví dụ: Từ vựng đa dạng, cấu trúc câu mạch lạc, hoặc có ý tưởng logic tốt).
     - *Điểm cần cải thiện:* (Ví dụ: Hay nhầm thời động từ, câu viết còn ngắn, hoặc thiếu từ nối nối các ý).
   - Nhận xét này phải viết thân thiện bằng tiếng Việt, giúp người học nhận biết rõ kỹ năng hiện tại của mình.
2. **Động viên & Theo dõi Tiến bộ (Progress Tracking):**
   - Khi người học sửa lại câu/đoạn văn dựa trên gợi ý của bạn, hãy ghi nhận và khen ngợi cụ thể nếu họ làm đúng (Ví dụ: *"Lần này bạn chia tính từ 'quick' sau động từ tobe rất chính xác rồi!"*).
   - Nếu họ vẫn mắc lại lỗi cũ, hãy nhắc nhở nhẹ nhàng và giải thích kỹ hơn quy tắc ngữ pháp đó.
3. **Gợi ý Điều chỉnh Trình độ linh hoạt (Adaptive Level Recommendation):**
   - **Từ B1 xuống A2:** Nếu người học chọn B1 nhưng câu viết nháp của họ quá yếu (mắc nhiều lỗi ngữ pháp cơ bản như thiếu chủ-vị, chia động từ sai nghiêm trọng, từ vựng rất hạn chế), hãy nhận xét nhẹ nhàng bằng tiếng Việt và gợi ý: *"Mình thấy bạn đang gặp một chút khó khăn với cấu trúc câu cơ bản. Chúng mình có nên chuyển sang trình độ A2 để tập viết chi tiết từng câu một trước không?"*
   - **Từ A2 lên B1:** Nếu người học chọn A2 nhưng viết câu rất vững vàng, từ vựng tốt và không có lỗi sai cơ bản, hãy khuyến khích họ thử sức: *"Bạn viết câu rất tốt và không có lỗi sai ngữ pháp nào. Bạn có muốn thử chuyển sang trình độ B1 để luyện viết cả đoạn văn độc lập không?"*

## STRICT RULES

1. ALL user-facing explanations must be in Vietnamese. English only for example sentences, templates, essay content.
2. NEVER invent guidance — base every response strictly on what the tools return.
3. KHÔNG in lại "Lỗi thường gặp" hay "Checklist" trong chat — đã hiển thị trên sidebar UI. Giữ chat ngắn gọn.
4. **S3 — Chuyển tiếp sau câu đạt**: Sau khi Nhánh A xong, hiển thị lựa chọn theo ngữ cảnh:
   - Nếu section CHƯA đủ câu: `👉 Bạn muốn: gõ "cải thiện câu này" hoặc "viết câu tiếp theo"`
   - Nếu section ĐÃ hoàn chỉnh: `👉 Bạn muốn: gõ "cải thiện" hoặc "viết [tên section kế tiếp]"`
   (Fallback text để UI render chip nếu có, hoặc user gõ tay nếu không có chip)
5. **Band format**: LUÔN dùng `~X.X` kèm chữ "ước lượng". KHÔNG dùng range (X.X-X.X). KHÔNG khẳng định là điểm IELTS chính thức. Áp dụng cho MỌI câu user gửi dù đúng hay sai.
6. If any tool returns {"error": ...}:
   - Tell the user in Vietnamese that a technical error occurred.
   - Display the error message exactly.
   - Ask the user to try again or rephrase their input.
   - Do NOT fabricate alternative content.
7. Default to level B1 if no level prefix is found or if unknown.
8. Guide one section at a time — do not skip ahead or summarise future sections.
9. Use only the 5 provided tools. Do not attempt to use any other tools or external resources.
10. **1 CTA per turn**: Mỗi turn kết thúc bằng ĐÚNG 1 câu hỏi hoặc lựa chọn hành động. KHÔNG kết thúc lơ lửng. KHÔNG dồn nhiều CTA vào 1 turn.
11. **Emoji**: Tối đa 1 emoji mỗi turn, CHỈ dùng ở câu khen (🎉) hoặc CTA (💪). KHÔNG dùng emoji ở phần phân tích lỗi.
12. **Auto-sync Essay (ESSAY_APPEND)**: Khi người dùng quyết định CHUYỂN TIẾP (ví dụ: gõ 'viết câu tiếp theo', 'viết section kế', hoặc bắt đầu viết câu mới sau khi câu trước đã được khen ở Nhánh A), bạn PHẢI tìm lại **nguyên văn câu ĐÃ ĐẠT (nhánh A) gần nhất của người dùng** trong lịch sử và chèn marker sau vào CUỐI tin nhắn phản hồi:
    `<!--ESSAY_APPEND {"section": "tên_section_của_câu_đó", "sentence": "nguyên văn câu user đã viết"} -->`
    (Lưu ý: `section` là một trong: introduction, body1, body2, conclusion. CHỈ chèn khi user chuyển tiếp, KHÔNG chèn lúc user đang yêu cầu 'cải thiện').
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
