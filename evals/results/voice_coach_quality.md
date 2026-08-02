# Voice-coach quality eval — `run_voice_coach`

20 spoken-coach turns through the real voice coach (**gpt-4o-mini** + grammar tools); judge = **gpt-4o-mini** (independent, temp 0). Scores the behaviours the text-coach evals don't cover: the spoken-TL;DR format, English-only explanation, noise→ask-to-repeat, and resolving referential turns from spoken history. Deterministic checks decide format; the judge decides content against each case's authored expectation. See `results/README.md` to re-derive any number.

## Headlines

- **Misleading claims: 0/20** (the dangerous error — a wrong grammar claim spoken aloud)
- **Meets expectation: 0.800** (did the reply do the job the turn required, per its rubric)
- **Explanation in English (judge): 1.000** · spoken line English (deterministic): 0.750
- **Split format valid: 1.000** (spoken line present + markdown-free) · breakdown present 1.000

## Spoken-line speakability (non-garbled turns)

The first line is read aloud, so it must be one short sentence. Word count — p50 **15**, p95 **30**, max **30** (over 40 words = too long to speak). Speakable rate 1.000, markdown-free 1.000.

## Behaviour slices

- **Noise robustness** (garbled turns): correctly handled **0.250** — i.e. asked the learner to clarify instead of inventing a correction for the noise. (The `asks_to_repeat` judge flag, 0.500, is NOT a reliable noise signal: the coach's trailing 'try saying …' drill reads to the judge as a repeat request even when it fabricated a correction — so meets_expectation is the metric here.)
- **History grounding** (referential turns): meets-expectation 1.000; wrongly asked to repeat 1/4 (the context already held the answer).

## By turn type

| Type | n | meets_expectation | misleading | English |
|---|---|---|---|---|
| sentence_coach | 6 | 0.833 | 0 | 1.000 |
| question | 6 | 1.000 | 0 | 1.000 |
| referential | 4 | 1.000 | 0 | 1.000 |
| garbled | 4 | 0.250 | 0 | 1.000 |

## Did not meet expectation

- `sc05` (sentence_coach) — _control — a correct sentence must not be 'corrected'_: The coach incorrectly suggests that the learner's sentence is not natural and offers an alternative, rather than affirming the correctness of the original sentence.
  - spoken: `"Please give me a glass of water" is correct, but a more natural way to say it in Mandarin is "请给我一杯水。"`
- `g02` (garbled) — _mixed-noise mis-transcription_: The coach fails to recognize that the learner's turn is unintelligible and instead fabricates a correction, which does not meet the expectation.
  - spoken: `Your sentence is not correct and doesn't make sense in Mandarin.`
- `g03` (garbled) — _failed romanised STT_: The coach does not recognize the learner's unintelligible turn and instead provides a correction, which does not meet the expectation of asking the learner to repeat.
  - spoken: `Your sentence needs some corrections for clarity and naturalness.`
- `g04` (garbled) — _mostly-inaudible turn_: The coach does not ask the learner to repeat the inaudible part, instead providing an explanation about 的 without addressing the incompleteness of the learner's turn.
  - spoken: `It seems like your sentence is incomplete, but I can help clarify the use of 的.`

## Caveats

- **Small hand-authored set (n=20), our rubrics.** Deterministic format/speakability numbers are exact; the content verdicts are one judge's call — vet with `--verify-judge <model>` (agreement in the JSON). The garbled slice is only n=4, so its rate is directional.
- **The coach runs at production temperature (0.2), so its replies — and therefore the judge-based rates — vary run to run.** The findings note reports the spread across repeated runs; the deterministic format checks are stable.
- **The judge scores against an authored EXPECTATION, not a single reference string** — multiple correct explanations pass, matching how the text-coach correction judge works.
- **The deterministic spoken-line-English rate understates compliance**: the prompt asks the headline to include the corrected Chinese sentence, so a legitimate headline can exceed the 15% Han-ratio threshold. The judge's explanation_in_english (on the prose) is the truer English signal.
