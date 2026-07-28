"""The coaching agent — built with LangGraph.

Uses LangGraph's prebuilt tool-calling agent (`create_agent`, the LangGraph 1.0
successor to `create_react_agent`). LangGraph runs the decide -> call tools ->
observe -> answer loop as a graph, gives us a MemorySaver checkpointer for
per-conversation memory (keyed by thread_id), and produces a single grouped
LangSmith trace per turn.

The model is ChatLiteLLM (via OpenRouter), so every graph run is traced by
LangSmith when LANGSMITH_TRACING is set.
"""
import asyncio
import os
from collections import namedtuple

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

import memory
from typing import Literal

from config import CONVERSATION_MODEL, DEFAULT_MODEL, FALLBACK_MODEL, get_llm
from prompts import (
    AGENT_SYSTEM_PROMPT,
    ERROR_EXTRACTION_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    SENTENCE_CORRECTION_PROMPT,
    VOICE_COACH_SYSTEM_PROMPT,
)
from tools import make_tools

# Hard ceiling on a whole agent turn (which may chain several LLM + tool calls).
# Generous enough for a legit multi-tool reasoning turn, but bounded so a hung
# provider can't strand the user — on breach we fall back to the fast model.
AGENT_TURN_TIMEOUT = float(os.environ.get("AGENT_TURN_TIMEOUT", "180"))

# A built coach: the primary (reasoning) graph plus a fast fallback graph. Each has
# its own checkpointer so a partially-run primary turn can't corrupt fallback state.
CoachAgent = namedtuple("CoachAgent", ["primary", "fallback"])

# Post-turn extraction guard (see root README, Task 6.3). The OpenRouter models
# intermittently return had_error=True with correction/category/explanation dropped
# together, or malformed JSON that raises — provider-side non-determinism, not a
# capability limit. Either would silently poison the error corpus, so the extraction
# call is retried a bounded number of times and only a complete record is ever logged.
EXTRACTION_MAX_ATTEMPTS = int(os.environ.get("EXTRACTION_MAX_ATTEMPTS", "3"))
# Per-attempt hard bound: the default extraction model can hang (DECISIONS #4) and
# litellm's own timeout does not reliably interrupt it, so each attempt is wrapped so
# the retry loop can't compound a hang across this post-turn write.
EXTRACTION_TIMEOUT = float(os.environ.get("EXTRACTION_TIMEOUT", "60"))

VALID_CATEGORIES = {
    "grammar", "word_order", "measure_word", "particle", "vocabulary", "tones"
}


def answer_text(content) -> str:
    """Extract user-facing text from a message, dropping reasoning-model thinking blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return ""


def _build_graph(user_id: str, prompt: str, model_key: str, *, checkpointer=None):
    """One LangGraph tool-calling graph on `model_key`. With a checkpointer it keeps
    per-thread state (the text coach); without one it is stateless — each invoke sees
    only the messages you pass (the voice coach, which injects its own history)."""
    return create_agent(
        get_llm(model_key, streaming=False),
        make_tools(user_id),
        system_prompt=prompt,
        **({"checkpointer": checkpointer} if checkpointer is not None else {}),
    )


def build_agent(user_id: str, profile_note: str = "") -> CoachAgent:
    """Build the coach for one user: a primary (reasoning) graph plus a fast fallback.

    Each graph's MemorySaver checkpointer keeps per-conversation state keyed by
    thread_id, so each turn only needs the new message (LangGraph reloads history).
    """
    prompt = AGENT_SYSTEM_PROMPT + (f"\n\n{profile_note}" if profile_note else "")
    return CoachAgent(
        primary=_build_graph(user_id, prompt, DEFAULT_MODEL, checkpointer=MemorySaver()),
        fallback=_build_graph(user_id, prompt, FALLBACK_MODEL, checkpointer=MemorySaver()),
    )


# --------------------------------------------------------------------------- #
# Voice coach (Phase 1) — the agentic brain, bounded for a live spoken turn.
# Same tools as the text coach, but a fast non-reasoning model, a tight timeout, and
# a low tool-call ceiling: the learner is holding the mic waiting for audio. It is
# STATELESS (no checkpointer) — voice_api injects the recent spoken history as the
# message list, so voice keeps its own context instead of the LangGraph thread's.
# --------------------------------------------------------------------------- #
VOICE_COACH_MODEL = os.environ.get("VOICE_COACH_MODEL", CONVERSATION_MODEL)
VOICE_COACH_TIMEOUT = float(os.environ.get("VOICE_COACH_TIMEOUT", "45"))
# LangGraph counts every LLM + tool step against this; a spoken answer should resolve
# in a couple of tool calls, so keep it low to bound worst-case latency.
VOICE_COACH_RECURSION_LIMIT = int(os.environ.get("VOICE_COACH_RECURSION_LIMIT", "8"))


def build_voice_coach(user_id: str, profile_note: str = ""):
    """A stateless voice-coach graph for one user (see the section note above)."""
    prompt = VOICE_COACH_SYSTEM_PROMPT + (f"\n\n{profile_note}" if profile_note else "")
    return _build_graph(user_id, prompt, VOICE_COACH_MODEL)


def _split_spoken(full_text: str) -> tuple[str, str]:
    """VOICE_COACH_SYSTEM_PROMPT asks for `spoken TL;DR` on line 1, detail below. Split
    into (spoken, full): the first line is read aloud, the whole answer is shown."""
    text = (full_text or "").strip()
    if not text:
        return "……", ""
    first = text.split("\n", 1)[0].strip()
    return (first or text), text


# Only the AMBIGUOUS (mixed-script) case reaches this LLM call — pure-English and
# pure-Chinese turns are routed by a zero-latency script heuristic in voice_api. Kept
# short so it barely adds to turn latency, and biased to 'converse' on any failure.
VOICE_INTENT_TIMEOUT = float(os.environ.get("VOICE_INTENT_TIMEOUT", "12"))


class TurnIntent(BaseModel):
    """Which voice brain should handle one spoken turn."""

    intent: Literal["converse", "coach"] = Field(
        description="'coach' for a question/explanation request about the language or a "
        "correction; 'converse' for ordinary conversation."
    )


async def classify_turn_intent(text: str) -> str:
    """Classify a mixed-language spoken turn as 'converse' or 'coach'. Uses the fast voice
    model; on timeout or any error returns 'converse' (precision-first: don't lecture when
    the learner wanted to chat)."""
    llm = get_llm(CONVERSATION_MODEL, streaming=False).with_structured_output(TurnIntent)
    try:
        result = await asyncio.wait_for(
            llm.ainvoke(
                [SystemMessage(content=INTENT_CLASSIFIER_PROMPT), HumanMessage(content=text)]
            ),
            timeout=VOICE_INTENT_TIMEOUT,
        )
        return result.intent
    except Exception as e:  # noqa: BLE001 — timeout/malformed → safe default
        print(f"[classify_turn_intent] failed: {type(e).__name__}: {e}; defaulting to converse")
        return "converse"


async def run_voice_coach(graph, history_messages: list, question: str) -> tuple[str, str]:
    """One bounded voice-coach turn. Injects the recent spoken history as the message
    list (stateless graph, so only these messages count) and returns (spoken, full).
    On timeout/error returns a short spoken apology for BOTH so the turn still speaks."""
    messages = [*history_messages, HumanMessage(content=question)]
    config = {"recursion_limit": VOICE_COACH_RECURSION_LIMIT}
    try:
        result = await asyncio.wait_for(
            graph.ainvoke({"messages": messages}, config=config),
            timeout=VOICE_COACH_TIMEOUT,
        )
        return _split_spoken(answer_text(result["messages"][-1].content))
    except Exception as e:  # noqa: BLE001 — timeout OR any provider/tool error → speak an apology
        print(f"[run_voice_coach] failed: {type(e).__name__}: {e}")
        msg = "Sorry — I couldn't work that one out just now. Could you ask again?"
        return msg, msg


async def _invoke(graph, user_input: str, config) -> str:
    result = await asyncio.wait_for(
        graph.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=config),
        timeout=AGENT_TURN_TIMEOUT,
    )
    return answer_text(result["messages"][-1].content) or "(no response)"


async def invoke_with_trace(graph, user_input: str, thread_id: str, callbacks=None):
    """Run one turn on a SINGLE graph and return (final_text, raw_message_list).

    Eval-only companion to `run_agent`. `run_agent` returns just the final text and
    silently swaps to the fallback graph on a stall — both are wrong for evaluating
    the agent's tool-use: the RAGAS agentic metrics need the full LangGraph message
    trace (HumanMessage / AIMessage[tool_calls] / ToolMessage), and the trace must
    come from ONE known model (clean provenance), not whichever graph happened to
    answer. So this invokes the graph you hand it directly, still bounded by
    AGENT_TURN_TIMEOUT so a hung provider degrades one case instead of the run.

    Returns the raw *langchain* messages; converting them to `ragas.messages` lives
    in the eval harness so the live app never imports ragas.
    """
    config = {"configurable": {"thread_id": thread_id}}
    if callbacks:
        config["callbacks"] = callbacks
    result = await asyncio.wait_for(
        graph.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=config),
        timeout=AGENT_TURN_TIMEOUT,
    )
    messages = result["messages"]
    return (answer_text(messages[-1].content) or "(no response)"), messages


async def run_agent(agent: CoachAgent, user_input: str, thread_id: str, callbacks=None) -> str:
    """Run one turn on the primary graph; on stall/error fall back to the fast model.

    The whole turn is bounded by AGENT_TURN_TIMEOUT because litellm's own request
    timeout does not reliably interrupt a hung streaming connection (observed: a
    deepseek call ran 34 minutes past a 600s timeout). The fallback guarantees the
    user always gets a response.
    """
    config = {"configurable": {"thread_id": thread_id}}
    if callbacks:
        config["callbacks"] = callbacks
    try:
        return await _invoke(agent.primary, user_input, config)
    except Exception as e:  # noqa: BLE001 — timeout OR any provider error → fall back
        print(f"[run_agent] primary ({DEFAULT_MODEL}) failed: {type(e).__name__}: {e}; "
              f"falling back to {FALLBACK_MODEL}")
    try:
        return await _invoke(agent.fallback, user_input, config)
    except Exception as e:  # noqa: BLE001 — both models down
        print(f"[run_agent] fallback ({FALLBACK_MODEL}) also failed: {type(e).__name__}: {e}")
        return "Sorry — I'm having trouble reaching the model right now. Please try again in a moment."


# --------------------------------------------------------------------------- #
# Post-turn error logging (structured extraction) — unchanged
# --------------------------------------------------------------------------- #
class ErrorExtraction(BaseModel):
    """Structured record of the single most important error in the learner's input."""

    had_error: bool = Field(
        description="True only if the learner's Chinese input contained a correctable error"
    )
    original: str = Field(default="", description="The learner's original erroneous Chinese")
    correction: str = Field(default="", description="The corrected Chinese sentence")
    category: str = Field(
        default="",
        description="One of: grammar, word_order, measure_word, particle, vocabulary, tones",
    )
    explanation: str = Field(default="", description="Brief root cause, in English")


def _has_chinese(text: str) -> bool:
    return any("一" <= c <= "鿿" for c in text)


def _record_complete(rec: ErrorExtraction) -> bool:
    """True only for a record safe to log: an error with BOTH the original and its
    correction present. `had_error=True` with an empty correction is exactly the
    field-drop failure mode (DECISIONS #13) — logging it would poison the corpus, so
    it counts as incomplete and drives a retry."""
    return bool(rec.had_error and rec.original.strip() and rec.correction.strip())


async def _extract_record(
    user_input: str, agent_answer: str, model: str | None = None
) -> ErrorExtraction:
    """One structured-extraction call, bounded by EXTRACTION_TIMEOUT. Raises on a hung
    provider (timeout) or malformed output (e.g. null string fields); callers decide
    whether to retry. Shared by the production guard and the eval sibling below."""
    llm = get_llm(model, streaming=False) if model else get_llm(streaming=False)
    structured = llm.with_structured_output(ErrorExtraction)
    return await asyncio.wait_for(
        structured.ainvoke(
            [
                SystemMessage(content=ERROR_EXTRACTION_PROMPT),
                HumanMessage(
                    content=f"Learner input:\n{user_input}\n\nCoach reply:\n{agent_answer}"
                ),
            ]
        ),
        timeout=EXTRACTION_TIMEOUT,
    )


async def extract_and_log_error(user_id: str, user_input: str, agent_answer: str):
    """Extract the learner's error (if any) and log it so the corpus grows from use.

    Guarded against the documented structured-output flakiness (DECISIONS #13):
      * a `had_error=True` record whose correction was dropped, or a call that raises
        (malformed JSON / hung provider), is retried up to EXTRACTION_MAX_ATTEMPTS;
      * a confident `had_error=False` is trusted immediately — a correct sentence is a
        valid result, not a failure, so there is nothing to retry or log;
      * if no complete record is ever obtained, NOTHING is logged. This preserves the
        original fail-safe: the corpus only ever gains full, usable records.
    """
    if not _has_chinese(user_input):
        return None

    rec: ErrorExtraction | None = None
    for _ in range(EXTRACTION_MAX_ATTEMPTS):
        try:
            candidate = await _extract_record(user_input, agent_answer)
        except Exception:  # noqa: BLE001 — timeout/hang OR malformed output → retry
            continue
        if not candidate.had_error:
            return None  # confident clean sentence — nothing to log, no point retrying
        rec = candidate  # remember the latest error record in case none is ever complete
        if _record_complete(candidate):
            break  # full record — stop retrying
        # else: fields were dropped this attempt — try again for a complete one

    if rec is None or not _record_complete(rec):
        return None  # never got a loggable record — fail safe (protect the corpus)

    category = rec.category if rec.category in VALID_CATEGORIES else "grammar"
    memory.add_personal_error(
        user_id, rec.original, rec.correction, category, rec.explanation
    )
    return {
        "category": category,
        "original": rec.original,
        "correction": rec.correction,
    }


# Minimum speech-to-text confidence (0–1) for a voice turn to be eligible for
# logging. Below this the transcript is too likely to be mis-heard to trust as an
# "error" — logging it would poison the corpus with STT artefacts rather than real
# learner mistakes. A turn with NO confidence signal at all is logged anyway: the
# source="voice" tag + the extraction guard remain the protection there.
VOICE_MIN_STT_CONFIDENCE = float(os.environ.get("VOICE_MIN_STT_CONFIDENCE", "0.6"))


async def extract_and_log_error_voice(
    user_id: str,
    user_text: str,
    assistant_text: str,
    confidence: float | None = None,
):
    """Voice sibling of `extract_and_log_error`: same guarded extraction, but the
    logged record is tagged source="voice" and low-confidence STT turns are skipped.

    Reuses the exact production guard (`_extract_record` + `_record_complete` +
    EXTRACTION_MAX_ATTEMPTS) so voice logging inherits the same field-drop / hung-
    provider protection as text. Differences from the text path, both deliberate:
      * a confidence gate up front — if `confidence` is provided and below
        VOICE_MIN_STT_CONFIDENCE, nothing is logged (the transcript is probably a
        mis-hear, not a real error). `confidence=None` means no signal was available,
        so we do NOT drop the turn — we fall through to the normal guard;
      * the logged error is tagged source="voice" so it stays distinguishable in the
        corpus from text-coach errors.
    """
    if confidence is not None and confidence < VOICE_MIN_STT_CONFIDENCE:
        return None
    if not _has_chinese(user_text):
        return None

    rec: ErrorExtraction | None = None
    for _ in range(EXTRACTION_MAX_ATTEMPTS):
        try:
            candidate = await _extract_record(user_text, assistant_text)
        except Exception:  # noqa: BLE001 — timeout/hang OR malformed output → retry
            continue
        if not candidate.had_error:
            return None
        rec = candidate
        if _record_complete(candidate):
            break

    if rec is None or not _record_complete(rec):
        return None

    category = rec.category if rec.category in VALID_CATEGORIES else "grammar"
    memory.add_personal_error(
        user_id, rec.original, rec.correction, category, rec.explanation, source="voice"
    )
    return {
        "category": category,
        "original": rec.original,
        "correction": rec.correction,
    }


class SentenceCorrection(BaseModel):
    """Pass-1 correction of a learner's own sentence (the pronunciation coach)."""

    had_error: bool = Field(description="True if the learner's sentence needed correcting")
    corrected: str = Field(default="", description="The corrected Chinese sentence (chars only)")
    category: str = Field(
        default="grammar",
        description="One of: grammar, word_order, measure_word, particle, vocabulary, tones",
    )
    note: str = Field(default="", description="Brief English explanation of the fix")


async def correct_sentence(text: str) -> SentenceCorrection:
    """Correct the learner's own sentence into a clean target they can then read aloud.

    Bounded by EXTRACTION_TIMEOUT. On any failure it returns the input unchanged
    (had_error=False) so Pass 1 degrades gracefully rather than blocking practice.
    """
    llm = get_llm(streaming=False)
    structured = llm.with_structured_output(SentenceCorrection)
    try:
        return await asyncio.wait_for(
            structured.ainvoke(
                [SystemMessage(content=SENTENCE_CORRECTION_PROMPT), HumanMessage(content=text)]
            ),
            timeout=EXTRACTION_TIMEOUT,
        )
    except Exception:  # noqa: BLE001 — hung/malformed provider → degrade to "as-is"
        return SentenceCorrection(had_error=False, corrected=text)


async def extract_error_record(user_input: str, agent_answer: str, model: str | None = None):
    """Eval-only sibling of `extract_and_log_error`: run the SAME extraction prompt +
    schema for ONE call and return the raw `ErrorExtraction`, with **no side effects**
    and **no retry guard**.

    Kept un-guarded on purpose: the extraction eval surface measures the *raw* provider
    reliability (field-drop / malformed-JSON rate), so it must see a single unguarded
    call. Differences from the production path, all deliberate:
      * no `memory.add_personal_error` write (eval must not mutate a corpus);
      * no `_has_chinese` guard (the eval applies that pure check itself so the
        guard's auto-negatives are scored deterministically and separately from
        the LLM's own had_error judgment);
      * no retry loop (production retries; the eval measures the pre-guard baseline);
      * the extraction model is overridable (production defaults to deepseek, which
        hangs on OpenRouter — evals pin `glm` for reproducibility, see DECISIONS #4).

    Returns the validated `ErrorExtraction` (never None) so the caller sees the
    real `had_error`/`category` even when the record would not be logged.
    """
    return await _extract_record(user_input, agent_answer, model)
