# Implementation Plan: Two-Pass Pronunciation Coach

## Context

The voice feature is being re-scoped from a free-flowing **conversation partner** (the
current OpenRouter STT→LLM→TTS pipeline in `app/voice_api.py`) to a **pronunciation
coach**: a learner-driven *record → analyze → improve* loop with a strong emphasis on
**tones**. The design decisions that led here:

- **Learner autonomy over prescribed scripts.** The learner composes their *own*
  sentences and is corrected on them — no "repeat after me" canned drills. A sentence the
  learner authored and we then corrected is still a *known target*, which is all the
  acoustic analysis needs. Tractability came from knowing the *text*, not from dictating
  the *content*.
- **Acoustics-first, no tidying ASR in the judging path.** A word-level ASR is trained to
  recover the *intended word* and will silently "fix" bad pronunciation, so it cannot judge
  tones. We go straight to the pitch signal instead. ASR is used only in Pass 1 to capture
  the learner's words (where tidying is fine), never to score pronunciation.
- **DSP-only for v1, no new ML model.** Pitch extraction (pYIN) and contour comparison
  (DTW) are classic algorithms, not trained models — validated to recover clean tone
  contours from audio in the prototype (`scratchpad/tone_proto.py`). Models remain an
  accuracy dial to turn later (CREPE, forced aligner, tone classifier), which is where a
  bigger VM would earn its keep.

## Flow

```
PASS 1 — compose & correct (content)                PASS 2 — say & score (pronunciation)
──────────────────────────────────────             ──────────────────────────────────────
learner types OR speaks a draft                     learner records the corrected sentence
        │ (if audio: STT — tidying OK here)                 │
        ▼                                                    ▼
POST /api/pronounce/correct                         POST /api/pronounce/assess (audio + target)
  → corrected sentence + grammar notes                → extract_f0 (pYIN)   [tone_analysis.py]
  → logs grammar errs (add_personal_error)            → DTW vs target melody (pypinyin tones)
  → TTS reference audio to hear the target            → per-syllable verdict + curve + score
        │                                                    → logs tone errs (category="tones")
        └──────────────► corrected sentence = the TARGET ───┘
                         (learner-owned, so it's a known target)

both error types → same corpus + error_stats trends → LLM suggests what to drill next
```

## Files to create

**`app/tone_analysis.py`** — pure DSP, no framework (lifts the validated prototype):
- `extract_f0(wav_bytes) -> (times, f0_hz)` — decode WAV via `soundfile`, run `librosa.pyin`,
  keep voiced frames.
- `contour_shape(f0_hz)` — log2 → resample to N points → mean-remove (speaker
  normalization: compare the melody, not absolute pitch).
- `TONE_TEMPLATES` (Chao 1–5 levels) + `classify_contour()` + `assess(learner_f0, target_tones)`
  using `librosa.sequence.dtw` for whole-contour comparison →
  `{overall_score, divergence_points, per_syllable: [...]}`.

**`app/pronounce_api.py`** — FastAPI router, `require_user`-gated, included by `server.py`:
- `POST /api/pronounce/correct` — body `{text?, audio?}`. If audio → STT via existing
  `voice_api._openrouter_client().audio.transcriptions`. Then a **focused structured
  correction** (`get_llm` + new `SENTENCE_CORRECTION_PROMPT` → `{corrected, had_error, note}`)
  — cleaner than the chatty agent for extracting a target string. Logs grammar errors via
  existing `agent.extract_and_log_error`. Returns `{original, corrected, note, target_tones}`.
- `POST /api/pronounce/reference` — TTS the corrected sentence via existing OpenRouter TTS
  (`voice_api._synthesize`) → base64 audio (+ optionally its F0 curve for overlay).
- `POST /api/pronounce/assess` — multipart `audio` + form `target`. Computes target tones
  (`pypinyin` `Style.TONE3`), runs `tone_analysis.assess`, and for each syllable below the
  threshold writes **directly** `memory.add_personal_error(..., category="tones",
  source="voice")` (we have ground truth — no LLM extraction needed). Returns per-syllable
  verdicts + both pitch curves + overall score.

**`app/web_ui/practice.js` + a new "Practice" tab**:
1. Compose box (type or record draft) → **Check** → `/api/pronounce/correct`; show
   original→corrected diff, play reference TTS, show pinyin + target tones.
2. **Record & score** → `/api/pronounce/assess` → render on a `<canvas>`: learner curve vs
   target curve overlay ("follow the grey line"), per-syllable green/amber/red pinyin with
   target-vs-produced tone, overall score, **Try again**.

## Files to modify

- `app/prompts.py` — add `SENTENCE_CORRECTION_PROMPT`.
- `app/server.py` — `app.include_router(pronounce_router)`.
- `app/web_ui/index.html` / `app.js` — add the **Practice** tab (make it the primary voice
  surface; demote free-conversation to a "just chat" tab or drop it).
- `app/tools.py` — helper returning per-character numeric tones (`Style.TONE3`) beside the
  existing `_tone_pinyin`.
- `pyproject.toml` — add `librosa`, `soundfile`, `numpy` (currently venv-only). Grows the
  image (numba/scipy, a few hundred MB) — acceptable for v1.

## Two technical decisions

1. **Record WAV in the browser, not webm/opus.** MediaRecorder defaults to webm/opus, which
   `soundfile`/libsndfile won't decode server-side. Encode PCM **WAV** client-side from the
   Web Audio stream so the server decodes trivially. (Hidden in the conversation pipeline
   because OpenRouter STT accepted webm; here we decode locally, so format matters.)
2. **v1 scoring = whole-contour DTW, not hard per-syllable alignment.** Lead with the
   **graded distance + curve overlay** (the prototype showed this catches subtle sags a hard
   tone label misses); give per-syllable verdicts only where clean voicing gaps allow
   segmentation. Precise per-syllable scoring on long sentences needs a forced aligner —
   **Phase 2** (a model, bigger VM). Keep the v1 practice unit short (word / a few syllables).

## Verification

- **Unit** `tests/test_tone_analysis.py` — reuse the prototype cases: synth → assess →
  assert correct verdicts, and that a sagging T1 raises the contour distance.
- **API** (TestClient) — `/api/pronounce/correct` (stub the LLM) returns a corrected string +
  logs a grammar error; `/api/pronounce/assess` (feed a synthesized WAV) returns per-syllable
  verdicts and writes a `category="tones"` record that appears in `error_stats`.
- **Eval before auto-logging** — `evals/surfaces/tone_assessment_eval.py`: labeled/synthetic
  set → measure tone precision/recall → set the logging threshold. Same "measure before you
  trust it" discipline as the guarded text extractor. **Done:** the ungated predicate scored
  precision 0.833 (8 false positives on shallow T2/T3 flipping to flat T1); a calibrated
  confidence gate `LOG_MARGIN = 0.067` lifts it to 1.00 at 0.95 recall (Surface 5 in the
  certification README).
- **Manual** — full practice loop (correction + TTS need the OpenRouter key; assessment runs
  locally).

## Build order

1. `tone_analysis.py` + unit test — the core, already prototyped.
2. `/api/pronounce/assess` (assessment only, known target) + test.
3. Pass-1 correction + `SENTENCE_CORRECTION_PROMPT` + reference TTS.
4. Practice UI (compose → correct → record → canvas score).
5. Tone-error logging + threshold gating + trends wiring.
6. `pyproject` deps + docs.
7. *(Phase 2)* forced aligner for full-sentence per-syllable; CREPE for creaky-voice
   robustness; score calibration; perception drills.

## Risks

- **Browser audio format** → mitigated by client-side WAV encoding (decision 1).
- **pYIN on real creaky voice** (synthetic was clean) → CREPE upgrade path, Phase 2.
- **Multi-syllable segmentation** without an aligner → v1 whole-contour DTW + best-effort;
  precise per-syllable is Phase 2.
- **librosa/numba image weight** → accept for v1, revisit if deploy size bites.
- **L2 accuracy unproven** → the eval gate before auto-writing to the corpus is
  non-negotiable.

## Reuse map (what already exists)

| Need | Reused from |
|---|---|
| Auth (cookie, `require_user`) | `app/web_api.py` |
| Grammar correction brain | `agent.run_agent` / `agent.extract_and_log_error` |
| STT / TTS via OpenRouter | `voice_api._openrouter_client` / `voice_api._synthesize` |
| Corpus + `"tones"` category + trends | `memory.add_personal_error(..., source=)`, `memory.error_stats` |
| Target pinyin/tones | `tools._tone_pinyin` (+ `Style.TONE3` helper) |
| LLM for feedback phrasing / drills | `config.get_llm`, `drill_generator` |
| UI shell (login/onboard/tabs) | `app/web_ui/` |

The DSP core (`tone_analysis.py`) is the only genuinely new muscle, and it is already
prototyped and validated on synthetic audio.
