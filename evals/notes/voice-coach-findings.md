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
   "我去了商店 (I went to the store)" and explained 的 from a mostly-`[inaudible]` turn. The two
   unambiguous-noise turns (g02, g03) are fabricated **every run under both judges**, and the
   independent judge flags them **misleading**. Garbled meets_expectation runs **0.25–0.50** depending
   on how the two borderline fragments (g01, g04) are scored. n=4 is small, but the fabrication on
   clear noise is stable, not sampling noise. This is the one clear, actionable defect.
2. **It won't cleanly affirm a correct sentence.** Given the already-correct 请给我一杯水 (the control
   case), it invents a "more natural" change (drop 请) rather than confirming it's right. Reproduced
   across both runs.

Everything else (二/两, 把, measure words, 了/过, the referential recasts) was explained correctly. The
independent judge flags **3–4 misleading claims** (of 20) — stably the two noise fabrications (g02, g03:
presenting an invented sentence as "the correct way to say it" is a misleading assertion), plus a
variable one or two grammar-framing slips (e.g. sc04 calling a Chinese verb "past tense" — Chinese has
no tense conjugation). Note: the *same-model* gpt-4o-mini judge reported **0** misleading here; that gap
is the self-preference story below.

## Judge selection: gpt-4o (independent), after two rejections

This surface went through three judges — the second-to-third step is itself a finding.

**1. glm (the repo default) — rejected as unreliable.** The first run used `JUDGE_MODEL=glm` and gave a
garbled picture: it flagged four *correct* answers (sc04, sc06, q02, q04) as failing with the `reason`
field **empty on every case** — the same structured-output unreliability the extraction surface
documented (DECISIONS #13); the Pydantic warnings confirm glm mangled the JSON.

**2. gpt-4o-mini — reliable, but it is the coach, and that mattered.** Switching to gpt-4o-mini fixed
the reliability (reasons populate, the false negatives flip to passes) and its verdicts matched a manual
adjudication. BUT the coach under test is also gpt-4o-mini, and a `--verify-judge gpt-4o` cross-check on
identical coach outputs showed the same-model self-preference was **real and one-directional**: agreement
was 0.90 on meets_expectation and 1.0 on English, but on **misleading** all three disagreements went the
same way — gpt-4o-mini excused claims (sc04, g02, g03) that the stronger, independent gpt-4o flags.
The same-model judge reported **0/20 misleading**; the independent judge finds **3–4/20**. Exactly on the
headline "dangerous error" metric, the same-model judge was lenient on its own outputs.

**3. gpt-4o — adopted.** Stronger than the gpt-4o-mini coach and it graded it *stricter* (found more
misleading, not fewer), so it is not colluding. It is reliable (no glm-style empty verdicts) and fast
(unlike qwen, which stalled on OpenRouter — the documented reasoning-model hang). Residual caveat: gpt-4o
is same-*provider* as the coach; a cross-provider judge would be ideal but the available one (qwen) is
unusable here. `gpt-4o` was added to `config.MODELS` purely as an eval judge (no live path uses it).

One required schema change: gpt-4o(-mini) use OpenAI **strict** JSON-schema mode, so `VoiceQualityVerdict`
fields must be required (no Pydantic defaults) — otherwise the schema is rejected.

## A metric caught wrong during verification

The `asks_to_repeat` judge flag is **not** a reliable noise-robustness signal: the coach ends replies
with a "try saying … next time!" drill, which the judge reads as a repeat request even when the coach
*fabricated* a correction. So the noise metric is **garbled meets_expectation**, not `asks_to_repeat`
(the raw flag is kept in the JSON but demoted in the report).

## Nondeterminism

The coach runs at production temperature (0.2), so the judge-based rates move run to run. Spread across
**three gpt-4o-judged runs, BEFORE the fix below**: meets_expectation **0.80–0.85**, misleading **3–4/20**
(g02 + g03 in every run, plus a variable grammar-framing slip), garbled meets **0.50**. Stable across all
three: every deterministic check (split-valid, English, speakable) at **1.0**. So the pre-fix conclusions
— solid format machinery, a small-but-real misleading rate driven by noise fabrication, and the
noise-robustness gap — were not artefacts of a single sample.

## Fix applied & confirmed by re-running the surface

Both defects traced to the same root cause: `VOICE_COACH_SYSTEM_PROMPT` had **no** STT/garbled guidance
at all (the "if garbled, ask to repeat" line lives in the *conversation* prompt, not the coach's) and no
instruction to leave correct sentences alone. Two prompt edits fixed it:

1. **A garbled pre-check as the first rule** — "you hear the learner through speech-to-text…; if the turn
   is empty, fragmentary, cut off, a run of random syllables, or a failed transcription, do NOT invent a
   sentence or correction — briefly ask them to say it again. Never fabricate Chinese the learner didn't
   say."
2. **Affirm-correct-cleanly in the sentence branch** — "if it is already correct and natural, SAY SO and
   affirm it; do not invent a stylistic 'improvement' just to have something to fix."

Re-running the surface (gpt-4o judge, 3 runs) — before → after:

| Metric | before | after |
|---|---|---|
| Garbled handled correctly | 0.50 | **1.00** (all 3 runs) |
| Misleading | 3–4/20 | **0–2/20** (0 in the best run; noise fabrications gone) |
| sentence_coach meets (control affirmed) | ~0.83 | **0.83–1.00** |
| Referential meets (regression check) | 1.0 | **1.0** — no over-eager repeat-asking |
| English / split / speakable | 1.0 | 1.0 |

The noise-robustness gap — the whole reason this surface was worth building — is closed, with no
regression on the terse referential turns the pre-check could have mis-fired on. The residual variable
misleading flag (sc03/sc04 in some runs) is a separate, minor grammar-framing slip (calling a Chinese
verb "past tense"), not targeted by this fix.

## Still open (if this becomes a tracked metric)

- Grow the garbled slice beyond n=4 and add coach `--repeats` so the rate is stable, not directional
  (the router surface's pattern for a nondeterministic component).
- The minor "past tense" framing slip could be nipped with a one-line prompt note that Mandarin verbs
  don't conjugate for tense.
