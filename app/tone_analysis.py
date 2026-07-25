"""Mandarin tone analysis — pure DSP, no ML model and no ASR.

The acoustic core of the pronunciation coach (see docs/pronunciation-coach-plan.md).
Given a learner's audio and a KNOWN target (the syllables they were asked to say, from
the corrected sentence in Pass 1), it:

  1. recovers the pitch (F0) contour from the audio with pYIN          [extract_f0]
  2. reduces it to a register-independent shape (log-pitch, mean-removed)  [contour_shape]
  3. compares that shape to the canonical Mandarin tone contours       [classify_contour]
     or to the target's whole "melody"                                 [assess]

Everything here is deterministic signal processing (pYIN + DTW/RMSE on pitch curves),
so the verdict is inspectable and explainable — the whole point of the design. No trained
weights, no network. Validated against synthesised tones in tests/test_tone_analysis.py.
"""
from __future__ import annotations

import io

import librosa
import numpy as np
import soundfile as sf

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
N = 40                       # points a contour is resampled to for shape comparison
PYIN_FMIN, PYIN_FMAX = 80.0, 400.0
PYIN_FRAME, PYIN_HOP = 1024, 128
_SCORE_K = 4.0               # distance -> score sharpness (uncalibrated; see plan Phase 2)

# A speaker's pitch range, log-spaced across the Chao 1-5 scale. Absolute Hz only make the
# templates concrete; the *shape* (after mean-removal) is what the comparison uses, so this
# range is register-agnostic in practice.
_FMIN_SP, _FMAX_SP = 110.0, 210.0


def _chao_hz(level: float) -> float:
    """Chao pitch level (1=low .. 5=high) -> Hz, log-spaced across the speaker range."""
    return _FMIN_SP * (_FMAX_SP / _FMIN_SP) ** ((level - 1) / 4.0)


def _levels_to_contour(levels):
    """A pitch curve f(t), t in [0,1], piecewise-linear through Chao levels."""
    ts = np.linspace(0, 1, len(levels))
    hz = np.array([_chao_hz(l) for l in levels])
    return lambda t: np.interp(t, ts, hz)


# The four lexical tones as Chao level sequences (neutral/T5 is out of scope for v1).
TONE_LEVELS = {1: [5, 5], 2: [3, 5], 3: [2, 1, 4], 4: [5, 1]}
TONE_NAMES = {1: "T1 high-level", 2: "T2 rising", 3: "T3 dipping", 4: "T4 falling"}
TONE_TEMPLATES = {t: _levels_to_contour(lv) for t, lv in TONE_LEVELS.items()}


# --------------------------------------------------------------------------- #
# Pitch extraction
# --------------------------------------------------------------------------- #
def f0_from_samples(y: np.ndarray, sr: int):
    """pYIN on a mono float waveform -> (times, f0_hz) over voiced frames only."""
    y = np.asarray(y, dtype=np.float32)
    if y.ndim > 1:
        y = y.mean(axis=1)
    f0, _, _ = librosa.pyin(
        y, sr=sr, fmin=PYIN_FMIN, fmax=PYIN_FMAX,
        frame_length=PYIN_FRAME, hop_length=PYIN_HOP,
    )
    times = librosa.times_like(f0, sr=sr, hop_length=PYIN_HOP)
    voiced = ~np.isnan(f0)
    return times[voiced], f0[voiced]


def extract_f0(wav_bytes: bytes):
    """Decode a WAV byte string and recover its voiced F0 contour. Returns (times, f0_hz).

    WAV (PCM) is expected — the browser encodes it client-side so the server never has to
    decode webm/opus (see plan, decision 1)."""
    y, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=False)
    return f0_from_samples(y, sr)


# --------------------------------------------------------------------------- #
# Shape + comparison
# --------------------------------------------------------------------------- #
def contour_shape(f0_hz, n: int = N) -> np.ndarray:
    """Register-independent contour shape: log2-pitch, resampled to n points, mean-removed.

    Mean-removal is the speaker normalisation — a bass and a soprano saying the same tone
    map to the same shape, because only the *melody* survives, not the absolute pitch."""
    f0_hz = np.asarray(f0_hz, dtype=float)
    if f0_hz.size < 2:
        return np.zeros(n)
    lg = np.log2(f0_hz)
    lg = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(lg)), lg)
    return lg - lg.mean()


TEMPLATE_SHAPES = {
    t: contour_shape(fn(np.linspace(0, 1, 200))) for t, fn in TONE_TEMPLATES.items()
}


def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def _dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Timing-invariant contour distance (DTW), normalised by path length. Lets a learner's
    syllable be longer/shorter than the target melody without penalising the shape."""
    D, wp = librosa.sequence.dtw(X=a[np.newaxis, :], Y=b[np.newaxis, :], metric="euclidean")
    return float(D[-1, -1] / len(wp))


def _score(distance: float) -> int:
    """Map a contour distance to a 0-100 score. Uncalibrated for v1 — Phase 2 calibrates
    the mapping against real learner recordings."""
    return int(round(100 * np.exp(-_SCORE_K * distance)))


def target_melody_shape(target_tones) -> np.ndarray:
    """Concatenate the target tones' templates into one 'melody', then shape it — the
    reference a multi-syllable utterance is matched against."""
    segs = [TONE_TEMPLATES[t](np.linspace(0, 1, 50)) for t in target_tones if t in TONE_TEMPLATES]
    if not segs:
        return np.zeros(N)
    return contour_shape(np.concatenate(segs))


def classify_contour(f0_hz):
    """Nearest canonical tone for a single-syllable contour.

    Returns (predicted_tone:int, distances:{tone:dist}, match_pct:{tone:pct}). match_pct is
    a naive softmax confidence (illustrative); the raw distance is the trustworthy signal.
    """
    s = contour_shape(f0_hz)
    dists = {t: _rmse(s, ts) for t, ts in TEMPLATE_SHAPES.items()}
    predicted = min(dists, key=dists.get)
    inv = {t: np.exp(-3.0 * d) for t, d in dists.items()}
    z = sum(inv.values()) or 1.0
    match = {t: round(100 * v / z, 1) for t, v in inv.items()}
    return predicted, dists, match


# --------------------------------------------------------------------------- #
# Top-level assessment
# --------------------------------------------------------------------------- #
def assess(f0_hz, target_tones) -> dict:
    """Score a learner's recovered F0 against the known target tone sequence.

    v1 (DSP-only, no aligner):
      * single-syllable target -> a full per-syllable verdict (predicted tone, score);
      * multi-syllable target  -> a whole-melody DTW score + curve overlay, but NO precise
        per-syllable verdicts (that needs forced alignment — plan Phase 2).

    Returns a dict shaped for the API/UI: overall_score, per_syllable[], the learner and
    target shapes for the curve overlay, and a note describing v1 limits.
    """
    f0_hz = np.asarray(f0_hz, dtype=float)
    target_tones = [int(t) for t in target_tones]

    if f0_hz.size < 2:
        return {"voiced": False, "overall_score": 0, "predicted_tones": [],
                "per_syllable": [], "learner_shape": [], "target_shape": [],
                "note": "No voiced pitch detected — try recording again, closer to the mic."}

    learner = contour_shape(f0_hz)

    if not any(t in TONE_TEMPLATES for t in target_tones):
        return {"voiced": True, "overall_score": 0, "predicted_tones": [],
                "per_syllable": [], "learner_shape": [round(x, 4) for x in learner.tolist()],
                "target_shape": [], "note": "No scorable (T1–T4) tones in the target."}

    if len(target_tones) == 1 and target_tones[0] in TONE_TEMPLATES:
        target = target_tones[0]
        predicted, dists, _ = classify_contour(f0_hz)
        dist = dists.get(target, _rmse(learner, TEMPLATE_SHAPES.get(target, np.zeros(N))))
        score = _score(dist)
        return {
            "voiced": True,
            "overall_score": score,
            "predicted_tones": [predicted],
            "per_syllable": [{
                "index": 0, "target_tone": target, "predicted_tone": predicted,
                "distance": round(dist, 4), "score": score, "ok": predicted == target,
            }],
            "learner_shape": [round(x, 4) for x in learner.tolist()],
            "target_shape": [round(x, 4) for x in TEMPLATE_SHAPES[target].tolist()],
            "note": "",
        }

    # Multi-syllable: whole-melody match only in v1.
    melody = target_melody_shape(target_tones)
    dist = _dtw_distance(learner, melody)
    return {
        "voiced": True,
        "overall_score": _score(dist),
        "predicted_tones": [],
        "per_syllable": [],
        "learner_shape": [round(x, 4) for x in learner.tolist()],
        "target_shape": [round(x, 4) for x in melody.tolist()],
        "note": ("Whole-utterance melody match. Per-syllable tone verdicts on multi-syllable "
                 "input need forced alignment (Phase 2)."),
    }
