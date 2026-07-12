"""The coaching agent — built with LangGraph.

Uses LangGraph's prebuilt tool-calling agent (`create_agent`, the LangGraph 1.0
successor to `create_react_agent`). LangGraph runs the decide -> call tools ->
observe -> answer loop as a graph, gives us a MemorySaver checkpointer for
per-conversation memory (keyed by thread_id), and produces a single grouped
LangSmith trace per turn.

The model is ChatLiteLLM (via OpenRouter), so every graph run is traced by
LangSmith when LANGSMITH_TRACING is set.
"""
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

import memory
from config import get_llm
from prompts import AGENT_SYSTEM_PROMPT, ERROR_EXTRACTION_PROMPT
from tools import make_tools

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


def build_agent(user_id: str, profile_note: str = ""):
    """Build a LangGraph tool-calling agent for one user, with conversation memory.

    The MemorySaver checkpointer keeps per-conversation state keyed by thread_id,
    so each turn only needs the new message (LangGraph reloads the history).
    """
    tools = make_tools(user_id)
    llm = get_llm(streaming=False)
    prompt = AGENT_SYSTEM_PROMPT + (f"\n\n{profile_note}" if profile_note else "")
    return create_agent(llm, tools, system_prompt=prompt, checkpointer=MemorySaver())


async def run_agent(graph, user_input: str, thread_id: str, callbacks=None) -> str:
    """Invoke the LangGraph agent for one turn and return the final answer text."""
    config = {"configurable": {"thread_id": thread_id}}
    if callbacks:
        config["callbacks"] = callbacks
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=user_input)]}, config=config
    )
    return answer_text(result["messages"][-1].content) or "(no response)"


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
