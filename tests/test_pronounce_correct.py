"""Checks for the pronunciation coach Pass 1: /api/pronounce/correct and /reference.

The LLM correction, STT, and TTS are stubbed (no network); the test verifies the wiring:
draft -> corrected target + tone annotation, grammar logging into the shared corpus, the
audio-draft path, and reference TTS.

Run:  uv run python tests/test_pronounce_correct.py
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # repo root, for `import app.server`

os.environ.setdefault("EMBEDDING_MODEL", "default")
os.environ.setdefault("CHAINLIT_AUTH_SECRET", "test-secret-please-ignore-000000")


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


async def fake_correct(text):
    if text == "我是学生":  # already correct
        return SimpleNamespace(had_error=False, corrected=text, category="grammar", note="")
    return SimpleNamespace(had_error=True, corrected="我是学生", category="grammar", note="drop 的")


def main():
    import app.server as s
    import agent, memory, pronounce_api, voice_api

    memory.load_reference_data = lambda *a, **k: {}
    agent.correct_sentence = fake_correct
    voice_api._openrouter_client = lambda: object()
    voice_api._transcribe = lambda client, wav, fn: "我是学生的"
    voice_api._synthesize = lambda client, text: b"ID3-fake-mp3"

    from starlette.testclient import TestClient
    with TestClient(s.app) as c:
        check("correct requires auth (401)",
              c.post("/api/pronounce/correct", data={"text": "我是学生的"}).status_code == 401)

        c.post("/api/login", data={"username": "composer", "password": "pw123456"})

        # Typed draft with an error -> corrected target + tone annotation + grammar logged.
        r = c.post("/api/pronounce/correct", data={"text": "我是学生的"}).json()
        check("draft corrected to the clean target", r["corrected"] == "我是学生" and r["had_error"])
        check("  ...target syllables annotated with tones",
              len(r["syllables"]) == 4 and all("tone" in x and "pinyin" in x for x in r["syllables"]))
        check("  ...grammar error logged", r["logged"] and r["logged"]["category"] == "grammar")

        stats = c.get("/api/stats").json()
        check("grammar error landed in the shared corpus",
              stats["total"] >= 1 and "grammar" in stats["by_category"])

        # Already-correct draft -> nothing logged.
        r = c.post("/api/pronounce/correct", data={"text": "我是学生"}).json()
        check("already-correct draft logs nothing", r["logged"] is None and r["corrected"] == "我是学生")

        # Spoken draft -> STT (stubbed) -> correction.
        r = c.post("/api/pronounce/correct",
                   files={"audio": ("d.wav", b"RIFFfake", "audio/wav")}).json()
        check("audio draft is transcribed then corrected", r["corrected"] == "我是学生")

        # Empty -> 400.
        check("empty draft -> 400", c.post("/api/pronounce/correct").status_code == 400)

        # Reference TTS.
        r = c.post("/api/pronounce/reference", data={"text": "我是学生"}).json()
        check("reference returns audio", bool(r["audio_b64"]))

    print("\nAll pronounce-correct checks passed.")


def test_pronounce_correct():
    """pytest entry point — runs the full check sequence (see conftest.py)."""
    main()


if __name__ == "__main__":
    main()
