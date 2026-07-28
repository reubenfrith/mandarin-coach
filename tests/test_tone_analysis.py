"""Deterministic checks for app/tone_analysis.py — the DSP tone core.

Synthesises tones with known F0 contours, runs them through the real pYIN pipeline, and
asserts the analysis recovers the right verdicts. No network, no ML model. Mirrors the
prototype (scratchpad/tone_proto.py) that de-risked the approach.

Run:  uv run python tests/test_tone_analysis.py   (exit 0 = all passed)
"""
import io
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import tone_analysis as ta  # noqa: E402

SR = 22050
DUR = 0.5


def synth(levels, *, jitter=0.03, noise=0.004, seed=0):
    """Additive-harmonic tone at a pitch that moves through the given Chao levels."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    f0 = ta._levels_to_contour(levels)(t / DUR)
    if jitter:
        f0 = f0 * (1 + jitter * rng.standard_normal(len(t)).cumsum() / len(t) ** 0.5)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = sum((1.0 / k) * np.sin(k * phase) for k in range(1, 17))
    sig = (np.hanning(len(t)) ** 0.3) * sig + noise * rng.standard_normal(len(t))
    return (sig / np.max(np.abs(sig))).astype(np.float32)


def wav_bytes(samples):
    buf = io.BytesIO()
    sf.write(buf, samples, SR, format="WAV")
    return buf.getvalue()


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


def main():
    # 1. pYIN faithfully recovers a flat high pitch from audio -> classifies as T1.
    _, f0_good_t1 = ta.f0_from_samples(synth([5, 5], seed=1), SR)
    pred, dists, _ = ta.classify_contour(f0_good_t1)
    check("good T1 recovered and classified as T1", pred == 1)
    check("  ...with a tiny distance to T1", dists[1] < 0.05)

    # 2. THE key case: a subtle sag stays 'T1-ish' by label but the distance rises sharply,
    #    so the graded score — not the hard label — is what catches subtle errors.
    _, f0_sag = ta.f0_from_samples(synth([5, 3], seed=2), SR)
    _, dists_sag, _ = ta.classify_contour(f0_sag)
    check("sagging T1 has a much larger T1-distance than a good T1",
          dists_sag[1] > dists[1] * 3)
    check("  ...so its score is lower", ta._score(dists_sag[1]) < ta._score(dists[1]))

    # 3. Gross wrong tone: target rising (T2), produced falling -> predicted T4, not ok.
    _, f0_fall = ta.f0_from_samples(synth([5, 1], seed=3), SR)
    res = ta.assess(f0_fall, [2])
    check("falling audio against a rising target -> predicted T4", res["predicted_tones"] == [4])
    check("  ...flagged not-ok", res["per_syllable"][0]["ok"] is False)
    check("  ...with a low score", res["overall_score"] < 40)

    # 4. The hard dipping tone (T3) is recovered and classified correctly.
    _, f0_t3 = ta.f0_from_samples(synth([2, 1, 4], seed=4), SR)
    check("good T3 classified as T3", ta.classify_contour(f0_t3)[0] == 3)

    # 5. WAV round-trip: the decode path (extract_f0) matches the in-memory path.
    res_wav = ta.assess(ta.extract_f0(wav_bytes(synth([5, 5], seed=1)))[1], [1])
    check("extract_f0 WAV path scores a good T1 as ok", res_wav["per_syllable"][0]["ok"])
    check("  ...with a high score", res_wav["overall_score"] > 80)

    # 6. Multi-syllable: a matching melody beats a mismatching one (whole-contour DTW),
    #    and v1 correctly declines to give per-syllable verdicts.
    _, f0_seq = ta.f0_from_samples(
        np.concatenate([synth([5, 5], seed=5), synth([5, 1], seed=6)]), SR)  # T1 then T4
    good = ta.assess(f0_seq, [1, 4])
    bad = ta.assess(f0_seq, [4, 2])
    check("matching multi-syllable melody scores higher than a mismatching one",
          good["overall_score"] > bad["overall_score"])
    check("  ...and v1 gives no per-syllable verdicts for multi-syllable", good["per_syllable"] == [])
    check("  ...with an explanatory note", "Phase 2" in good["note"])

    # 7. Silence / unvoiced input degrades safely.
    res_silent = ta.assess(np.array([]), [1])
    check("empty F0 -> voiced False, score 0, no crash",
          res_silent["voiced"] is False and res_silent["overall_score"] == 0)

    print("\nAll tone-analysis checks passed.")


def test_tone_analysis():
    """pytest entry point — runs the full check sequence (see conftest.py)."""
    main()


if __name__ == "__main__":
    main()
