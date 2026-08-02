"""Pronunciation coach — Pass 2 (say & score).

`POST /api/pronounce/assess` takes the learner's recorded WAV plus the KNOWN target
sentence (the corrected sentence from Pass 1) and returns per-syllable tone verdicts +
the pitch-curve overlay the UI draws. Clear wrong-tone errors are logged into the same
per-user corpus as the text coach, tagged category="tones", source="voice".

All acoustic judgment is the deterministic DSP in tone_analysis.py — no ASR, no ML model.
"""
import asyncio
import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

import agent
import memory
import tone_analysis
import voice_api
from tools import annotate_tones
from web_api import require_user

router = APIRouter()

# Below this score a *correctly-labelled* syllable is flagged "weak" for the UI but NOT
# logged as an error (a UI-only nudge, never a corpus write).
WEAK_SCORE = 60

# Confidence gate on auto-logging a wrong-tone error. `assess` reports a per-syllable
# `margin` = how much better the predicted (wrong) tone fits than the target; we only log
# when that margin clears LOG_MARGIN, so an ambiguous near-miss (a shallow-but-real T2/T3
# that flips to flat T1) never poisons the corpus. Calibrated on the labeled set in
# evals/surfaces/pronunciation/tone_assessment_eval.py: at margin 0 (log on any mismatch) precision was
# 0.83 (8/48 borderline logs were false); this gate lifts it to 1.00 at 0.95 recall. The
# value is the midpoint of the empirical gap between the worst false-positive and the
# nearest true-positive margin (0.0651–0.0689). Re-run the eval to recalibrate.
LOG_MARGIN = 0.067


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


@router.post("/api/pronounce/correct")
async def correct(
    text: str = Form(None),
    audio: UploadFile = File(None),
    user_id: str = Depends(require_user),
):
    """Pass 1: turn the learner's OWN draft (typed, or a spoken draft we transcribe) into a
    clean corrected sentence — the target they'll read aloud in Pass 2. Here a tidying STT
    is fine: we only want their words, not to judge pronunciation. Grammar errors are logged
    into the same corpus as the text coach."""
    if audio is not None:
        wav = await audio.read()
        client = voice_api._openai_client()
        # Pass-1 drafts are always Chinese — pin to zh (unlike the voice coach, which
        # auto-detects so it can hear English questions).
        text = await asyncio.to_thread(
            voice_api._transcribe, client, wav, audio.filename or "draft.wav", "zh"
        )
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Provide text or audio to correct.")

    result = await agent.correct_sentence(text)
    corrected = (result.corrected or "").strip() or text

    logged = None
    if result.had_error and corrected != text:
        category = result.category if result.category in agent.VALID_CATEGORIES else "grammar"
        memory.add_personal_error(user_id, text, corrected, category, result.note, source="text")
        logged = {"category": category, "original": text, "correction": corrected}

    return {
        "original": text,
        "corrected": corrected,
        "had_error": result.had_error,
        "note": result.note,
        "syllables": annotate_tones(corrected),  # target tones for Pass 2 + UI
        "logged": logged,
    }


@router.post("/api/pronounce/reference")
async def reference(text: str = Form(...), user_id: str = Depends(require_user)):
    """TTS the target sentence so the learner can hear it before recording."""
    client = voice_api._openai_client()  # TTS is OpenAI-only (OpenRouter has no TTS model)
    audio_out = await asyncio.to_thread(voice_api._synthesize, client, text)
    return {"audio_b64": base64.b64encode(audio_out).decode("ascii")}


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
            s["margin"] = v.get("margin")  # wrong-tone confidence; drives the log gate below
            s["weak"] = bool(v["ok"] and v["score"] < WEAK_SCORE)
            # Log only a CONFIDENT wrong-tone call (calibrated gate) — protects the corpus
            # from ambiguous near-misses. A flagged-but-unlogged miss still shows in the UI.
            if not v["ok"] and v.get("margin", 0.0) >= LOG_MARGIN:
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
