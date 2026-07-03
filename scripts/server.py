"""
FastAPI Server — IELTS Writing Coach Backend
============================================
Exposes API endpoints for React frontend:
- POST /api/chat: runs ADK Agent turn
- POST /api/evaluate: evaluates IELTS Writing Task 2 essay
- GET /api/health: health check endpoint

Run:
    MOCK_GEMINI=1 python3 scripts/server.py
"""

import os
import sys
import asyncio
from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add scripts directory to path to resolve local imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Forward API Key for ADK
api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    os.environ.setdefault("GOOGLE_API_KEY", api_key)

# Lazy imports of agent and tools
from agent import create_runner, ensure_session
from tools import evaluate_essay
from google.genai import types as genai_types

app = FastAPI(title="IELTS Writing Coach Backend")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate a single global ADK runner
# It handles session indexing and keeps track of history internally
runner = create_runner()

# Pydantic schemas for requests
class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str = "react_user"
    level: str = "B1"

class EvaluateRequest(BaseModel):
    essay_text: str
    essay_type: str

# Async runner logic
async def _run_turn_structured_real(
    session_id: str, user_id: str, message: str
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

    agent_text = "".join(text_chunks)
    if not agent_text and not tool_calls:
        agent_text = "_(Agent không trả lời — vui lòng thử lại hoặc diễn đạt lại câu hỏi.)_"

    return {"text": agent_text, "tool_calls": tool_calls}


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat endpoint to send a message to the ADK agent."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Prepend level tag so the agent knows user's band level
    prefixed_input = f"[Level: {req.level}] {req.message}"
    
    try:
        result = await _run_turn_structured_real(req.session_id, req.user_id, prefixed_input)
        return result
    except Exception as exc:
        err_type = type(exc).__name__
        err_str = str(exc)
        print(f"[ERROR] FastAPI /api/chat — {err_type}: {err_str}", flush=True)
        
        friendly = f"⚠️ Đã xảy ra lỗi kỹ thuật ({err_type}). Vui lòng thử lại."
        if "429" in err_str or "ResourceExhausted" in err_type:
            friendly = "⚠️ Đã vượt giới hạn quota API. Vui lòng thử lại sau vài phút."
        elif "503" in err_str or "ServiceUnavailable" in err_type or "overloaded" in err_str.lower():
            friendly = "⚠️ Server AI đang quá tải (503). Vui lòng đợi 1-2 phút rồi thử lại."
        elif "NotFound" in err_type or "404" in err_str:
            friendly = "⚠️ Lỗi kết nối tới mô hình AI (404). Vui lòng kiểm tra lại API key."

        return {"text": friendly, "tool_calls": []}


@app.post("/api/evaluate")
def evaluate_endpoint(req: EvaluateRequest):
    """Evaluate endpoint to score the essay and return rubrics & A2UI layout."""
    if not req.essay_text.strip():
        raise HTTPException(status_code=400, detail="Essay text cannot be empty")
    
    try:
        result = evaluate_essay(req.essay_text, req.essay_type)
        return result
    except Exception as exc:
        err_type = type(exc).__name__
        print(f"[ERROR] FastAPI /api/evaluate — {err_type}: {exc}", flush=True)
        return {"error": True, "message": f"Lỗi chấm điểm: {err_type}"}


@app.get("/api/health")
def health_endpoint():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # Listen on port 8000 by default
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
