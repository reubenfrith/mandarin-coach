"""Phase-1 checks for the voice coach: shared spoken history + the coach path.

The load-bearing property is that BOTH voice brains read/write ONE history, so a
coaching question ("why was that wrong?") can see the recast the conversation partner
just made — and conversation resumes afterwards. No network: the conversation LLM and
the coach runner are stubbed; we assert the wiring (history injection, mode tags, the
spoken-vs-full split, and that only the short spoken line is written back).

Run:  uv run python tests/test_voice_coach.py
"""
import asyncio
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("CHROMA_PATH", "/tmp/mc_test_voice_coach_chroma")
os.environ.setdefault("EMBEDDING_MODEL", "default")
os.environ.setdefault("CHAINLIT_AUTH_SECRET", "test-secret-please-ignore-000000")

import voice_api  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: E402


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


class _FakeLLM:
    """Stands in for the conversation model; captures the messages it was prompted with."""
    def __init__(self, reply):
        self.reply = reply
        self.seen = None

    async def ainvoke(self, messages):
        self.seen = messages
        return SimpleNamespace(content=self.reply)


async def main():
    U = "voice-user"
    voice_api._voice_history.clear()

    # --- stub the conversation brain -------------------------------------------------
    convo_llm = _FakeLLM("你好！你今天做了什么？")
    voice_api.get_llm = lambda *a, **k: convo_llm
    voice_api._system_prompt = lambda uid: "SYS"

    # --- stub the coach runner (capture what history it was handed) ------------------
    captured = {}

    async def fake_run_voice_coach(graph, history_messages, question):
        captured["graph"] = graph
        captured["history"] = history_messages
        captured["question"] = question
        return ("了 marks a completed action.",
                "了 marks a completed action.\n\nExample: 我吃了饭 = I have eaten.")

    voice_api.run_voice_coach = fake_run_voice_coach
    voice_api._coach_for = lambda uid: "COACH_GRAPH"

    # 1. A conversation turn writes two converse-tagged entries.
    reply = await voice_api._reply(U, "我昨天去了商店")
    h = voice_api._history(U)
    check("converse turn returns the model reply", reply == "你好！你今天做了什么？")
    check("  ...history has the user + assistant turns", len(h) == 2)
    check("  ...both tagged mode=converse",
          h[0]["mode"] == "converse" and h[1]["mode"] == "converse")
    check("  ...roles + content correct",
          h[0] == {"role": "user", "content": "我昨天去了商店", "mode": "converse"}
          and h[1]["role"] == "assistant" and h[1]["content"] == reply)
    check("  ...first turn saw no prior history (SYS + 1 human)",
          len(convo_llm.seen) == 2 and isinstance(convo_llm.seen[0], SystemMessage))

    # 2. THE CRUX: a coaching question sees the prior conversation turns.
    spoken, full = await voice_api._coach_reply(U, "why did you use 了 there?")
    check("coach was handed the prior conversation as context",
          [type(m) for m in captured["history"]] == [HumanMessage, AIMessage]
          and captured["history"][0].content == "我昨天去了商店")
    check("  ...and the question", captured["question"] == "why did you use 了 there?")
    check("  ...uses the per-user coach graph", captured["graph"] == "COACH_GRAPH")

    # 3. Spoken vs full split; only the SHORT line is written back.
    check("returns the spoken TL;DR", spoken == "了 marks a completed action.")
    check("  ...and the full explanation for the UI", "Example: 我吃了饭" in full)
    h = voice_api._history(U)
    check("coach turn appended (user + assistant)", len(h) == 4)
    check("  ...tagged mode=coach", h[2]["mode"] == "coach" and h[3]["mode"] == "coach")
    check("  ...assistant entry stores the SHORT spoken line, not the full detail",
          h[3]["content"] == spoken and "Example" not in h[3]["content"])

    # 4. Conversation resumes and now sees the coaching detour (shared history).
    convo_llm2 = _FakeLLM("明白了，继续聊吧。")
    voice_api.get_llm = lambda *a, **k: convo_llm2
    await voice_api._reply(U, "好的")
    prompted = [m.content for m in convo_llm2.seen]
    check("next chat turn sees the coach detour in its prompt",
          "了 marks a completed action." in prompted and "why did you use 了 there?" in prompted)

    # 5. History stays capped at _HISTORY_TURNS.
    for i in range(20):
        voice_api._remember(U, "user", f"m{i}", "converse")
    check("history capped at _HISTORY_TURNS",
          len(voice_api._history(U)) == voice_api._HISTORY_TURNS)

    print("\nAll voice-coach (Phase 1) checks passed.")


def test_voice_coach():
    """pytest entry point (see conftest.py)."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
