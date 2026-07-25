"""End-to-end checks for POST /api/pronounce/assess (the pronunciation coach, Pass 2).

Synthesises WAV audio, drives the real endpoint via TestClient (real pYIN + DTW), and
asserts the verdicts + corpus logging. No network: load_reference_data is stubbed and the
assessment path is entirely local DSP.

Run:  uv run python tests/test_pronounce_api.py
"""
import io
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # repo root, for `import app.server`

os.environ.setdefault("EMBEDDING_MODEL", "default")
os.environ.setdefault("CHAINLIT_AUTH_SECRET", "test-secret-please-ignore-000000")

import tone_analysis as ta  # noqa: E402

SR = 22050
DUR = 0.5


def synth(levels, *, seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    f0 = ta._levels_to_contour(levels)(t / DUR) * (1 + 0.03 * rng.standard_normal(len(t)).cumsum() / len(t) ** 0.5)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = sum((1.0 / k) * np.sin(k * phase) for k in range(1, 17))
    sig = (np.hanning(len(t)) ** 0.3) * sig + 0.004 * rng.standard_normal(len(t))
    return (sig / np.max(np.abs(sig))).astype(np.float32)


def wav(levels, **kw):
    buf = io.BytesIO()
    sf.write(buf, synth(levels, **kw), SR, format="WAV")
    return buf.getvalue()


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


def main():
    import app.server as s
    import memory
    memory.load_reference_data = lambda *a, **k: {}  # skip the slow embed in this test

    from starlette.testclient import TestClient
    with TestClient(s.app) as c:
        # unauth
        r = c.post("/api/pronounce/assess", files={"audio": ("a.wav", wav([5, 5]), "audio/wav")},
                   data={"target": "妈"})
        check("assess requires auth (401)", r.status_code == 401)

        c.post("/api/login", data={"username": "toner", "password": "pw123456"})

        # 妈 = mā (T1). A good high-level tone -> ok, high score, nothing logged.
        r = c.post("/api/pronounce/assess", files={"audio": ("a.wav", wav([5, 5], seed=1), "audio/wav")},
                   data={"target": "妈"}).json()
        syl = r["syllables"][0]
        check("good T1 on 妈 -> ok", syl["ok"] is True and syl["predicted_tone"] == 1)
        check("  ...high score", r["overall_score"] > 80)
        check("  ...nothing logged", r["logged"] == [])
        check("  ...pinyin annotated", syl["pinyin"] == "mā" and syl["tone"] == 1)
        check("  ...curves returned for overlay", len(r["learner_shape"]) > 0 and len(r["target_shape"]) > 0)

        # 妈 target but a FALLING production (T4) -> wrong-tone, logged to corpus.
        r = c.post("/api/pronounce/assess", files={"audio": ("a.wav", wav([5, 1], seed=2), "audio/wav")},
                   data={"target": "妈"}).json()
        syl = r["syllables"][0]
        check("falling audio vs T1 target -> not ok, predicted T4", syl["ok"] is False and syl["predicted_tone"] == 4)
        check("  ...one tone error logged", len(r["logged"]) == 1 and r["logged"][0]["target_tone"] == 1)

        # It landed in the SAME corpus under category 'tones'.
        stats = c.get("/api/stats").json()
        check("corpus now has a 'tones' error", stats["total"] >= 1 and "tones" in stats["by_category"])

        # Multi-syllable 你好 -> whole-melody score, no per-syllable verdict in v1.
        r = c.post("/api/pronounce/assess", files={"audio": ("a.wav", wav([2, 1, 4], seed=3), "audio/wav")},
                   data={"target": "你好"}).json()
        check("multi-syllable returns an overall score", isinstance(r["overall_score"], int))
        check("  ...no per-syllable verdicts in v1", all(x["predicted_tone"] is None for x in r["syllables"]))
        check("  ...with a Phase-2 note", "Phase 2" in r["note"])

    print("\nAll pronounce-API checks passed.")


if __name__ == "__main__":
    main()
