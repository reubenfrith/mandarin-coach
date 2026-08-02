# Voice-coach quality eval — `run_voice_coach`

20 spoken-coach turns through the real voice coach (**gpt-4o-mini** + grammar tools); judge = **gpt-4o** (independent, temp 0). Scores the behaviours the text-coach evals don't cover: the spoken-TL;DR format, English-only explanation, noise→ask-to-repeat, and resolving referential turns from spoken history. Deterministic checks decide format; the judge decides content against each case's authored expectation. See `results/README.md` to re-derive any number.

## Headlines

- **Misleading claims: 3/20** (the dangerous error — a wrong grammar claim spoken aloud; ids: sc05, g02, g03)
- **Meets expectation: 0.850** (did the reply do the job the turn required, per its rubric)
- **Explanation in English (judge): 1.000** · spoken line English (deterministic): 0.750
- **Split format valid: 1.000** (spoken line present + markdown-free) · breakdown present 1.000

## Spoken-line speakability (non-garbled turns)

The first line is read aloud, so it must be one short sentence. Word count — p50 **15**, p95 **20**, max **20** (over 40 words = too long to speak). Speakable rate 1.000, markdown-free 1.000.

## Behaviour slices

- **Noise robustness** (garbled turns): correctly handled **0.500** — i.e. asked the learner to clarify instead of inventing a correction for the noise. (The `asks_to_repeat` judge flag, 0.500, is NOT a reliable noise signal: the coach's trailing 'try saying …' drill reads to the judge as a repeat request even when it fabricated a correction — so meets_expectation is the metric here.)
- **History grounding** (referential turns): meets-expectation 1.000; wrongly asked to repeat 0/4 (the context already held the answer).

## By turn type

| Type | n | meets_expectation | misleading | English |
|---|---|---|---|---|
| sentence_coach | 6 | 0.833 | 1 | 1.000 |
| question | 6 | 1.000 | 0 | 1.000 |
| referential | 4 | 1.000 | 0 | 1.000 |
| garbled | 4 | 0.500 | 2 | 1.000 |

## Misleading claims (inspect — spoken to the learner)

- `sc05` (sentence_coach): The reply incorrectly suggests that the learner's sentence is less natural, which is misleading since the original sentence is already correct and natural.
  - spoken: `Please say "给我一杯水" for a more natural request.`
- `g02` (garbled): The reply incorrectly attempts to correct the garbled sentence instead of asking the learner to repeat, and it misleadingly suggests '我在' for 'I was,' which is incorrect.
  - spoken: `Your sentence is not correct and doesn't make sense in Mandarin.`
- `g03` (garbled): The reply incorrectly assumes the learner's intent and provides a Mandarin sentence instead of asking for repetition.
  - spoken: `Your sentence needs some adjustments for clarity and correctness. A more natural way to say it would be "我去的地方是..." (Wǒ qù de dìfāng shì...), meaning "The place I am going to is...".`

## Did not meet expectation

- `sc05` (sentence_coach) — _control — a correct sentence must not be 'corrected'_: The reply incorrectly suggests that the learner's sentence is less natural, which is misleading since the original sentence is already correct and natural.
  - spoken: `Please say "给我一杯水" for a more natural request.`
- `g02` (garbled) — _mixed-noise mis-transcription_: The reply incorrectly attempts to correct the garbled sentence instead of asking the learner to repeat, and it misleadingly suggests '我在' for 'I was,' which is incorrect.
  - spoken: `Your sentence is not correct and doesn't make sense in Mandarin.`
- `g03` (garbled) — _failed romanised STT_: The reply incorrectly assumes the learner's intent and provides a Mandarin sentence instead of asking for repetition.
  - spoken: `Your sentence needs some adjustments for clarity and correctness. A more natural way to say it would be "我去的地方是..." (Wǒ qù de dìfāng shì...), meaning "The place I am going to is...".`

## Caveats

- **Small hand-authored set (n=20), our rubrics.** Deterministic format/speakability numbers are exact; the content verdicts are one judge's call — vet with `--verify-judge <model>` (agreement in the JSON). The garbled slice is only n=4, so its rate is directional.
- **The coach runs at production temperature (0.2), so its replies — and therefore the judge-based rates — vary run to run.** The findings note reports the spread across repeated runs; the deterministic format checks are stable.
- **The judge scores against an authored EXPECTATION, not a single reference string** — multiple correct explanations pass, matching how the text-coach correction judge works.
- **The deterministic spoken-line-English rate understates compliance**: the prompt asks the headline to include the corrected Chinese sentence, so a legitimate headline can exceed the 15% Han-ratio threshold. The judge's explanation_in_english (on the prose) is the truer English signal.
