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
import re

from fastapi import APIRouter, Depends, File, Form, UploadFile
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from openai import OpenAI

import users
from agent import (
    answer_text,
    build_voice_coach,
    classify_turn_intent,
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
from web_api import _profile_note, require_user

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
        # Same HSK profile note the text coach gets, so it pitches to the learner's level.
        _voice_coaches[user_id] = build_voice_coach(user_id, _profile_note(user_id))
    return _voice_coaches[user_id]


# A run of >=2 latin letters = an English word (ignores stray "OK"/"app"-style single tokens
# less, but 2+ letters is a good "this turn is English" signal).
_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")


def _has_han(text: str) -> bool:
    return any("一" <= c <= "鿿" for c in text)


# Question markers that make a Han-only turn AMBIGUOUS (a coaching question like "这个词是什么
#意思？" vs a conversational one like "你呢？"). Their presence sends the turn to the classifier;
# a plain Mandarin statement (no marker) stays on the zero-latency converse fast path.
_ZH_QUESTION_MARKERS = ("吗", "呢", "什么", "为什么", "怎么", "怎样", "哪", "谁",
                        "多少", "几", "如何", "是不是", "有没有", "对不对", "？", "?")

# A pure-English turn with at most this many words is treated as conversational glue ("and you?",
# "me too") and fast-pathed to converse. Anything longer is a possible coaching question and goes
# to the classifier. Tuned on evals/surfaces/voice_coach (the 5 glue cases are all <=2 words; the
# shortest real coaching question is 5) — see evals/notes/voice-router-findings.md.
_ENGLISH_GLUE_MAX_WORDS = 2


def _is_zh_question(text: str) -> bool:
    return any(m in text for m in _ZH_QUESTION_MARKERS)


def _heuristic_route(text: str) -> str | None:
    """The zero-latency routing decision, or None when the turn is genuinely AMBIGUOUS and worth
    a classifier call. Principle: fast-path only what is unambiguous from surface form (a plain
    Mandarin statement, a very short English aside, an empty turn); classify everything else.

    This replaced the old two blunt rules (Latin->coach, Han->converse), which the router eval
    showed caused 100% of misroutes — English glue lectured, Mandarin questions ignored. Biased
    to converse: a coach turn missed here degrades gracefully (the partner corrects inline)."""
    han, latin = _has_han(text), bool(_LATIN_WORD.search(text))
    if not han and not latin:
        return "converse"                       # no real content → don't lecture
    if han and not latin:
        # plain Mandarin statement → converse (the common, instant path); a Mandarin QUESTION is
        # ambiguous (conversational vs coaching) → let the classifier decide.
        return None if _is_zh_question(text) else "converse"
    if latin and not han:
        # short English aside → converse; a longer English turn may be a coaching question → classify.
        return "converse" if len(_LATIN_WORD.findall(text)) <= _ENGLISH_GLUE_MAX_WORDS else None
    return None                                 # mixed script → classifier


async def _route_intent(user_id: str, text: str, mode: str) -> str:
    """Decide which brain answers a spoken turn: 'converse' or 'coach'.

    Manual override wins. Otherwise the zero-latency heuristic resolves the unambiguous turns
    (plain Mandarin statements, short English asides, empty) and only the ambiguous ones —
    Mandarin questions, substantive English, mixed script — cost a classifier call. Biased to
    'converse' throughout: a misrouted chat->coach turn (an English lecture when you wanted to
    talk) is more jarring than the reverse, and the partner still does light inline correction."""
    if mode in ("converse", "coach"):
        return mode
    decided = _heuristic_route(text)
    if decided is not None:
        return decided
    return await classify_turn_intent(text)


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
async def voice_turn(
    audio: UploadFile = File(...),
    mode: str = Form("auto"),
    user_id: str = Depends(require_user),
):
    """Full spoken turn. `mode` is auto|converse|coach (the UI's toggle). Routes the turn to
    the conversation partner or the voice coach, and returns the transcripts (with ruby
    segments), the detected intent, what was spoken, and the reply audio as base64 mp3."""
    audio_bytes = await audio.read()

    # STT is a blocking HTTP call; keep it off the event loop. Auto-detect the language
    # (VOICE_STT_LANGUAGE is None) so an English question transcribes as English — the
    # signal _route_intent reads.
    user_text = await asyncio.to_thread(
        _transcribe, _openai_client(), audio_bytes, audio.filename or "audio.webm",
        VOICE_STT_LANGUAGE,
    )
    if not user_text:
        return {"intent": None, "user_text": "", "assistant_text": "", "spoken_text": "",
                "audio_b64": None, "logged": None}

    intent = await _route_intent(user_id, user_text, mode)

    if intent == "coach":
        # Coach: speak the short TL;DR, show the full explanation. A learning question has
        # no learner error of its own, so nothing is logged.
        spoken, assistant_text = await _coach_reply(user_id, user_text)
        logged = None
    else:
        assistant_text = await _reply(user_id, user_text)
        spoken = assistant_text  # conversation: speak the whole reply
        # STT gives no confidence signal, so pass None: the source="voice" tag + the
        # extraction guard remain the corpus-pollution protection.
        logged = await extract_and_log_error_voice(user_id, user_text, assistant_text, confidence=None)

    audio_out = await asyncio.to_thread(_synthesize, _openai_client(), spoken)

    return {
        "intent": intent,
        "user_text": user_text,
        "assistant_text": assistant_text,
        "spoken_text": spoken,
        # Ruby segments up front so the UI renders 汉字-over-pīnyīn immediately (no second
        # /api/pinyin round-trip per turn, no plain-then-ruby reflow flicker). On an English
        # coach answer these ruby-annotate only the Chinese example sentences.
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
