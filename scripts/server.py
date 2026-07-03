"""
FastAPI Server — IELTS Writing Coach Backend (Reboot: 2026-07-03)
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

# Lazy imports of agent and tools
from agent import create_runner, ensure_session
from tools import evaluate_essay
from google.genai import types as genai_types

app = FastAPI(title="IELTS Writing Coach Backend")

import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse

# Simple in-memory sliding window rate limiter to protect the API from spam bots
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 10  # Max 10 requests per minute per IP

ip_request_history = defaultdict(list)

@app.middleware("http")
async def check_rate_limit(request: Request, call_next):
    path = request.url.path
    if path in ["/api/chat", "/api/evaluate"]:
        # Get client IP (support Hugging Face / Vercel proxies)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        # Clean up older timestamps
        ip_request_history[client_ip] = [
            ts for ts in ip_request_history[client_ip]
            if now - ts < RATE_LIMIT_WINDOW_SECONDS
        ]

        if len(ip_request_history[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            # Block request immediately
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "text": "⚠️ Bạn đang gửi quá nhiều yêu cầu. Vui lòng đợi 1 phút trước khi tiếp tục.",
                    "message": "⚠️ Bạn đang gửi quá nhiều yêu cầu. Vui lòng đợi 1 phút trước khi tiếp tục."
                }
            )

        # Record request timestamp
        ip_request_history[client_ip].append(now)

    response = await call_next(request)
    return response

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
    history: list[dict] = []

class EvaluateRequest(BaseModel):
    essay_text: str
    essay_type: str

# Async runner logic
async def _run_turn_structured_real(
    session_id: str, user_id: str, message: str, history: list[dict] = []
) -> dict:
    await ensure_session(runner, user_id, session_id)
    
    # Sync frontend history to memory if empty (e.g., page reload or backend container restart)
    session = await runner.session_service.get_session(
        app_name="essay_writing_coach",
        user_id=user_id,
        session_id=session_id
    )
    if session and (not session.events) and history:
        import uuid
        import time
        from google.adk.events.event import Event
        
        for h_msg in history:
            role = h_msg.get("role", "user")
            content_role = "user" if role == "user" else "model"
            author = "user" if role == "user" else "model"
            content_text = h_msg.get("content", "")
            if not content_text:
                continue
                
            event = Event(
                id=str(uuid.uuid4()),
                invocation_id=f"e-{uuid.uuid4()}",
                author=author,
                timestamp=time.time(),
                content=genai_types.Content(
                    role=content_role,
                    parts=[genai_types.Part.from_text(text=content_text)]
                )
            )
            session.events.append(event)
            
    msg = genai_types.Content(
        role="user", parts=[genai_types.Part(text=message)]
    )
    agent_text = ""
    tool_calls: list[dict] = []

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=msg
    ):
        if not (event.content and event.content.parts):
            continue
            
        # Overwrite agent_text with the cumulative text parts from the latest event to prevent duplicate prints
        chunks = []
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not getattr(part, "thought", False):
                chunks.append(part.text)
        agent_text = "".join(chunks)

        for part in event.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                # Avoid inserting duplicate tool calls
                if not any(tc["tool"] == fc.name for tc in tool_calls):
                    tool_calls.append({"tool": fc.name, "args": dict(fc.args) if fc.args else {}, "result": None})
            if hasattr(part, "function_response") and part.function_response:
                fr = part.function_response
                for tc in reversed(tool_calls):
                    if tc["tool"] == fr.name and tc["result"] is None:
                        tc["result"] = dict(fr.response) if fr.response else {}
                        break
                else:
                    # Avoid duplicate response tool logs
                    if not any(tc["tool"] == fr.name and tc["result"] is not None for tc in tool_calls):
                        tool_calls.append({"tool": fr.name, "args": {}, "result": dict(fr.response) if fr.response else {}})

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
        result = await _run_turn_structured_real(req.session_id, req.user_id, prefixed_input, req.history)
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

@app.get("/")
def index_endpoint():
    return {
        "status": "healthy",
        "service": "IELTS Writing Coach Backend",
        "description": "FastAPI AI Agent endpoints are ready under /api/chat and /api/evaluate"
    }



if __name__ == "__main__":
    import uvicorn
    # Listen on port 8000 by default
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
