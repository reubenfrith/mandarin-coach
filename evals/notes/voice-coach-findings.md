# Voice-coach quality — findings & decisions

Decision record for the `voice_coach_quality` surface (`surfaces/voice_coach/voice_coach_quality_eval.py`).
The headline `.md`/`.json` live in `results/voice_coach_quality.{md,json}`; this note is the narrative:
why the surface exists, what it found, why the judge is gpt-4o-mini (not the repo default), and the
product changes it argues for.

## Why the voice coach needed its own quality surface

The voice router (`voice_intent_eval`) checks *which brain* answers a spoken turn. It never checks
whether the coach brain's actual **explanation** is any good. The text-coach evals (head-to-head,
RAGAS) score correction quality, but the voice coach has behaviours they don't touch:

- **Spoken/full split** — line 1 is read aloud (`_split_spoken`), so it must be one short, markdown-free
  English sentence, with the breakdown below.
- **English-only** — explain in English even when the learner spoke Mandarin.
- **Noise robustness** — STT is lossy; on a garbled turn the coach should ask to repeat, not invent a
  correction for noise.
- **History grounding** — resolve a referential turn ("why was that wrong?") from the recent spoken
  context without asking the learner to repeat.

20 hand-authored turns (6 sentence_coach · 6 question · 4 referential · 4 garbled), each with an
authored EXPECTATION the judge scores against. Format/speakability are checked deterministically (no
LLM); content is judged by an independent model.

## What it found

**The format machinery is solid (deterministic, stable):** every reply put a valid, markdown-free
English headline on line 1 with a breakdown below (split-valid 1.0), and every spoken line was
speakable (≤40 words; p95 ≈ 31). Explanation-in-English 1.0.

**Content is good on questions and referential turns, weak on two things:**

1. **Noise robustness is the real gap.** On garbled/STT-mangled input the coach *fabricates* a
   correction instead of asking to repeat — e.g. it turned `wo qu le de shdjf ne uh` into
   "我去了商店 (I went to the store)" and explained 的 from a mostly-`[inaudible]` turn. Garbled
   meets_expectation was **0.25 in all three gpt-4o-mini runs** (3 of the 4 garbled turns fabricate,
   every run — stable, not sampling noise, though n=4 is small). This is the one clear, actionable
   defect.
2. **It won't cleanly affirm a correct sentence.** Given the already-correct 请给我一杯水 (the control
   case), it invents a "more natural" change (drop 请) rather than confirming it's right. Reproduced
   across both runs.

Everything else (二/两, 把, measure words, 了/过, the referential recasts) was explained correctly, and
the reliable judge found **0 misleading claims**.

## Judge selection: gpt-4o-mini, not the repo-default glm

The first run used the repo default `JUDGE_MODEL=glm` and produced a **misleading** picture:
`misleading 3/20`, `meets_expectation 0.65`, and it flagged four correct answers (sc04, sc06, q02,
q04) as failing — with the `reason` field **left empty on every case**. That empty-reason signature is
the same structured-output unreliability the extraction surface documented for glm (DECISIONS #13);
the Pydantic serialization warnings during the run confirm glm mangled the JSON.

Switching the judge to **gpt-4o-mini** (this surface overrides the default; glm stays the default
elsewhere): reasons are populated and sensible, the four false negatives flip to passes, and the three
false-positive "misleading" flags disappear. Crucially, **all 20 gpt-4o-mini verdicts match an
independent manual adjudication** of the coach replies — the strongest available reliability check.

*Self-preference caveat:* the coach is also gpt-4o-mini, so a same-model judge could in principle be
lenient. Two things bound that here: (1) the gpt-4o-mini judge **failed 5/20 of its own model's
replies** — including the real defects — which a rubber-stamping judge would not; and (2) every one of
its 20 verdicts matches an independent manual adjudication. A `--verify-judge qwen` cross-check was
attempted (different family, Chinese-strong) but qwen stalled on OpenRouter and was abandoned — the same
reasoning-model hang this repo already documents for the text coach; glm is unfit for the role (it is
the model under discussion), so manual adjudication is the reliability authority. `--verify-judge` is
wired for a future run against a fast, reliable non-OpenAI judge.

One required schema change: gpt-4o-mini uses OpenAI **strict** JSON-schema mode, so `VoiceQualityVerdict`
fields must be required (no Pydantic defaults) — otherwise the schema is rejected.

## A metric caught wrong during verification

The `asks_to_repeat` judge flag is **not** a reliable noise-robustness signal: the coach ends replies
with a "try saying … next time!" drill, which the judge reads as a repeat request even when the coach
*fabricated* a correction. So the noise metric is **garbled meets_expectation**, not `asks_to_repeat`
(the raw flag is kept in the JSON but demoted in the report).

## Nondeterminism

The coach runs at production temperature (0.2), so the judge-based rates move run to run. Spread across
**three gpt-4o-mini-judged runs**: meets_expectation **0.75–0.80**, referential **0.75–1.0**. Stable
across all three: misleading **0/20**, garbled meets **0.25**, and every deterministic check
(split-valid, English, speakable) at **1.0**. So the headline conclusions — solid format machinery, no
misleading claims, and a real noise-robustness gap — are not artefacts of a single sample.

## Recommended product changes (argued by this surface)

1. **Harden noise handling — the biggest win.** `VOICE_COACH_SYSTEM_PROMPT` says "if something seems
   garbled, ask them to repeat", but the model overrides it and tries to help. Strengthen it (make the
   ask-to-repeat an explicit first-check: "If the turn is fragmentary, nonsensical, or looks like a
   failed transcription, DO NOT invent a correction — ask the learner to say it again."), and/or add a
   cheap pre-check before invoking the coach.
2. **Affirm correct input cleanly.** Tighten the "if it's already correct, say so" branch so the coach
   stops inventing stylistic changes to correct sentences.
3. **If noise robustness becomes a tracked metric, grow the garbled slice and add coach `--repeats`** so
   the rate is stable, not directional (the router surface's pattern for a nondeterministic component).
