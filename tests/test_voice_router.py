"""Phase-2 checks for the voice intent router + the /api/voice/turn branch.

Two layers, both no-network:
  * _route_intent: manual override wins; a zero-latency script heuristic routes the clear
    cases (English -> coach, Mandarin -> converse); only a mixed turn calls the classifier.
  * /api/voice/turn: the endpoint branches to the right brain, speaks the right text, and
    only logs learner errors on a conversation turn (a coach question has none).

Run:  uv run python tests/test_voice_router.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("CHROMA_PATH", "/tmp/mc_test_voice_router_chroma")
os.environ.setdefault("EMBEDDING_MODEL", "default")
os.environ.setdefault("CHAINLIT_AUTH_SECRET", "test-secret-please-ignore-000000")

import voice_api  # noqa: E402


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


async def router_checks():
    print("[router]")
    calls = {"classify": 0}

    async def fake_classify(text):
        calls["classify"] += 1
        return "coach"

    orig = voice_api.classify_turn_intent
    voice_api.classify_turn_intent = fake_classify
    try:
        async def route(text, mode="auto"):
            return await voice_api._route_intent("u", text, mode)

        check("manual override -> coach", await route("我今天很好", "coach") == "coach")
        check("manual override -> converse", await route("why is this wrong", "converse") == "converse")
        check("pure English -> coach (no classifier)", await route("why was that wrong?") == "coach")
        check("pure Mandarin -> converse (no classifier)", await route("我昨天去了公园") == "converse")
        check("punctuation only -> converse", await route("。。。？") == "converse")
        check("  ...classifier NOT called for the clear cases", calls["classify"] == 0)
        check("mixed script -> classifier decides", await route("explain 了 please") == "coach")
        check("  ...classifier called exactly once (only the mixed turn)", calls["classify"] == 1)
    finally:
        voice_api.classify_turn_intent = orig


def endpoint_checks():
    print("[endpoint]")
    import app.server as s
    import memory
    memory.load_reference_data = lambda *a, **k: {}

    calls = {"reply": 0, "coach": 0, "extract": 0}

    async def fake_reply(uid, text):
        calls["reply"] += 1
        return "听起来不错！"

    async def fake_coach(uid, text):
        calls["coach"] += 1
        return ("Because 了 marks a completed action.",
                "Because 了 marks a completed action.\n\nExample: 我吃了饭.")

    async def fake_extract(uid, u, a, confidence=None):
        calls["extract"] += 1
        return {"category": "particle", "original": u, "correction": "x"}

    voice_api._reply = fake_reply
    voice_api._coach_reply = fake_coach
    voice_api.extract_and_log_error_voice = fake_extract
    voice_api._synthesize = lambda client, text: b"ID3-fake-mp3"
    voice_api._openai_client = lambda: object()

    from starlette.testclient import TestClient
    AUDIO = {"audio": ("turn.webm", b"RIFFfake", "audio/webm")}

    def turn(text, mode="auto"):
        voice_api._transcribe = lambda *a, **k: text
        return c.post("/api/voice/turn", files=AUDIO, data={"mode": mode}).json()

    with TestClient(s.app) as c:
        check("turn requires auth (401)",
              c.post("/api/voice/turn", files=AUDIO, data={"mode": "auto"}).status_code == 401)
        c.post("/api/login", data={"username": "voicer", "password": "pw123456"})

        # English question -> coach: speak the TL;DR, show the full answer, log nothing.
        r = turn("why was that wrong?")
        check("English -> intent coach", r["intent"] == "coach")
        check("  ...spoken is the TL;DR", r["spoken_text"] == "Because 了 marks a completed action.")
        check("  ...shown text is the full answer", "Example: 我吃了饭" in r["assistant_text"])
        check("  ...nothing logged on a coach question", r["logged"] is None)
        check("  ...coach ran, converse/extract did not",
              calls == {"reply": 0, "coach": 1, "extract": 0})

        # Mandarin -> converse: speak the whole reply, run the error-logging path.
        r = turn("我昨天去公园了的")
        check("Mandarin -> intent converse", r["intent"] == "converse")
        check("  ...speaks the whole reply", r["spoken_text"] == r["assistant_text"] == "听起来不错！")
        check("  ...logged via the extraction path", r["logged"] is not None)
        check("  ...converse + extract ran", calls["reply"] == 1 and calls["extract"] == 1)

        # Override: English text but mode=converse stays in conversation.
        r = turn("why is this", mode="converse")
        check("override converse wins over the English heuristic", r["intent"] == "converse")

        # Empty transcript -> null intent, no brain called.
        before = dict(calls)
        r = turn("")
        check("empty transcript -> null intent", r["intent"] is None and r["audio_b64"] is None)
        check("  ...no brain invoked", calls == before)

    print("  (coach did not run on the converse/override/empty turns)")


async def main():
    await router_checks()
    endpoint_checks()
    print("\nAll voice-router (Phase 2) checks passed.")


def test_voice_router():
    """pytest entry point (see conftest.py)."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
