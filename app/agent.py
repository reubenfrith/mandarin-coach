"""The coaching agent: an explicit tool-calling loop.

The LLM is bound to the five tools and decides which to call based on intent. We
run the loop by hand (rather than AgentExecutor) because the reasoning model
returns content as mixed thinking/text blocks; an explicit loop lets us strip the
thinking, surface each tool call to the UI, and stay robust.

All calls go through ChatLiteLLM, so LangSmith traces the whole agent run.
"""
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from config import get_llm
from prompts import AGENT_SYSTEM_PROMPT
from tools import make_tools

MAX_ITERS = 6


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


def build_agent(user_id: str):
    """Return (llm_bound_to_tools, {tool_name: tool}) for one user."""
    tools = make_tools(user_id)
    llm = get_llm(streaming=False).bind_tools(tools)
    return llm, {t.name: t for t in tools}


def new_history() -> list:
    return [SystemMessage(content=AGENT_SYSTEM_PROMPT)]


async def run_agent(llm, tools_by_name, history, on_tool=None) -> str:
    """Run the tool-calling loop until the model produces a final answer.

    `history` is mutated in place (the running message list). `on_tool`, if given,
    is an async callback (name, args, result) used by the UI to show each step.
    Returns the final answer text.
    """
    for _ in range(MAX_ITERS):
        ai: AIMessage = await llm.ainvoke(history)
        history.append(ai)

        if not ai.tool_calls:
            return answer_text(ai.content) or "(no response)"

        for call in ai.tool_calls:
            tool = tools_by_name.get(call["name"])
            try:
                result = (
                    await tool.ainvoke(call["args"])
                    if tool
                    else f"Unknown tool: {call['name']}"
                )
            except Exception as e:  # a failing tool must not kill the turn
                result = f"Tool error ({type(e).__name__}): {e}"
            if on_tool:
                await on_tool(call["name"], call["args"], str(result))
            history.append(
                ToolMessage(content=str(result), tool_call_id=call["id"])
            )

    return "I wasn't able to finish that within the tool limit — please try rephrasing."
