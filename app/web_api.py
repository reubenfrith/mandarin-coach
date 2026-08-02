"""FastAPI routes for the custom web UI: auth, the text coach, profile/stats, pinyin.

Replaces the Chainlit interface. Everything below the UI is reused unchanged:
`build_agent` / `run_agent` (the LangGraph tool-calling coach with its timeout +
fallback safety) and `extract_and_log_error` (the guarded post-turn corpus write).

The coach is stateful per user via LangGraph's in-memory checkpointer, so we cache
one built agent per user in-process and let the browser carry a `thread_id` (its
conversation key) — the single-process design means one cache and one ChromaDB
writer (see app/server.py).
"""
import os
import time

import jwt
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from langchain_core.messages import AIMessage, HumanMessage

import memory
import users
from agent import answer_text, build_agent, extract_and_log_error, run_agent
from tools import _tone_pinyin, pinyin_segments

router = APIRouter()

# One credentials store, one signing secret (the same one Chainlit used).
_JWT_SECRET = os.environ.get("CHAINLIT_AUTH_SECRET", "")
_JWT_ALG = "HS256"
_COOKIE = "coach_session"
_COOKIE_TTL = 60 * 60 * 12  # 12h

# Per-user built coach (primary + fallback graphs, each with its own checkpointer).
_agents: dict = {}


# --------------------------------------------------------------------------- #
# Auth (PyJWT cookie) — shared by the voice router too
# --------------------------------------------------------------------------- #
def issue_cookie(resp, user_id: str) -> None:
    now = int(time.time())
    token = jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + _COOKIE_TTL}, _JWT_SECRET, algorithm=_JWT_ALG
    )
    resp.set_cookie(_COOKIE, token, httponly=True, samesite="lax", max_age=_COOKIE_TTL)


def require_user(request: Request) -> str:
    token = request.cookies.get(_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in.")
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALG])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")


def _profile_note(user_id: str) -> str:
    """The same HSK profile note the Chainlit onboarding produced for the agent."""
    hsk = (users.get_profile(user_id) or {}).get("hsk_level")
    if hsk and hsk != "unsure":
        return f"The learner self-reports their level as {hsk}. Pitch examples and drills accordingly."
    return ""


def _agent_for(user_id: str):
    if user_id not in _agents:
        _agents[user_id] = build_agent(user_id, _profile_note(user_id))
    return _agents[user_id]


# --------------------------------------------------------------------------- #
# Auth + profile routes
# --------------------------------------------------------------------------- #
@router.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate against the existing user store (auto-creates on first login)."""
    if not users.verify_or_create(username, password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    user_id = (username or "").strip().lower()
    profile = users.get_profile(user_id) or {}
    resp = JSONResponse({"ok": True, "user_id": user_id, "hsk_level": profile.get("hsk_level")})
    issue_cookie(resp, user_id)
    return resp


@router.post("/api/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(_COOKIE)
    return resp


@router.get("/api/profile")
def get_profile(user_id: str = Depends(require_user)):
    profile = users.get_profile(user_id) or {}
    return {"user_id": user_id, "hsk_level": profile.get("hsk_level")}


class HskBody(BaseModel):
    hsk_level: str


@router.post("/api/profile")
def set_profile(body: HskBody, user_id: str = Depends(require_user)):
    """Set the learner's HSK level (the onboarding question) and rebuild their agent
    so the new level reaches the system prompt."""
    users.set_hsk_level(user_id, body.hsk_level)
    _agents.pop(user_id, None)  # evict so the profile note is re-spliced
    return {"ok": True, "hsk_level": body.hsk_level}


@router.get("/api/stats")
def stats(user_id: str = Depends(require_user)):
    """Powers the 'welcome back — N logged errors' panel."""
    return memory.error_stats(user_id)


@router.get("/api/errors")
def errors(limit: int = 25, user_id: str = Depends(require_user)):
    """Recent logged errors (newest first) for the Progress view."""
    return {"errors": memory.recent_errors(user_id, max(1, min(limit, 100)))}


# --------------------------------------------------------------------------- #
# Text coach
# --------------------------------------------------------------------------- #
class ChatBody(BaseModel):
    message: str
    thread_id: str


@router.post("/api/chat")
async def chat(body: ChatBody, user_id: str = Depends(require_user)):
    """One coach turn. Reuses run_agent (timeout + fast-model fallback) and then the
    guarded post-turn error extraction, exactly as the Chainlit handler did."""
    agent = _agent_for(user_id)
    answer = await run_agent(agent, body.message, body.thread_id)
    logged = await extract_and_log_error(user_id, body.message, answer)
    return {"answer": answer, "logged": logged}


@router.get("/api/chat/history")
def chat_history(thread_id: str, user_id: str = Depends(require_user)):
    """Best-effort restore of a text-coach conversation after a page reload.

    History lives in the primary graph's in-memory checkpointer (keyed by thread_id),
    so it survives a reload within a server session but not a server restart. If the
    user's agent isn't built yet (fresh process), there is nothing to restore. We return
    only the human turns and the final AI answers — tool-call/observation messages and
    the system prompt are dropped."""
    agent = _agents.get(user_id)
    if agent is None:
        return {"messages": []}
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = agent.primary.get_state(config)
    except Exception:  # noqa: BLE001 — unknown thread / no state → nothing to restore
        return {"messages": []}
    out = []
    for m in (getattr(state, "values", None) or {}).get("messages", []):
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": answer_text(m.content)})
        elif isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
            # Only terminal AI messages are answers; ones carrying tool_calls are the
            # model's pre-tool narration (some models put text there too) — skip them
            # so a restore matches what the live turn actually rendered.
            txt = answer_text(m.content).strip()
            if txt:
                out.append({"role": "assistant", "content": txt})
    return {"messages": out}


@router.get("/api/pinyin")
def pinyin(text: str, user_id: str = Depends(require_user)):
    """Tone-marked pīnyīn for 汉字 (reuses the dictionary tool's pypinyin helper).

    `segments` aligns pīnyīn to each character for the ruby (character-over-pinyin) view;
    `pinyin` stays for any caller that just wants the flat string."""
    return {"text": text, "pinyin": _tone_pinyin(text), "segments": pinyin_segments(text)}
