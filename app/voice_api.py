"""Voice Conversation Partner — OpenRouter turn-based pipeline.

OpenRouter has no speech-to-speech realtime API, so one spoken turn is:

    mic audio ->  STT (OpenRouter /audio/transcriptions, zh)
              ->  chat LLM (CONVERSATION_MODEL via get_llm, CONVERSATION_SYSTEM_PROMPT)
              ->  TTS (OpenAI /audio/speech — OpenRouter has no TTS model)
              ->  audio played in the browser

Audio flows browser -> this server -> OpenRouter (the OpenRouter key must never
reach the browser, and OpenRouter has no ephemeral tokens). Turn-based payloads
are small and occasional, so proxying them on the small VM is fine.

Reuses the same brain and corpus as the text coach: the reply runs on the same
OpenRouter models, and notable spoken mistakes are logged via
`extract_and_log_error_voice` into the same per-user ChromaDB corpus (source="voice").
"""
import asyncio
import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from openai import OpenAI

import users
from agent import answer_text, extract_and_log_error_voice
from config import (
    CONVERSATION_MODEL,
    OPENROUTER_BASE_URL,
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE,
    get_llm,
    openai_key,
    openrouter_key,
)
from prompts import CONVERSATION_SYSTEM_PROMPT
from web_api import require_user

router = APIRouter()

# Per-user rolling conversation history for voice (separate from the text coach's
# LangGraph memory — voice deliberately uses no tools and its own prompt).
_voice_history: dict = {}
_HISTORY_TURNS = 12  # cap: keep the last N messages so the prompt stays bounded


def _openrouter_client() -> OpenAI:
    # OpenRouter's audio endpoints are OpenAI-compatible, so the openai SDK (already a
    # dependency) drives them by pointing base_url at OpenRouter. Used for STT.
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_key())


def _openai_client() -> OpenAI:
    # TTS goes direct to OpenAI (default base_url) — OpenRouter has no TTS model.
    return OpenAI(api_key=openai_key())


def _system_prompt(user_id: str) -> str:
    hsk = (users.get_profile(user_id) or {}).get("hsk_level")
    prompt = CONVERSATION_SYSTEM_PROMPT
    if hsk and hsk != "unsure":
        prompt += f"\n\nThe learner self-reports their level as {hsk}. Pitch your Mandarin accordingly."
    return prompt


def _transcribe(client: OpenAI, audio_bytes: bytes, filename: str) -> str:
    resp = client.audio.transcriptions.create(
        model=STT_MODEL, file=(filename, audio_bytes), language="zh"
    )
    return (getattr(resp, "text", "") or "").strip()


def _synthesize(client: OpenAI, text: str) -> bytes:
    resp = client.audio.speech.create(
        model=TTS_MODEL, voice=TTS_VOICE, input=text, response_format="mp3"
    )
    return resp.read()  # raw mp3 bytes


async def _reply(user_id: str, user_text: str) -> str:
    """Run one conversational turn on the OpenRouter chat model with rolling history."""
    history = _voice_history.setdefault(user_id, [])
    messages = [SystemMessage(content=_system_prompt(user_id)), *history, HumanMessage(content=user_text)]
    llm = get_llm(CONVERSATION_MODEL, streaming=False)
    resp = await llm.ainvoke(messages)
    answer = answer_text(resp.content) or "……"
    history.extend([HumanMessage(content=user_text), AIMessage(content=answer)])
    del history[:-_HISTORY_TURNS]  # keep only the most recent turns
    return answer


@router.post("/api/voice/turn")
async def voice_turn(audio: UploadFile = File(...), user_id: str = Depends(require_user)):
    """Full spoken turn. Returns both transcripts (for the 汉字 view — the browser
    fetches pīnyīn separately) and the reply audio as base64 mp3."""
    audio_bytes = await audio.read()

    # STT + TTS are blocking HTTP calls; keep them off the event loop. STT runs on
    # OpenRouter; TTS on OpenAI direct (OpenRouter has no TTS model).
    user_text = await asyncio.to_thread(
        _transcribe, _openrouter_client(), audio_bytes, audio.filename or "audio.webm"
    )
    if not user_text:
        return {"user_text": "", "assistant_text": "", "audio_b64": None, "logged": None}

    assistant_text = await _reply(user_id, user_text)
    audio_out = await asyncio.to_thread(_synthesize, _openai_client(), assistant_text)

    # OpenRouter STT returns no confidence signal, so pass None: the source="voice"
    # tag + the extraction guard remain the corpus-pollution protection.
    logged = await extract_and_log_error_voice(user_id, user_text, assistant_text, confidence=None)

    return {
        "user_text": user_text,
        "assistant_text": assistant_text,
        "audio_b64": base64.b64encode(audio_out).decode("ascii"),
        "logged": logged,
    }


@router.post("/api/voice/reset")
def voice_reset(user_id: str = Depends(require_user)):
    """Clear the rolling voice conversation history (start a fresh conversation)."""
    _voice_history.pop(user_id, None)
    return {"ok": True}
