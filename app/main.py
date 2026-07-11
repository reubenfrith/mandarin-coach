"""Chainlit entry point — the coaching agent UI.

Path: browser -> Chainlit -> tool-calling agent (ChatLiteLLM + 5 tools + ChromaDB
memory) -> OpenRouter. Each tool call is surfaced as a step so the agent's
reasoning is visible.

Run locally:  uv run chainlit run app/main.py -w
"""
import os
import sys

# Ensure sibling modules import regardless of working directory.
sys.path.insert(0, os.path.dirname(__file__))

import chainlit as cl
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

import memory
from agent import build_agent, new_history, run_agent

load_dotenv()

# Single-user prototype (OAuth is post-v1). One fixed namespace for the corpus.
USER_ID = os.environ.get("MANDARIN_USER_ID", "local_user")


@cl.set_starters
async def starters():
    return [
        cl.Starter(label="Check this sentence", message="她把书被他借走了"),
        cl.Starter(label="了 vs 过", message="What is the difference between 了 and 过?"),
        cl.Starter(label="Drill me on 把", message="Drill me on 把 sentences"),
        cl.Starter(label="What am I getting wrong?", message="What am I getting wrong?"),
    ]


@cl.on_chat_start
async def on_chat_start():
    # Reference data lazy-loads on first query; ensure it's present.
    memory.load_reference_data()
    llm, tools_by_name = build_agent(USER_ID)
    cl.user_session.set("llm", llm)
    cl.user_session.set("tools", tools_by_name)
    cl.user_session.set("history", new_history())


@cl.on_message
async def on_message(message: cl.Message):
    llm = cl.user_session.get("llm")
    tools_by_name = cl.user_session.get("tools")
    history = cl.user_session.get("history")
    history.append(HumanMessage(content=message.content))

    async def on_tool(name, args, result):
        async with cl.Step(name=name, type="tool") as step:
            step.input = args
            step.output = result[:1500]

    answer = await run_agent(llm, tools_by_name, history, on_tool=on_tool)
    await cl.Message(content=answer).send()
