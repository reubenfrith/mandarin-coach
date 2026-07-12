"""Chainlit entry point — the coaching agent UI, with per-user accounts.

Simple username/password auth (no OAuth). The authenticated username namespaces
that user's ChromaDB error corpus, so every user has a separate, persistent
profile. First login auto-creates the account and asks for the learner's level.

Path: browser -> login -> Chainlit -> tool-calling agent (ChatLiteLLM + 5 tools +
per-user ChromaDB memory) -> OpenRouter.

Run locally:  uv run chainlit run app/main.py -w   (set CHAINLIT_AUTH_SECRET first)
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))

import chainlit as cl
from dotenv import load_dotenv

import memory
import users
from agent import build_agent, extract_and_log_error, run_agent

load_dotenv()
users.init_db()

HSK_ACTIONS = [
    ("HSK 1-2", "HSK 1-2 (beginner)"),
    ("HSK 3-4", "HSK 3-4 (intermediate)"),
    ("HSK 5-6", "HSK 5-6 (advanced)"),
    ("unsure", "Not sure"),
]


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Validate credentials; auto-create the account on first login."""
    if users.verify_or_create(username, password):
        return cl.User(identifier=username.strip().lower(), metadata={"provider": "credentials"})
    return None


@cl.set_starters
async def starters():
    return [
        cl.Starter(label="Check this sentence", message="她把书被他借走了"),
        cl.Starter(label="了 vs 过", message="What is the difference between 了 and 过?"),
        cl.Starter(label="Drill me on 把", message="Drill me on 把 sentences"),
        cl.Starter(label="What am I getting wrong?", message="What am I getting wrong?"),
    ]


async def onboard_if_new(user_id: str) -> str:
    """Ask a first-time user for their level; return a profile note for the agent."""
    profile = users.get_profile(user_id) or {}
    hsk = profile.get("hsk_level")
    if not hsk:
        res = await cl.AskActionMessage(
            content=f"Welcome, {user_id}! What's your current Mandarin level?",
            actions=[
                cl.Action(name=name, payload={"value": name}, label=label)
                for name, label in HSK_ACTIONS
            ],
        ).send()
        hsk = res.get("payload", {}).get("value") if res else "unsure"
        users.set_hsk_level(user_id, hsk)
    if hsk and hsk != "unsure":
        return f"The learner self-reports their level as {hsk}. Pitch examples and drills accordingly."
    return ""


@cl.on_chat_start
async def on_chat_start():
    memory.load_reference_data()
    app_user = cl.user_session.get("user")
    user_id = app_user.identifier if app_user else "local_user"

    profile_note = await onboard_if_new(user_id)
    agent = build_agent(user_id, profile_note)
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("agent", agent)
    cl.user_session.set("thread_id", uuid.uuid4().hex)

    stats = memory.error_stats(user_id)
    if stats["total"] > 0:
        top = next(iter(stats["by_category"]), None)
        await cl.Message(
            content=(
                f"Welcome back, **{user_id}**. You have {stats['total']} logged "
                f"errors so far — most common: **{top}**. Want a drill, or shall we "
                f"check a new sentence?"
            )
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")
    user_id = cl.user_session.get("user_id")

    # Chainlit's LangChain callback renders each LangGraph tool call as a step.
    cb = cl.LangchainCallbackHandler()
    answer = await run_agent(agent, message.content, thread_id, callbacks=[cb])
    await cl.Message(content=answer).send()

    logged = await extract_and_log_error(user_id, message.content, answer)
    if logged:
        async with cl.Step(name="📝 logged to your error corpus", type="tool") as step:
            step.output = f"{logged['category']}: {logged['original']} → {logged['correction']}"
