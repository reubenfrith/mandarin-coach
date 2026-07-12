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
from config import DEFAULT_MODEL, FALLBACK_MODEL, get_llm
from prompts import AGENT_SYSTEM_PROMPT, ERROR_EXTRACTION_PROMPT
from tools import make_tools

# Hard ceiling on a whole agent turn (which may chain several LLM + tool calls).
# Generous enough for a legit multi-tool reasoning turn, but bounded so a hung
# provider can't strand the user — on breach we fall back to the fast model.
AGENT_TURN_TIMEOUT = float(os.environ.get("AGENT_TURN_TIMEOUT", "180"))

# A built coach: the primary (reasoning) graph plus a fast fallback graph. Each has
# its own checkpointer so a partially-run primary turn can't corrupt fallback state.
CoachAgent = namedtuple("CoachAgent", ["primary", "fallback"])

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


def _build_graph(user_id: str, prompt: str, model_key: str):
    """One LangGraph tool-calling graph on `model_key`, with its own checkpointer."""
    return create_agent(
        get_llm(model_key, streaming=False),
        make_tools(user_id),
        system_prompt=prompt,
        checkpointer=MemorySaver(),
    )


def build_agent(user_id: str, profile_note: str = "") -> CoachAgent:
    """Build the coach for one user: a primary (reasoning) graph plus a fast fallback.

    Each graph's MemorySaver checkpointer keeps per-conversation state keyed by
    thread_id, so each turn only needs the new message (LangGraph reloads history).
    """
    prompt = AGENT_SYSTEM_PROMPT + (f"\n\n{profile_note}" if profile_note else "")
    return CoachAgent(
        primary=_build_graph(user_id, prompt, DEFAULT_MODEL),
        fallback=_build_graph(user_id, prompt, FALLBACK_MODEL),
    )


async def _invoke(graph, user_input: str, config) -> str:
    result = await asyncio.wait_for(
        graph.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=config),
        timeout=AGENT_TURN_TIMEOUT,
    )
    return answer_text(result["messages"][-1].content) or "(no response)"


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


async def extract_and_log_error(user_id: str, user_input: str, agent_answer: str):
    """Extract the learner's error (if any) and log it so the corpus grows from use."""
    if not _has_chinese(user_input):
        return None
    try:
        structured = get_llm(streaming=False).with_structured_output(ErrorExtraction)
        rec: ErrorExtraction = await structured.ainvoke(
            [
                SystemMessage(content=ERROR_EXTRACTION_PROMPT),
                HumanMessage(
                    content=f"Learner input:\n{user_input}\n\nCoach reply:\n{agent_answer}"
                ),
            ]
        )
    except Exception:
        return None

    if not rec.had_error or not rec.original.strip():
        return None
    category = rec.category if rec.category in VALID_CATEGORIES else "grammar"
    memory.add_personal_error(
        user_id, rec.original, rec.correction, category, rec.explanation
    )
    return {
        "category": category,
        "original": rec.original,
        "correction": rec.correction,
    }
