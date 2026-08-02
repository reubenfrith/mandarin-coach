# Voice-router intent eval — `_route_intent`

Classifier model **gpt-4o-mini** (mixed-script turns only; 30/40 cases are resolved by the zero-latency script heuristic with no LLM call). Coach is the positive class: a CONVERSE turn routed to COACH is the jarring false positive the router is tuned to avoid. See `results/README.md` for how to re-derive any number.

## Routing decision (coach = positive)

| | Predicted coach | Predicted converse |
|---|---|---|
| **Actually coach** | TP 13 | FN 5 |
| **Actually converse** | FP 5 | TN 17 |

- **Coach precision 0.722** (headline — a false positive is the jarring converse→coach misroute)
- **Converse→coach misroute rate 0.227** (5 of 22 conversation turns force-routed to a lecture)
- Coach recall 0.722 · Coach F1 0.722 (a missed coach turn degrades gracefully — the partner still corrects inline)
- Converse precision 0.773 · recall 0.773
- Overall accuracy 0.750

## Per-bucket accuracy (heuristic error vs classifier error, kept separate)

Bucket = the script the heuristic sees, which fixes the code path. Pure buckets are labelled by TRUE intent, so they are NOT guaranteed correct — the adversarial cases (English glue, Mandarin questions) are exactly where the heuristic loses.

| Bucket | Path | n | Accuracy | FP (→coach) | FN (→converse) |
|---|---|---|---|---|---|
| mandarin | heuristic | 15 | 0.667 | 0 | 5 |
| english | heuristic | 12 | 0.583 | 5 | 0 |
| mixed | classifier | 10 | 1.000 | 0 | 0 |
| empty | heuristic | 3 | 1.000 | 0 | 0 |

**Classifier alone** (the 10 mixed turns): 0 FP / 0 FN (TP 6 FP 0 FN 0 TN 4) — **treat as *no errors observed, not a validation*** (see caveats).

## Findings & caveats

- **The robust, headline finding — 100% of misroutes are the HEURISTIC's, not the classifier's.** Every false positive is short English glue the `Latin→coach` rule routes to a lecture *without ever calling the classifier*; every false negative is a Mandarin question the `Han→converse` rule sends to chat. This rests on unambiguous labels, is deterministic, and is directly actionable: **the calibration target is the script heuristic** (e.g. route short English affirmations to converse; let the classifier see Han-only turns that look interrogative — 吗/什么/为什么/怎么/呢/？).
- **The classifier slice is NOT a validation.** n=10 is small; the classifier runs at the production temperature (`get_llm` default 0.2, **nondeterministic** — a rerun may differ); and **4 of the 10 labels are contestable** against the deployed prompt.
- **Prompt/intent misalignment this surface exposes.** `INTENT_CLASSIFIER_PROMPT` mandates coach for ALL code-switching (`我很喜欢 hiking` → coach). We labelled proper-noun code-switches (`去 Melbourne 玩`, `Netflix`, `Starbucks`, `David`) as **converse** — a learner naming a place/brand isn't asking to be taught the word. So the classifier returning converse there *deviates* from its own instructions, and our label rewards the deviation. If the product wants proper nouns left in conversation, the fix is a **proper-noun carve-out in the prompt**, not a claim the classifier is already correct.

## False positives — conversation routed to coach (the jarring failure — inspect)

- `e08` (heuristic, english): `And you?` · _english-but-converse: the classifier prompt itself lists this as converse; heuristic force-routes it to coach_
- `e09` (heuristic, english): `Yeah, exactly.` · _english-but-converse: agreement, not a question_
- `e10` (heuristic, english): `Haha okay.` · _english-but-converse: filler_
- `e11` (heuristic, english): `One sec.` · _english-but-converse: aside_
- `e12` (heuristic, english): `Me too!` · _english-but-converse: agreement_

## False negatives — coach question routed to converse (graceful miss)

- `m11` (heuristic, mandarin): `这个词是什么意思？` · _mandarin-but-coach: asks a word's meaning; heuristic sends it to converse_
- `m12` (heuristic, mandarin): `这样说对吗？` · _mandarin-but-coach: is this correct?_
- `m13` (heuristic, mandarin): `刚才那个句子为什么不对？` · _mandarin-but-coach: why was that wrong?_
- `m14` (heuristic, mandarin): `“把”和“被”有什么区别？` · _mandarin-but-coach: grammar contrast question (quotes are full-width Han)_
- `m15` (heuristic, mandarin): `再给我一个例子好吗？` · _mandarin-but-coach: give me another example_
