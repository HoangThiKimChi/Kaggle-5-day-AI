"""
app.py — Essay Writing Coach (Streamlit UI)
============================================
Layout 3 vùng: Sidebar (progress) | Chat (center) | Panel kết quả (tabs)

Chạy:
    MOCK_GEMINI=1 streamlit run app.py        # mock, không tốn quota
    source ~/.zshrc && streamlit run app.py   # API thật

Spec: ui_spec.md
"""

import asyncio
import os
import sys
import uuid
import hashlib

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

sys.path.insert(0, os.path.dirname(__file__))

# Load env variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Forward GEMINI_API_KEY to GOOGLE_API_KEY for ADK internally
api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    os.environ.setdefault("GOOGLE_API_KEY", api_key)

# ── Mock mode ─────────────────────────────────────────────────────────────────
MOCK_MODE = os.environ.get("MOCK_GEMINI", "").strip() == "1"

# ── Import agent (lazy: chỉ import 1 lần khi cần) ────────────────────────────
from agent import create_runner, ensure_session
from tools import evaluate_essay
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Essay Writing Coach",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

SECTIONS = ["introduction", "body1", "body2", "conclusion"]
SECTION_LABELS = {
    "introduction": "Introduction",
    "body1": "Body 1",
    "body2": "Body 2",
    "conclusion": "Conclusion",
}
STATUS_ICON = {"pending": "🔲", "in_progress": "⏳", "done": "✅"}
CONFIDENCE_COLOR = {"high": "🟢", "medium": "🟡", "low": "🔴"}
ESSAY_TYPE_LABEL = {
    "opinion": "Opinion",
    "discussion": "Discussion",
    "adv_dis": "Advantages & Disadvantages",
    "problem_solution": "Problem & Solution",
    "two_part_question": "Two-Part Question",
}

# ─────────────────────────────────────────────────────────────────────────────
# run_turn_structured — text + tool_calls từ ADK event stream
# ─────────────────────────────────────────────────────────────────────────────

async def _run_turn_structured_real(
    runner: InMemoryRunner, session_id: str, user_id: str, message: str
) -> dict:
    await ensure_session(runner, user_id, session_id)
    msg = genai_types.Content(
        role="user", parts=[genai_types.Part(text=message)]
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


async def _run_turn_mock(
    runner: InMemoryRunner, session_id: str, user_id: str, message: str
) -> dict:
    """Mock turn: calls ensure_session (real ADK) but returns fixed structured data."""
    await ensure_session(runner, user_id, session_id)
    msg_lower = message.lower()
    is_a2 = "level: a2" in msg_lower

    # 1. First turn: essay prompt input
    if any(kw in msg_lower for kw in ["agree", "disagree", "extent", "opinion", "discuss", "advantage"]):
        if is_a2:
            return {
                "text": (
                    "Chào bạn! 👋 Mình đã phân tích đề bài của bạn.\n\n"
                    "Đây là dạng **Opinion Essay** (đồng ý hoặc không đồng ý). "
                    "Vì bạn đang ở trình độ A2, chúng ta sẽ bắt đầu viết mở bài từng câu một.\n\n"
                    "Đầu tiên, bạn nghĩ gì về chủ đề này? Hãy cho mình biết ý kiến ngắn gọn của bạn."
                ),
                "tool_calls": [
                    {
                        "tool": "classify_essay_type",
                        "args": {"essay_prompt": message[:80]},
                        "result": {
                            "essay_type": "opinion",
                            "confidence": "high",
                            "explanation": "[MOCK] Từ khóa 'agree or disagree' → Opinion Essay.",
                        },
                    },
                    {
                        "tool": "guide_essay_section",
                        "args": {"section": "introduction", "essay_type": "opinion"},
                        "result": {
                            "section": "introduction",
                            "next_section": "body1",
                            "instructions": [
                                "[MOCK A2] Bước 1: Trình bày bối cảnh đề bài bằng câu đơn giản.",
                                "[MOCK A2] Bước 2: Nêu ý kiến cá nhân rõ ràng (đồng ý hay phản đối).",
                            ],
                            "template": "[MOCK A2] Many people believe that [topic]. In my opinion, I agree with this because...",
                            "example": "[MOCK A2] Many people believe that music connects people. In my opinion, I agree with this because it is helpful.",
                            "useful_phrases": [
                                "Many people believe that...",
                                "In my opinion, I agree...",
                            ],
                            "common_errors": [
                                "[MOCK A2] Viết câu quá phức tạp dẫn đến sai ngữ pháp.",
                            ],
                            "checklist": [
                                "Đã có câu nêu quan điểm chưa?",
                            ],
                        },
                    },
                ],
            }
        else:
            return {
                "text": (
                    "Chào bạn! 👋 Mình đã phân tích đề bài của bạn.\n\n"
                    "Đây là dạng **Opinion Essay** — bạn cần nêu rõ ý kiến cá nhân "
                    "(đồng ý hoặc không đồng ý) và đưa ra 2 lý do cụ thể.\n\n"
                    "Mình cũng đã chuẩn bị 3 cách paraphrase đề bài cho bạn ở panel bên phải. "
                    "Bạn chọn cách nào hoặc mình tiến hành hướng dẫn phần Introduction nhé?"
                ),
                "tool_calls": [
                    {
                        "tool": "classify_essay_type",
                        "args": {"essay_prompt": message[:80]},
                        "result": {
                            "essay_type": "opinion",
                            "confidence": "high",
                            "explanation": "[MOCK] Từ khóa 'agree or disagree' → Opinion Essay.",
                        },
                    },
                    {
                        "tool": "paraphrase_prompt",
                        "args": {"prompt": message[:80], "level": "B1"},
                        "result": {
                            "level": "B1",
                            "paraphrases": [
                                {"text": "[MOCK] It is often argued that music serves as an effective means of uniting individuals from diverse cultural backgrounds.", "technique": "Synonym Substitution"},
                                {"text": "[MOCK] The notion that music plays a crucial role in fostering cohesion among people of varied backgrounds is widely held.", "technique": "Structure Change"},
                                {"text": "[MOCK] Many contend that music possesses a unique ability to bridge divides between cultures and generations.", "technique": "Perspective Shift"},
                            ],
                            "explanation": "[MOCK] Ba cách paraphrase đề bài ở trình độ B1.",
                        },
                    },
                ],
            }

    # 2. A2 Brainstorming if user is stuck
    if is_a2 and any(kw in msg_lower for kw in ["không biết", "chưa nghĩ ra", "bí ý"]):
        return {
            "text": (
                "Không sao cả! Mình sẽ gợi mở ý tưởng cho bạn.\n\n"
                "[Tính năng tham khảo internet đang phát triển, tạm thời hãy thử nghĩ về hai hướng này nhé]:\n"
                "1. **Hướng 1**: Âm nhạc giúp kết nối mọi người thông qua cảm xúc chung.\n"
                "2. **Hướng 2**: Âm nhạc giúp giải tỏa căng thẳng trong cuộc sống.\n\n"
                "Bạn muốn chọn hướng nào để viết câu đầu tiên?"
            ),
            "tool_calls": []
        }

    # 3. A2 Sentence correction (short sentences or broken English)
    if is_a2 and not any(kw in msg_lower for kw in ["introduction", "mở bài", "body", "lý do", "conclusion", "kết bài"]):
        clean_msg = message.split("]")[-1].strip()
        return {
            "text": (
                f"Mình nhận được câu viết của bạn: \"*{clean_msg}*\" (Trình độ A2).\n\n"
                "Cú pháp câu này chưa hoàn chỉnh. Mình đề xuất sửa lại như sau:\n"
                "- Câu hoàn chỉnh: **\"I believe that music is highly beneficial.\"**\n"
                "- Giải thích lỗi sai: Câu của bạn thiếu động từ to-be 'is' trước tính từ 'good' (music is good), "
                "và ta nên nâng cấp 'good' thành 'highly beneficial' để đạt điểm từ vựng tốt hơn.\n\n"
                "Bạn xem gợi ý chi tiết ở tab Hướng dẫn nhé! Bạn có muốn lưu câu này vào bài viết không?"
            ),
            "tool_calls": [
                {
                    "tool": "suggest_sentence_structures",
                    "args": {"idea": clean_msg, "level": "A2"},
                    "result": {
                        "original": clean_msg,
                        "variations": [
                            {
                                "pattern": "I believe that S + is + highly beneficial",
                                "text": "I believe that music is highly beneficial.",
                                "level": "A2",
                                "explanation": "Thêm động từ 'is' và nâng cấp 'good' thành 'highly beneficial'.",
                            }
                        ],
                        "explanation": "[MOCK A2] Giải thích lỗi sai ngữ pháp cho A2.",
                        "avoid": ["avoid writing 'music good' without verb"],
                    }
                }
            ]
        }

    # 4. Standard section guidance
    if "introduction" in msg_lower or "mở bài" in msg_lower:
        return {
            "text": (
                "📌 **Hướng dẫn viết Introduction**\n\n"
                "Mình đã chuẩn bị hướng dẫn chi tiết ở panel bên phải — "
                "bao gồm mẫu câu, ví dụ, và checklist tự kiểm tra. "
                "Bạn đọc qua rồi thử viết phần Introduction vào tab 'Bài viết' nhé!"
            ),
            "tool_calls": [
                {
                    "tool": "guide_essay_section",
                    "args": {"section": "introduction", "essay_type": "opinion"},
                    "result": {
                        "section": "introduction",
                        "next_section": "body1",
                        "instructions": [
                            "[MOCK] Bước 1: Paraphrase đề bài — thay ít nhất 3-4 từ chính bằng từ đồng nghĩa.",
                            "[MOCK] Bước 2: Nêu rõ thesis statement — bạn đồng ý hay không đồng ý?",
                            "[MOCK] Bước 3: Báo hiệu sẽ đưa ra 2 lý do trong body.",
                        ],
                        "template": "[MOCK] It is [often/widely] argued that [paraphrase topic]. I completely [agree/disagree] with this view for two main reasons.",
                        "example": "[MOCK] It is often argued that music serves as a universal connector across cultures and generations. I completely agree with this perspective.",
                        "useful_phrases": [
                            "It is often argued that...",
                            "This essay strongly agrees/disagrees...",
                            "Many people believe that...",
                            "I completely agree with this view...",
                        ],
                        "common_errors": [
                            "[MOCK] Lặp từ từ đề bài — phải paraphrase, không copy nguyên văn.",
                            "[MOCK] Quên nêu thesis statement rõ ràng.",
                            "[MOCK] Introduction quá dài (>3 câu) hoặc quá ngắn (1 câu).",
                        ],
                        "checklist": [
                            "Đã paraphrase đề bài (không copy nguyên văn)?",
                            "Đã nêu rõ thesis statement (đồng ý/không đồng ý)?",
                            "Câu dẫn đọc tự nhiên, không cứng nhắc?",
                        ],
                    },
                },
            ],
        }

    if "body" in msg_lower or "lý do" in msg_lower or "body 1" in msg_lower:
        return {
            "text": (
                "📌 **Hướng dẫn viết Body 1**\n\n"
                "Hướng dẫn chi tiết đã có ở panel bên phải. "
                "Nhớ dùng cấu trúc TEE: **T**opic sentence → **E**xplanation → **E**xample."
            ),
            "tool_calls": [
                {
                    "tool": "guide_essay_section",
                    "args": {"section": "body1", "essay_type": "opinion"},
                    "result": {
                        "section": "body1",
                        "next_section": "body2",
                        "instructions": [
                            "[MOCK] Bước 1: Viết Topic sentence — nêu lý do chính rõ ràng.",
                            "[MOCK] Bước 2: Explanation — giải thích tại sao lý do đó đúng.",
                            "[MOCK] Bước 3: Example — ví dụ cụ thể để minh chứng.",
                        ],
                        "template": "[MOCK] Firstly, [lý do chính]. This is because [giải thích]. For instance, [ví dụ cụ thể].",
                        "example": "[MOCK] Firstly, music transcends language barriers, allowing people from different countries to connect emotionally. This is because lyrics carry universal emotions that resonate across cultures. For instance, K-pop has gained millions of fans worldwide despite being in Korean.",
                        "useful_phrases": [
                            "Firstly, / To begin with,",
                            "This is because...",
                            "For instance, / For example,",
                            "As a result, / Consequently,",
                        ],
                        "common_errors": [
                            "[MOCK] Viết topic sentence quá chung chung — phải liên kết rõ với đề bài.",
                            "[MOCK] Thiếu example cụ thể — không có số liệu hay tình huống thật.",
                        ],
                        "checklist": [
                            "Topic sentence có nêu rõ 1 lý do duy nhất không?",
                            "Explanation có giải thích cơ chế/logic không?",
                            "Example có cụ thể và thuyết phục không?",
                        ],
                    },
                },
            ],
        }

    if "vocabulary" in msg_lower or "từ vựng" in msg_lower or "enrich" in msg_lower:
        return {
            "text": "📝 Gợi ý từ vựng đã có ở panel bên phải. Hãy xem và chọn từ phù hợp với văn phong của bạn!",
            "tool_calls": [
                {
                    "tool": "enrich_vocabulary",
                    "args": {"text": message[:80]},
                    "result": {
                        "overused_words": ["people (2x)", "good", "technology"],
                        "suggestions": {
                            "people": [{"word": "individuals", "meaning": "cá nhân", "example": "[MOCK] Individuals benefit greatly from this."}],
                            "good": [{"word": "beneficial", "meaning": "có lợi", "example": "[MOCK] This is highly beneficial."}],
                        },
                        "topic_words": [{"word": "cultural harmony", "meaning": "sự hòa hợp văn hóa", "example": "[MOCK] Music promotes cultural harmony."}],
                        "collocations": ["foster unity", "bridge divides"],
                        "improved_text": "[MOCK] Individuals benefit greatly from music as it fosters cultural harmony.",
                        "explanation": "[MOCK] Đã thay thế các từ lặp bằng từ vựng học thuật.",
                    },
                },
            ],
        }

    # Default
    return {
        "text": (
            "Tôi hiểu yêu cầu của bạn. 😊\n\n"
            "Để bắt đầu, hãy paste đề bài IELTS Writing Task 2 của bạn vào đây — "
            "mình sẽ phân tích dạng đề và hướng dẫn từng bước."
        ),
        "tool_calls": [],
    }


def run_turn_structured(runner: InMemoryRunner, session_id: str, user_id: str, message: str) -> dict:
    """Sync wrapper for async run_turn_structured. Safe to call from Streamlit."""
    if MOCK_MODE:
        coro = _run_turn_mock(runner, session_id, user_id, message)
    else:
        coro = _run_turn_structured_real(runner, session_id, user_id, message)
    return asyncio.run(coro)


# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "messages": [],
        "essay_type": "opinion",
        "essay_type_confidence": None,
        "level": "B1",
        "current_section": None,
        "sections_status": {s: "pending" for s in SECTIONS},
        "essay_draft": {s: "" for s in SECTIONS},
        "last_tool_result": None,   # {"tool_name": str, "data": dict}
        "adk_runner": None,
        "adk_session_id": None,
        "adk_user_id": "streamlit_user",
        "pending_retry": False,
        "last_user_msg": "",
        "essay_evaluation": None,
        "evaluation_cache": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ADK runner khởi tạo 1 lần duy nhất
    if st.session_state["adk_runner"] is None:
        st.session_state["adk_runner"] = create_runner()
        st.session_state["adk_session_id"] = str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Process tool_calls → update state
# ─────────────────────────────────────────────────────────────────────────────

def _apply_tool_calls(tool_calls: list[dict]) -> None:
    """Update session_state from tool call results."""
    for tc in tool_calls:
        tool_name = tc.get("tool", "")
        result = tc.get("result") or {}

        if tool_name == "classify_essay_type":
            st.session_state["essay_type"] = result.get("essay_type")
            st.session_state["essay_type_confidence"] = result.get("confidence")

        elif tool_name == "paraphrase_prompt":
            st.session_state["last_tool_result"] = {"tool_name": "paraphrase_prompt", "data": result}

        elif tool_name == "guide_essay_section":
            section = result.get("section")
            if section and section in SECTIONS:
                # Mark current section as in_progress if pending
                if st.session_state["sections_status"][section] == "pending":
                    st.session_state["sections_status"][section] = "in_progress"
                st.session_state["current_section"] = section
            st.session_state["last_tool_result"] = {"tool_name": "guide_essay_section", "data": result}

        elif tool_name == "suggest_sentence_structures":
            st.session_state["last_tool_result"] = {"tool_name": "suggest_sentence_structures", "data": result}

        elif tool_name == "enrich_vocabulary":
            st.session_state["last_tool_result"] = {"tool_name": "enrich_vocabulary", "data": result}


# ─────────────────────────────────────────────────────────────────────────────
# Send message handler
# ─────────────────────────────────────────────────────────────────────────────

def _send_message(user_input: str) -> None:
    if not user_input.strip():
        return

    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.session_state["last_user_msg"] = user_input
    st.session_state["pending_retry"] = False

    # Prepend target level as prefix so agent can read and process level flows correctly
    level_prefix = f"[Level: {st.session_state['level']}] "
    prefixed_input = level_prefix + user_input

    try:
        result = run_turn_structured(
            st.session_state["adk_runner"],
            st.session_state["adk_session_id"],
            st.session_state["adk_user_id"],
            prefixed_input,
        )
        _apply_tool_calls(result["tool_calls"])
        st.session_state["messages"].append({"role": "agent", "content": result["text"]})
    except Exception as exc:
        err_type = type(exc).__name__
        if "429" in str(exc) or "ResourceExhausted" in err_type:
            friendly = "⚠️ Đã vượt giới hạn quota API. Vui lòng thử lại sau vài phút."
        elif "NotFound" in err_type or "404" in str(exc):
            friendly = "⚠️ Lỗi kết nối tới mô hình AI (404). Vui lòng kiểm tra lại API key."
        else:
            friendly = f"⚠️ Đã xảy ra lỗi kỹ thuật ({err_type}). Vui lòng thử lại."
        st.session_state["messages"].append({"role": "error", "content": friendly})
        st.session_state["pending_retry"] = True


# ─────────────────────────────────────────────────────────────────────────────
# UI — Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ✍️ Essay Writing Coach")
        if MOCK_MODE:
            st.caption("🔧 Mock mode (MOCK_GEMINI=1)")
        st.divider()

        # Essay type
        st.markdown("**📄 Dạng đề**")
        et = st.session_state["essay_type"]
        conf = st.session_state["essay_type_confidence"]
        if et:
            conf_icon = CONFIDENCE_COLOR.get(conf or "low", "⚪")
            label = ESSAY_TYPE_LABEL.get(et, et)
            st.markdown(f"{conf_icon} **{label}**")
            if conf:
                st.caption(f"Độ tin cậy: {conf}")
        else:
            st.markdown("_Chưa xác định — paste đề bài vào chat_")

        st.divider()

        # Level selector
        st.markdown("**🎯 Trình độ**")
        level = st.radio(
            "Chọn level",
            ["A2", "B1"],
            index=0 if st.session_state["level"] == "A2" else 1,
            label_visibility="collapsed",
            key="level_radio",
        )
        if level != st.session_state["level"]:
            st.session_state["level"] = level

        st.divider()

        # Progress checklist
        st.markdown("**📊 Tiến độ**")
        for sec in SECTIONS:
            status = st.session_state["sections_status"][sec]
            icon = STATUS_ICON[status]
            label = SECTION_LABELS[sec]
            is_current = st.session_state["current_section"] == sec
            if is_current:
                st.markdown(f"{icon} **{label}** ← đang làm")
            else:
                st.markdown(f"{icon} {label}")

        st.divider()

        # Reset button
        if st.button("🔄 Bắt đầu lại", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# UI — Chat column
# ─────────────────────────────────────────────────────────────────────────────

def _render_chat(col: DeltaGenerator) -> None:
    with col:
        st.markdown("### 💬 Chat")

        # Message history
        chat_container = st.container(height=520)
        with chat_container:
            if not st.session_state["messages"]:
                st.markdown(
                    "_Chào bạn! Hãy paste đề bài IELTS Writing Task 2 vào ô bên dưới "
                    "để bắt đầu. Mình sẽ hướng dẫn từng bước từ Introduction đến Conclusion._"
                )
            for msg in st.session_state["messages"]:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif role == "agent":
                    with st.chat_message("assistant"):
                        st.markdown(content)
                elif role == "error":
                    with st.chat_message("assistant"):
                        st.error(content)

        # Retry button (shown only after error)
        if st.session_state.get("pending_retry"):
            if st.button("🔁 Thử lại", key="retry_btn"):
                last_msg = st.session_state.get("last_user_msg", "")
                if last_msg:
                    # Remove last error message
                    msgs = st.session_state["messages"]
                    if msgs and msgs[-1]["role"] == "error":
                        st.session_state["messages"] = msgs[:-1]
                    _send_message(last_msg)
                    st.rerun()

        # Input box
        user_input = st.chat_input(
            "Nhập đề bài hoặc câu hỏi của bạn...",
            key="chat_input",
        )
        if user_input:
            _send_message(user_input)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# UI — Panel kết quả (tab Hướng dẫn)
# ─────────────────────────────────────────────────────────────────────────────

def _render_guidance_tab() -> None:
    ltr = st.session_state.get("last_tool_result")
    if not ltr:
        st.markdown("_Chưa có hướng dẫn. Hãy bắt đầu bằng cách gửi đề bài vào chat._")
        return

    tool_name = ltr.get("tool_name", "")
    data = ltr.get("data", {})

    if tool_name == "guide_essay_section":
        section = data.get("section", "")
        st.markdown(f"#### 📌 Hướng dẫn: {SECTION_LABELS.get(section, section)}")

        instructions = data.get("instructions", [])
        if instructions:
            st.markdown("**Các bước thực hiện:**")
            for i, step in enumerate(instructions, 1):
                st.markdown(f"{i}. {step}")

        template = data.get("template")
        if template:
            st.markdown("**✏️ Mẫu câu (điền vào chỗ trống):**")
            st.code(template, language=None)

        example = data.get("example")
        if example:
            st.markdown("**💡 Ví dụ:**")
            st.info(example)

        phrases = data.get("useful_phrases", [])
        if phrases:
            st.markdown("**🔑 Useful phrases:**")
            for p in phrases:
                st.markdown(f"- `{p}`")

        errors = data.get("common_errors", [])
        if errors:
            st.markdown("**⚠️ Lỗi thường gặp:**")
            for e in errors:
                st.warning(e)

        checklist = data.get("checklist", [])
        if checklist:
            st.markdown("**✅ Tự kiểm tra trước khi tiếp tục:**")
            for item in checklist:
                st.checkbox(item, key=f"chk_{section}_{item[:20]}")

    elif tool_name == "paraphrase_prompt":
        st.markdown("#### 🔄 Paraphrase đề bài")
        paraphrases = data.get("paraphrases", [])
        for i, p in enumerate(paraphrases, 1):
            st.markdown(f"**Cách {i} — {p.get('technique', '')}:**")
            st.success(p.get("text", ""))
        explanation = data.get("explanation")
        if explanation:
            st.caption(explanation)

    elif tool_name == "suggest_sentence_structures":
        st.markdown("#### 🏗️ Gợi ý cấu trúc câu")
        variations = data.get("variations", [])
        for v in variations:
            st.markdown(f"**Pattern:** `{v.get('pattern', '')}`")
            st.info(v.get("text", ""))
            if v.get("explanation"):
                st.caption(v["explanation"])
        avoid = data.get("avoid", [])
        if avoid:
            st.markdown("**Tránh:**")
            for a in avoid:
                st.warning(a)

    elif tool_name == "enrich_vocabulary":
        st.markdown("#### 📚 Làm giàu từ vựng")
        overused = data.get("overused_words", [])
        if overused:
            st.markdown(f"**Từ lặp:** {', '.join(overused)}")
        suggestions = data.get("suggestions", {})
        for word, sug_list in suggestions.items():
            st.markdown(f"**Thay `{word}` bằng:**")
            for sug in sug_list:
                st.markdown(f"- **{sug['word']}** ({sug['meaning']}): _{sug['example']}_")
        topic_words = data.get("topic_words", [])
        if topic_words:
            st.markdown("**Từ vựng theo chủ đề:**")
            for tw in topic_words:
                st.markdown(f"- **{tw['word']}** ({tw['meaning']}): _{tw['example']}_")
        improved = data.get("improved_text")
        if improved:
            st.markdown("**Văn bản đã cải thiện:**")
            st.success(improved)


# ─────────────────────────────────────────────────────────────────────────────
# UI — Panel kết quả (tab Bài viết)
# ─────────────────────────────────────────────────────────────────────────────

def _render_essay_tab() -> None:
    st.markdown("#### 📝 Bài viết của bạn")
    st.caption("Tự gõ/dán nội dung của bạn vào từng phần — agent không viết hộ, chỉ hướng dẫn.")

    # Essay type: hiển thị kết quả agent tự xác định, không cần chọn tay
    essay_types = {
        "opinion":                  "Quan điểm cá nhân (Opinion)",
        "discussion":               "Thảo luận hai quan điểm (Discussion)",
        "problem_solution":         "Vấn đề - Giải pháp (Problem - Solution)",
        "adv_dis":                  "Lợi ích - Bất lợi (Advantages - Disadvantages)",
        "two_part_question":        "Câu hỏi hai phần (Two-part question)",
        "advantages_disadvantages": "Lợi ích - Bất lợi (Advantages - Disadvantages)",
    }

    current_type = st.session_state.get("essay_type")
    conf         = st.session_state.get("essay_type_confidence")

    if current_type and current_type in essay_types:
        conf_icon = CONFIDENCE_COLOR.get(conf or "low", "⚪")
        label     = essay_types[current_type]
        st.success(f"{conf_icon} **Dạng đề được xác định: {label}**")
        if conf:
            st.caption(f"Độ tin cậy: {conf} — Agent tự phân loại dựa trên đề bài bạn nhập ở Chat.")
    else:
        st.info("💡 Paste đề bài vào **Chat** — agent sẽ tự xác định dạng bài luận cho bạn.")

    # Cho phép ghi đè thủ công nếu agent xác định sai
    with st.expander("⚙️ Điều chỉnh dạng đề (nếu agent xác định sai)", expanded=False):
        keys_list = list(essay_types.keys())[:5]  # bỏ alias advantages_disadvantages
        fallback_type = current_type if current_type in keys_list else "opinion"
        selected_type_key = st.selectbox(
            "Chọn lại dạng bài luận:",
            options=keys_list,
            format_func=lambda x: essay_types[x],
            index=keys_list.index(fallback_type),
            key="selectbox_essay_type_widget",
        )
        if selected_type_key != st.session_state.get("essay_type"):
            if st.button("✅ Xác nhận thay đổi", key="btn_override_essay_type"):
                st.session_state["essay_type"] = selected_type_key
                st.rerun()


    st.divider()

    for sec in SECTIONS:
        status = st.session_state["sections_status"][sec]
        icon = STATUS_ICON[status]
        label = SECTION_LABELS[sec]

        st.markdown(f"**{icon} {label}**")

        draft = st.text_area(
            label=f"draft_{sec}",
            value=st.session_state["essay_draft"][sec],
            placeholder=f"Viết {label} vào đây...",
            height=100,
            label_visibility="collapsed",
            key=f"textarea_{sec}",
        )
        # Persist draft edits
        if draft != st.session_state["essay_draft"][sec]:
            st.session_state["essay_draft"][sec] = draft

        # "Xong phần này" button — only show for current in-progress section
        if status == "in_progress" and draft.strip():
            if st.button(f"✅ Xong phần {label}", key=f"done_{sec}"):
                # Determine the next section key and construct an explicit instruction
                idx = SECTIONS.index(sec)
                if idx + 1 < len(SECTIONS):
                    next_sec = SECTIONS[idx + 1]
                    next_label = SECTION_LABELS[next_sec]
                    user_msg = (
                        f"Tôi đã viết xong phần {label} (khóa '{sec}'). "
                        f"Đây là nội dung của tôi:\n\"{draft.strip()}\"\n\n"
                        f"Hãy nhận xét ngắn gọn bài viết của tôi bằng tiếng Việt. "
                        f"Sau đó, BẮT BUỘC gọi công cụ guide_essay_section với section='{next_sec}' "
                        f"và essay_type='{st.session_state.get('essay_type')}' để hiển thị hướng dẫn phần tiếp theo ({next_label})."
                    )
                else:
                    user_msg = (
                        f"Tôi đã viết xong phần {label} (khóa '{sec}'). "
                        f"Đây là nội dung của tôi:\n\"{draft.strip()}\"\n\n"
                        f"Hãy nhận xét ngắn gọn toàn bộ bài viết hoàn chỉnh bằng tiếng Việt. "
                        f"Không cần gọi thêm công cụ guide_essay_section nữa."
                    )

                st.session_state["messages"].append({"role": "user", "content": user_msg})
                st.session_state["last_user_msg"] = user_msg
                st.session_state["pending_retry"] = False

                # Prepend target level as prefix
                level_prefix = f"[Level: {st.session_state['level']}] "
                prefixed_input = level_prefix + user_msg

                try:
                    with st.spinner("Agent đang kiểm tra bài viết và chuẩn bị hướng dẫn phần tiếp theo..."):
                        result = run_turn_structured(
                            st.session_state["adk_runner"],
                            st.session_state["adk_session_id"],
                            st.session_state["adk_user_id"],
                            prefixed_input,
                        )
                    # Mark current section as done
                    st.session_state["sections_status"][sec] = "done"
                    
                    # Apply tool calls (e.g. guide_essay_section for next section)
                    _apply_tool_calls(result["tool_calls"])
                    
                    # Append agent's feedback message
                    st.session_state["messages"].append({"role": "agent", "content": result["text"]})

                    # Save session state if database is enabled
                    if st.session_state.get("db_enabled"):
                        try:
                            from db import save_session
                            save_session(
                                session_id=st.session_state["adk_session_id"],
                                essay_type=st.session_state["essay_type"],
                                level=st.session_state["level"],
                                sections_status=st.session_state["sections_status"],
                                essay_draft=st.session_state["essay_draft"]
                            )
                        except Exception:
                            pass
                except Exception as exc:
                    err_type = type(exc).__name__
                    if "429" in str(exc) or "ResourceExhausted" in err_type:
                        friendly = "⚠️ Đã vượt giới hạn quota API. Vui lòng thử lại sau vài phút."
                    elif "NotFound" in err_type or "404" in str(exc):
                        friendly = "⚠️ Lỗi kết nối tới mô hình AI (404). Vui lòng kiểm tra lại API key."
                    else:
                        friendly = f"⚠️ Đã xảy ra lỗi kỹ thuật ({err_type}). Vui lòng thử lại."
                    st.session_state["messages"].append({"role": "error", "content": friendly})
                    st.session_state["pending_retry"] = True
                st.rerun()

    st.divider()

    # Copy full essay
    full_essay = "\n\n".join(
        f"[{SECTION_LABELS[s]}]\n{st.session_state['essay_draft'][s]}"
        for s in SECTIONS
        if st.session_state["essay_draft"][s].strip()
    )
    if full_essay:
        st.markdown("**📋 Toàn bộ essay:**")
        st.text_area(
            "full_essay_display",
            value=full_essay,
            height=200,
            label_visibility="collapsed",
            key="full_essay_area",
        )
    else:
        st.caption("_Chưa có nội dung nào — hãy viết vào các ô bên trên._")


def render_a2ui(payload: dict) -> None:
    """Động dịch và hiển thị mã A2UI JSON v0.9 bằng streamlit native components."""
    if not payload or "updateComponents" not in payload:
        return
    
    update = payload["updateComponents"]
    components = update.get("components", [])
    
    # Build lookup map by ID
    comp_map = {c["id"]: c for c in components}
    
    # Helper to recursively render components
    def render_node(comp_id: str):
        if comp_id not in comp_map:
            return
        
        comp = comp_map[comp_id]
        comp_type = comp.get("component")
        
        if comp_type == "Column":
            children = comp.get("children", [])
            for child_id in children:
                render_node(child_id)
                
        elif comp_type == "Row":
            children = comp.get("children", [])
            if children:
                cols = st.columns(len(children))
                for idx, child_id in enumerate(children):
                    with cols[idx]:
                        render_node(child_id)
                        
        elif comp_type == "Card":
            children = comp.get("children", [])
            with st.container(border=True):
                for child_id in children:
                    render_node(child_id)
                    
        elif comp_type == "Tabs":
            children = comp.get("children", [])
            if children:
                tab_labels = comp.get("labels", [f"Tab {i+1}" for i in range(len(children))])
                st_tabs = st.tabs(tab_labels)
                for idx, child_id in enumerate(children):
                    with st_tabs[idx]:
                        render_node(child_id)
                        
        elif comp_type == "Text":
            text = comp.get("text", "")
            variant = comp.get("variant", "body")
            if variant == "h1":
                st.subheader(text)
            elif variant == "h2":
                st.markdown(f"##### {text}")
            elif variant == "h3":
                st.markdown(f"###### {text}")
            elif variant == "caption":
                st.caption(text)
            else:
                st.write(text)
                
        elif comp_type == "Divider":
            st.divider()
            
        elif comp_type == "Button":
            label_id = comp.get("child")
            label_text = comp_map.get(label_id, {}).get("text", "Button") if label_id else "Button"
            action = comp.get("action", {})
            event_name = action.get("event", {}).get("name", "")
            
            if st.button(label_text, key=f"a2ui_{comp_id}"):
                st.session_state["a2ui_event"] = event_name
                st.rerun()
                
        elif comp_type == "Image":
            src = comp.get("src", "")
            st.image(src)
            
        elif comp_type == "Icon":
            name = comp.get("name", "")
            st.write(f"Icon: {name}")

    if "root" in comp_map:
        render_node("root")
    elif components:
        render_node(components[0]["id"])


def _render_standard_evaluation(eval_result: dict, essay_type: str, word_count: int) -> None:
    overall_band = eval_result["overall_band"]
    criteria = eval_result["criteria"]
    words = eval_result.get("word_count", word_count)

    # Overall Band display
    st.subheader("🏆 Kết quả đánh giá chung")
    st.metric(label="Overall Band Score", value=f"{overall_band} / 6.5")
    st.progress(overall_band / 6.5)
    st.caption(f"Tổng số từ đã chấm: **{words} từ** | Dạng đề: **{essay_type.replace('_', ' ').title()}**")
    
    st.divider()

    # Detailed criteria scores
    st.subheader("🎯 Điểm số chi tiết theo tiêu chí")
    criteria_labels = {
        "task_response": "Task Response (Đáp ứng yêu cầu)",
        "coherence_cohesion": "Coherence & Cohesion (Mạch lạc & Liên kết)",
        "lexical_resource": "Lexical Resource (Từ vựng)",
        "grammatical_range": "Grammatical Range (Ngữ pháp)"
    }

    for key, label in criteria_labels.items():
        crit_data = criteria.get(key, {})
        band = crit_data.get("band", 1.0)
        
        st.markdown(f"**{label}: {band} / 6.5**")
        st.progress(band / 6.5)
        
        with st.expander(f"🔍 Xem nhận xét tiêu chí {label.split(' (')[0]}", expanded=False):
            st.markdown(f"**Nhận xét:** {crit_data.get('feedback', '')}")
            st.markdown("**Gợi ý cải thiện:**")
            suggestions = crit_data.get("suggestions", [])
            if suggestions:
                for sug in suggestions:
                    st.write(f"- {sug}")
            else:
                st.write("_Không có gợi ý cụ thể._")
        st.write("")

    st.divider()


def _render_evaluation_tab() -> None:
    st.markdown("#### 📊 Đánh giá bài viết (IELTS Band 1.0 – 6.5)")
    st.caption("Chấm điểm bài viết của bạn dựa trên thang rubric rút gọn của IELTS Writing Task 2.")

    # 1. Combine draft text and calculate word count
    combined_text = "\n\n".join(
        st.session_state["essay_draft"][s].strip()
        for s in SECTIONS
        if st.session_state["essay_draft"][s].strip()
    )
    word_count = len(combined_text.split())

    # Calculate cache key
    essay_type = st.session_state.get("essay_type", "opinion")
    cache_key = hashlib.sha256((combined_text + essay_type).encode("utf-8")).hexdigest()

    # 2. Check if already evaluated
    eval_result = st.session_state.get("essay_evaluation")

    # Render word count warning if < 50
    can_evaluate = word_count >= 50

    if not can_evaluate:
        st.warning(f"⚠️ Cần tối thiểu 50 từ để chấm điểm (hiện tại: {word_count} từ). Hãy viết thêm trong tab 'Bài viết'.")

    # Display evaluation interface
    if not eval_result:
        # State: Not evaluated yet
        st.markdown(
            "_Hãy hoàn thành bài viết của bạn bên tab 'Bài viết' rồi nhấn nút dưới đây để nhận đánh giá chi tiết._"
        )
        if st.button("📊 Chấm điểm bài viết", key="btn_eval_initial", disabled=not can_evaluate):
            # Check cache first
            if cache_key in st.session_state["evaluation_cache"]:
                st.session_state["essay_evaluation"] = st.session_state["evaluation_cache"][cache_key]
                st.rerun()
            else:
                with st.spinner("Hệ thống đang chấm điểm bài viết của bạn..."):
                    result = evaluate_essay(combined_text, essay_type)
                    if result.get("error"):
                        st.error(result.get("message"))
                    else:
                        st.session_state["essay_evaluation"] = result
                        st.session_state["evaluation_cache"][cache_key] = result
                        st.rerun()
    else:
        # State: Already evaluated. Try rendering using A2UI if available.
        if eval_result.get("ui_available") and eval_result.get("ui"):
            try:
                render_a2ui(eval_result["ui"])
            except Exception as e:
                # Fallback to standard dashboard rendering if rendering fails
                st.error(f"Lỗi giải mã A2UI: {e}. Chuyển sang hiển thị mặc định.")
                _render_standard_evaluation(eval_result, essay_type, word_count)
        else:
            _render_standard_evaluation(eval_result, essay_type, word_count)

        # Re-evaluate button
        if st.button("🔄 Chấm điểm lại", key="btn_eval_re", disabled=not can_evaluate):
            if cache_key in st.session_state["evaluation_cache"]:
                st.session_state["essay_evaluation"] = st.session_state["evaluation_cache"][cache_key]
                st.toast("Bài viết chưa thay đổi, hiển thị kết quả gần nhất.", icon="ℹ️")
                st.rerun()
            else:
                with st.spinner("Hệ thống đang chấm điểm lại bài viết của bạn..."):
                    result = evaluate_essay(combined_text, essay_type)
                    if result.get("error"):
                        st.error(result.get("message"))
                    else:
                        st.session_state["essay_evaluation"] = result
                        st.session_state["evaluation_cache"][cache_key] = result
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Main layout
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    _init_state()
    _render_sidebar()

    # 3-column layout: chat (wider) | result panel
    col_chat, col_panel = st.columns([3, 2], gap="medium")

    _render_chat(col_chat)

    with col_panel:
        st.markdown("### 📖 Kết quả")
        tab_guide, tab_essay, tab_eval = st.tabs(["💡 Hướng dẫn", "📝 Bài viết", "📊 Chấm điểm"])
        with tab_guide:
            _render_guidance_tab()
        with tab_essay:
            _render_essay_tab()
        with tab_eval:
            _render_evaluation_tab()


if __name__ == "__main__":
    main()
