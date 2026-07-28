"""Voice Conversation Partner — all-OpenAI turn-based pipeline.

There is no speech-to-speech realtime API here, so one spoken turn is:

    mic audio ->  STT (OpenAI /audio/transcriptions, auto-detect language)
              ->  chat LLM (CONVERSATION_MODEL via get_llm — a fast, non-reasoning model)
              ->  TTS (OpenAI /audio/speech)
              ->  audio played in the browser

Every leg runs direct on OPENAI_API_KEY (see config's pipeline note): keeping voice on
one fast provider — and off the reasoning chat models — is the latency fix. Audio flows
browser -> this server -> OpenAI (the key never reaches the browser). Turn-based payloads
are small and occasional, so proxying them on the small VM is fine.

Shares the corpus with the text coach: notable spoken mistakes are logged via
`extract_and_log_error_voice` into the same per-user ChromaDB corpus (source="voice").
"""
import asyncio
import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from openai import OpenAI

import users
from agent import (
    answer_text,
    build_voice_coach,
    extract_and_log_error_voice,
    run_voice_coach,
)
from tools import pinyin_segments
from config import (
    CONVERSATION_MODEL,
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE,
    VOICE_STT_LANGUAGE,
    get_llm,
    openai_key,
)
from prompts import CONVERSATION_SYSTEM_PROMPT
from web_api import require_user

router = APIRouter()

# Per-user rolling spoken history — the SINGLE canonical log for the voice session,
# shared by BOTH brains (conversation partner + voice coach) so a coaching question can
# see the recast the partner just made, and conversation resumes after a coaching detour.
# Each entry: {"role": "user"|"assistant", "content": str, "mode": "converse"|"coach"}.
# Kept separate from the text coach's LangGraph memory (the decision: voice owns its
# context). The mode tag lets us keep coaching detours from derailing the chat.
_voice_history: dict = {}
_HISTORY_TURNS = 12  # cap: keep the last N entries so the prompt stays bounded

# One stateless voice-coach graph per user, built lazily (make_tools loads dictionaries,
# so we don't want to rebuild it every turn).
_voice_coaches: dict = {}


def _history(user_id: str) -> list:
    return _voice_history.setdefault(user_id, [])


def _remember(user_id: str, role: str, content: str, mode: str) -> None:
    h = _history(user_id)
    h.append({"role": role, "content": content, "mode": mode})
    del h[:-_HISTORY_TURNS]


def _history_messages(user_id: str) -> list:
    """The recent spoken turns as LangChain messages, for prompting either brain."""
    return [
        HumanMessage(content=t["content"]) if t["role"] == "user"
        else AIMessage(content=t["content"])
        for t in _history(user_id)
    ]


def _openai_client() -> OpenAI:
    # The whole voice pipeline (STT + TTS) runs direct on OpenAI — see config's pipeline note.
    return OpenAI(api_key=openai_key())


def _coach_for(user_id: str):
    if user_id not in _voice_coaches:
        _voice_coaches[user_id] = build_voice_coach(user_id)
    return _voice_coaches[user_id]


def _system_prompt(user_id: str) -> str:
    hsk = (users.get_profile(user_id) or {}).get("hsk_level")
    prompt = CONVERSATION_SYSTEM_PROMPT
    if hsk and hsk != "unsure":
        prompt += f"\n\nThe learner self-reports their level as {hsk}. Pitch your Mandarin accordingly."
    return prompt


def _transcribe(client: OpenAI, audio_bytes: bytes, filename: str, language: str | None = None) -> str:
    """Transcribe one clip. `language` is an ISO-639-1 hint; pass None to auto-detect
    (the voice coach does this so an English question isn't forced into Chinese). The
    caller reads the transcript's script to decide intent — gpt-4o-mini-transcribe has
    no verbose_json/detected-language field, so the script is our language signal."""
    kwargs = {"model": STT_MODEL, "file": (filename, audio_bytes)}
    if language:
        kwargs["language"] = language
    resp = client.audio.transcriptions.create(**kwargs)
    return (getattr(resp, "text", "") or "").strip()


def _synthesize(client: OpenAI, text: str) -> bytes:
    resp = client.audio.speech.create(
        model=TTS_MODEL, voice=TTS_VOICE, input=text, response_format="mp3"
    )
    return resp.read()  # raw mp3 bytes


async def _reply(user_id: str, user_text: str) -> str:
    """One conversational turn on the fast voice model, over the shared spoken history."""
    messages = [SystemMessage(content=_system_prompt(user_id)),
                *_history_messages(user_id), HumanMessage(content=user_text)]
    llm = get_llm(CONVERSATION_MODEL, streaming=False)
    resp = await llm.ainvoke(messages)
    answer = answer_text(resp.content) or "……"
    _remember(user_id, "user", user_text, "converse")
    _remember(user_id, "assistant", answer, "converse")
    return answer


async def _coach_reply(user_id: str, question: str) -> tuple[str, str]:
    """One voice-COACH turn. Runs the bounded agentic brain over the same shared history
    (so it can see the correction being asked about) and returns (spoken, full). Only the
    short spoken line is written back to history — the full explanation stays in the UI, so
    a long English answer doesn't bloat the log or drift the next chat turn into English."""
    spoken, full = await run_voice_coach(_coach_for(user_id), _history_messages(user_id), question)
    _remember(user_id, "user", question, "coach")
    _remember(user_id, "assistant", spoken, "coach")
    return spoken, full


@router.post("/api/voice/turn")
async def voice_turn(audio: UploadFile = File(...), user_id: str = Depends(require_user)):
    """Full spoken turn. Returns both transcripts (for the 汉字 view — the browser
    fetches pīnyīn separately) and the reply audio as base64 mp3."""
    audio_bytes = await audio.read()

    # STT + TTS are blocking HTTP calls; keep them off the event loop. STT runs on
    # OpenRouter; TTS on OpenAI direct (OpenRouter has no TTS model).
    # Auto-detect the spoken language (VOICE_STT_LANGUAGE is None by default) so an English
    # clarifying question transcribes as English — the signal the intent router reads.
    user_text = await asyncio.to_thread(
        _transcribe, _openai_client(), audio_bytes, audio.filename or "audio.webm",
        VOICE_STT_LANGUAGE,
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
        # Ruby segments up front so the UI renders 汉字-over-pīnyīn immediately (no
        # second /api/pinyin round-trip per turn, no plain-then-ruby reflow flicker).
        "user_segments": pinyin_segments(user_text),
        "assistant_segments": pinyin_segments(assistant_text),
        "audio_b64": base64.b64encode(audio_out).decode("ascii"),
        "logged": logged,
    }


@router.post("/api/voice/reset")
def voice_reset(user_id: str = Depends(require_user)):
    """Clear the rolling voice conversation history (start a fresh conversation)."""
    _voice_history.pop(user_id, None)
    return {"ok": True}
