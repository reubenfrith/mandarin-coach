"""Chainlit entry point — thin vertical slice (Task 4, step 1).

Proves the full path end to end: browser UI -> Chainlit -> ChatLiteLLM ->
OpenRouter -> Chinese-native model, streamed back token by token. RAG retrieval,
the five agent tools, and the per-user personal-error memory layer on top of this
skeleton next.

Run locally:  chainlit run app/main.py -w
"""
import os
import sys

# Ensure sibling modules (config.py, etc.) import regardless of working directory.
sys.path.insert(0, os.path.dirname(__file__))

import chainlit as cl
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config import DEFAULT_MODEL, get_llm

load_dotenv()

SYSTEM_PROMPT = (
    "You are a Mandarin coach for lower-intermediate English-speaking learners "
    "(roughly HSK 2-4). When the user submits Chinese text, identify grammar and "
    "word-choice errors, give the corrected sentence, then explain the root cause "
    "briefly in English. If there is no error, confirm it and offer a small "
    "extension. Keep replies concise and encouraging."
)


def answer_text(content) -> str:
    """Extract user-facing answer text from a streamed chunk.

    Reasoning models (e.g. deepseek-v4-flash) return content as a list of blocks
    mixing {'type': 'thinking', ...} reasoning with the actual answer. Chainlit's
    stream_token needs a plain string, and we don't want the model's reasoning in
    the chat, so keep only string and {'type': 'text'} blocks and drop thinking.
    """
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


@cl.set_starters
async def starters():
    """Clickable first actions so the user never faces a blank chat."""
    return [
        cl.Starter(label="Check this sentence", message="她把书被他借走了"),
        cl.Starter(label="了 vs 过", message="What is the difference between 了 and 过?"),
        cl.Starter(label="Drill me on 把", message="Drill me on 把 sentences"),
    ]


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [SystemMessage(content=SYSTEM_PROMPT)])
    cl.user_session.set("llm", get_llm(DEFAULT_MODEL))


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history")
    llm = cl.user_session.get("llm")
    history.append(HumanMessage(content=message.content))

    reply = cl.Message(content="")
    async for chunk in llm.astream(history):
        token = answer_text(chunk.content)
        if token:
            await reply.stream_token(token)
    await reply.update()

    history.append(AIMessage(content=reply.content))
