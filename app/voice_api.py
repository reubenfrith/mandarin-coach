"""FastAPI router for the voice Conversation Partner.

Mounted into `app/server.py` in the SAME process as the Chainlit text coach, so
there is exactly one ChromaDB writer and one user-DB owner. Imports are BARE
(`import memory`, `from agent import ...`) to share the single module graph that
`main.py` sets up via `sys.path.insert` — see `app/server.py`.

The heavy lifting (audio) never touches this server: the browser streams audio
directly to OpenAI over WebRTC. This router only (a) authenticates against the
existing user store and mints a short-lived OpenAI ephemeral token, (b) logs
spoken turns into the existing per-user error corpus, and (c) annotates 汉字 with
pīnyīn for the transcript UI.
"""
import os
import time

import jwt
import requests
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import users
from agent import extract_and_log_error_voice
from config import REALTIME_MODEL, REALTIME_VOICE
from prompts import CONVERSATION_SYSTEM_PROMPT
from tools import _tone_pinyin

router = APIRouter()

# One credentials store across both UIs: sign the voice session cookie with the
# same secret Chainlit uses, so there is a single auth bridge (see README).
_JWT_SECRET = os.environ.get("CHAINLIT_AUTH_SECRET", "")
_JWT_ALG = "HS256"
_COOKIE = "voice_session"
_COOKIE_TTL = 60 * 60 * 12  # 12h; the OpenAI ephemeral token is separate and ~60s

_OPENAI_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"


# --------------------------------------------------------------------------- #
# Auth bridge (PyJWT cookie signed with CHAINLIT_AUTH_SECRET)
# --------------------------------------------------------------------------- #
def _issue_cookie(resp: Response, user_id: str) -> None:
    now = int(time.time())
    token = jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + _COOKIE_TTL}, _JWT_SECRET, algorithm=_JWT_ALG
    )
    resp.set_cookie(_COOKIE, token, httponly=True, samesite="lax", max_age=_COOKIE_TTL)


def require_user(request: Request) -> str:
    """Decode the voice session cookie; 401 if missing/invalid/expired."""
    token = request.cookies.get(_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in.")
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALG])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return payload["sub"]


@router.post("/voice/login")
def voice_login(username: str = Form(...), password: str = Form(...)):
    """Authenticate against the existing user store (auto-creates on first login,
    exactly like the text coach), then set a signed session cookie."""
    if not users.verify_or_create(username, password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    user_id = (username or "").strip().lower()
    resp = JSONResponse({"ok": True, "user_id": user_id})
    _issue_cookie(resp, user_id)
    return resp


# --------------------------------------------------------------------------- #
# Realtime ephemeral token (server holds the real OPENAI_API_KEY)
# --------------------------------------------------------------------------- #
def _instructions_for(user_id: str) -> str:
    """The conversation-partner system prompt with the learner's HSK level spliced in."""
    profile = users.get_profile(user_id) or {}
    hsk = profile.get("hsk_level")
    prompt = CONVERSATION_SYSTEM_PROMPT
    if hsk and hsk != "unsure":
        prompt += f"\n\nThe learner self-reports their level as {hsk}. Pitch your Mandarin accordingly."
    return prompt


@router.get("/realtime/session")
def realtime_session(user_id: str = Depends(require_user)):
    """Mint a short-lived OpenAI ephemeral token (called just-in-time by the browser,
    since these expire in ~60s). Session config — model, voice, transcription, turn
    detection, and the per-user Mandarin instructions — is attached to the secret.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("#"):
        raise HTTPException(status_code=503, detail="Voice unavailable: OPENAI_API_KEY not configured.")

    session_config = {
        "type": "realtime",
        "model": REALTIME_MODEL,
        "instructions": _instructions_for(user_id),
        "output_modalities": ["audio", "text"],  # text so we get assistant transcripts
        "audio": {
            "input": {
                "turn_detection": {"type": "semantic_vad"},
                "transcription": {"language": "zh"},
            },
            "output": {"voice": REALTIME_VOICE},
        },
        # Ask for transcription logprobs so /voice/log-turn can gate on STT confidence.
        "include": ["item.input_audio_transcription.logprobs"],
    }
    try:
        r = requests.post(
            _OPENAI_CLIENT_SECRETS_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"session": session_config},
            timeout=15,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        detail = getattr(e.response, "text", str(e)) if getattr(e, "response", None) else str(e)
        raise HTTPException(status_code=502, detail=f"Realtime token mint failed: {detail}")

    data = r.json()
    # Response shape has varied ("value" at top level vs nested client_secret); pass the
    # whole payload through and let the browser read the ephemeral value, plus the model
    # it should connect the WebRTC call with.
    return {"client_secret": data, "model": REALTIME_MODEL}


# --------------------------------------------------------------------------- #
# Post-turn logging + pinyin for the transcript UI
# --------------------------------------------------------------------------- #
@router.post("/voice/log-turn")
async def voice_log_turn(request: Request, user_id: str = Depends(require_user)):
    """Fire-and-forget (from the UI's view) logging of one spoken exchange into the
    same per-user error corpus as the text coach, tagged source="voice"."""
    body = await request.json()
    logged = await extract_and_log_error_voice(
        user_id,
        body.get("user_text", ""),
        body.get("assistant_text", ""),
        confidence=body.get("confidence"),
    )
    return {"logged": logged}


@router.get("/voice/pinyin")
def voice_pinyin(text: str, user_id: str = Depends(require_user)):
    """Tone-marked pīnyīn for 汉字, so the transcript UI can show both without a JS
    pinyin lib. Reuses the same pypinyin helper the dictionary tool uses."""
    return {"text": text, "pinyin": _tone_pinyin(text)}
