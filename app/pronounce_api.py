"""Pronunciation coach — Pass 2 (say & score).

`POST /api/pronounce/assess` takes the learner's recorded WAV plus the KNOWN target
sentence (the corrected sentence from Pass 1) and returns per-syllable tone verdicts +
the pitch-curve overlay the UI draws. Clear wrong-tone errors are logged into the same
per-user corpus as the text coach, tagged category="tones", source="voice".

All acoustic judgment is the deterministic DSP in tone_analysis.py — no ASR, no ML model.
"""
import asyncio

from fastapi import APIRouter, Depends, File, Form, UploadFile

import memory
import tone_analysis
from tools import annotate_tones
from web_api import require_user

router = APIRouter()

# Below this score a *correctly-labelled* syllable is flagged "weak" for the UI but NOT
# logged as an error — pre-calibration we only auto-log unambiguous wrong-tone cases, to
# keep the corpus clean (see plan: eval/calibrate before trusting the threshold).
WEAK_SCORE = 60


def _log_tone_error(user_id: str, syl: dict, verdict: dict) -> dict:
    """Write one clear wrong-tone error to the corpus (ground-truth, so no LLM extraction)."""
    produced = tone_analysis.TONE_NAMES.get(verdict["predicted_tone"], "?")
    target = tone_analysis.TONE_NAMES.get(syl["tone"], "?")
    explanation = f"Produced {produced}, target {target}."
    memory.add_personal_error(
        user_id,
        original=f'{syl["hanzi"]} said as {produced.split()[0]}',
        correction=f'{syl["hanzi"]} = {syl["pinyin"]} ({target})',
        category="tones",
        explanation=explanation,
        source="voice",
    )
    return {"hanzi": syl["hanzi"], "produced_tone": verdict["predicted_tone"],
            "target_tone": syl["tone"], "explanation": explanation}


@router.post("/api/pronounce/assess")
async def assess(
    audio: UploadFile = File(...),
    target: str = Form(...),
    user_id: str = Depends(require_user),
):
    wav = await audio.read()
    syllables = annotate_tones(target)
    if not syllables:
        return {"target": target, "syllables": [], "overall_score": 0, "voiced": False,
                "learner_shape": [], "target_shape": [], "logged": [],
                "note": "No Chinese characters in the target."}

    target_tones = [s["tone"] for s in syllables]
    # pYIN + DTW are CPU-bound (numba); keep them off the event loop.
    _, f0 = await asyncio.to_thread(tone_analysis.extract_f0, wav)
    result = tone_analysis.assess(f0, target_tones)

    # Attach per-syllable verdicts (v1: populated only for single-syllable targets) and
    # log unambiguous wrong-tone errors.
    per = result["per_syllable"]
    logged = []
    for i, s in enumerate(syllables):
        v = per[i] if i < len(per) else None
        if v:
            s["predicted_tone"], s["score"], s["ok"] = v["predicted_tone"], v["score"], v["ok"]
            s["weak"] = bool(v["ok"] and v["score"] < WEAK_SCORE)
            if not v["ok"]:
                logged.append(_log_tone_error(user_id, s, v))
        else:
            s["predicted_tone"], s["score"], s["ok"], s["weak"] = None, None, None, False

    return {
        "target": target,
        "syllables": syllables,
        "overall_score": result["overall_score"],
        "voiced": result["voiced"],
        "learner_shape": result["learner_shape"],
        "target_shape": result["target_shape"],
        "note": result["note"],
        "logged": logged,
    }
