# Voice router — findings & open questions

Evidence log for the voice-coach intent router (`app/voice_api.py` `_route_intent`), backed by
the `voice_intent_eval` surface (`surfaces/voice_coach/`, results in `results/voice_intent.md`).
This is a decision record: it exists so we don't re-litigate the "just use the classifier for
everything" question from memory.

## What the router is

Two stages decide which brain answers each spoken turn — the Mandarin conversation partner
(`converse`) or the English coach (`coach`):

1. a **zero-latency script heuristic** — `Latin-only → coach`, `Han-only / empty → converse` —
   which resolves the clear cases with **no LLM call**;
2. an **LLM classifier** (`classify_turn_intent`, gpt-4o-mini) that fires **only on a
   mixed-script turn** (Han *and* Latin).

Design bias is **precision-first toward converse**: a converse turn misrouted to coach (an
English lecture when you wanted to talk) is the *jarring* failure; a coach turn misrouted to
converse degrades gracefully because the partner still corrects inline. So coach is the
positive class and **coach precision is the headline**.

## The measured result (40 hand-labelled turns, gpt-4o-mini)

| Metric | Value |
|---|---|
| Coach precision (headline) | **0.72** |
| Converse→coach misroute rate | **0.23** (5 of 22 conversation turns) |
| Coach recall / F1 | 0.72 / 0.72 |
| Overall accuracy | 0.75 |
| Turns resolved with no LLM call | 30 / 40 |

Dataset is bucketed by **script** (which fixes the code path) but labelled by **true intent**,
so each pure bucket carries heuristic-adversarial cases — that's what stops it saturating at
1.0. Per-bucket accuracy (from `results/voice_intent.md`):

| Bucket | Path | n | Accuracy | Where it loses |
|---|---|---|---|---|
| mandarin | heuristic | 15 | 0.67 | 5 Mandarin **questions** → forced to converse (graceful FN) |
| english | heuristic | 12 | 0.58 | 5 English **glue** turns ("and you?", "me too") → forced to coach (jarring FP) |
| mixed | classifier | 10 | 1.00 | — 0 FP / 0 FN |
| empty | heuristic | 3 | 1.00 | — |

## Finding 1 (robust, deterministic) — every misroute is the HEURISTIC's, not the classifier's

All 5 false positives are short English glue the `Latin→coach` rule sends to a lecture
**without ever calling the classifier**. All 5 false negatives are Mandarin questions the
`Han→converse` rule sends to chat. The classifier itself made **no observed errors** on the 10
mixed turns. This rests on unambiguous labels, is deterministic, and is **directly
actionable**: the calibration target is the *script heuristic*.

## Finding 2 (caveated) — the classifier's 10/10 is "no errors observed", NOT a validation

Do not over-read the mixed-bucket 1.0. Three compounding reasons:

1. **n = 10** — a wide interval, not "flawless".
2. **Nondeterministic** — `classify_turn_intent` runs at the `get_llm` default `temperature=0.2`
   (production-faithful, but a rerun can differ). The heuristic half has no such risk.
3. **4 of the 10 labels are contestable** — see Finding 3.

## Finding 3 (a real misalignment this surface exposes) — the prompt over-mandates coach

`INTENT_CLASSIFIER_PROMPT` says code-switching → coach **unconditionally** ("我很喜欢 hiking"
→ coach). But we labelled proper-noun code-switches ("去 Melbourne 玩", Netflix, Starbucks,
David) as **converse** — a learner naming a place/brand isn't asking to be taught the word. So
when the classifier returns converse there it is *deviating from its own prompt*, and our label
rewards the deviation. If we want proper nouns left in conversation, the fix is a **proper-noun
carve-out in the prompt** — not a claim the classifier is already correct.

---

## Resolved with data: "should we just use the classifier for every turn?"

We ran the **classify-always arm** — `classify_turn_intent` over **all 40** turns, skipping the
heuristic, each turn classified 3× (temp 0.2 is nondeterministic). Command:
`voice_intent_eval.py --classify-always --repeats 3`; results in
`results/voice_intent_classify_always.md`. Outcome vs the production router:

| Metric | Router (heuristic+classifier) | Classify-always | Δ |
|---|---|---|---|
| Coach precision | 0.72 | **0.95** | +0.23 |
| Converse→coach misroute | 0.23 | **0.045** | −0.18 |
| Accuracy | 0.75 | **0.975** | +0.23 |

Per-turn head-to-head: **fixed 10, regressed 1, 0 unstable** across the 3 runs.

- It **fixed all 10** heuristic misroutes — the 5 English-glue FPs ("and you?", "me too") *and*
  the 5 Mandarin-question FNs ("这个词是什么意思？"). So Finding 1's hypothesis (the classifier
  would handle the turns the heuristic fumbles) is now **supported**, not extrapolated.
- It **regressed exactly 1**: `z02` = `？？？` (punctuation only), which the classifier reads as a
  question and sends to coach. The heuristic correctly routes no-content turns to converse.
- **0 turns were unstable** — every turn voted identically across 3 runs. The temp-0.2
  nondeterminism worry (Finding 2) was real in principle but did not bite on these 40 turns.

**So on ACCURACY, classify-most clearly wins.** The two blunt script rules (`Latin→coach`,
`Han→converse`) cost more than they save. The decision is no longer "is the classifier good
enough" — it is now purely a **latency/cost** question this surface cannot measure.

### What the evidence does NOT settle

- **Latency is unmeasured here.** Classify-always puts an LLM call (temp 0.2) on the critical
  path of *every* spoken turn, including the overwhelmingly common plain-Mandarin conversation
  turn the heuristic resolves in ~0 ms. On a mic-held pipeline the plan fought to keep fast,
  that per-turn cost is the real tradeoff — weigh it before adopting.
- **Scope: n=40, one dataset, our labels** — including the 4 contestable proper-noun labels
  (Finding 3), which classify-always also benefits from. But the core result is robust to them:
  the 10 fixes are all unambiguous, and only `？？？` regresses.
- **Stability is measured on 3 runs.** More repeats could surface some; 3× identical is decent
  but not proof of determinism at temp 0.2.

### Recommended design (harness-evidenced)

Two viable paths; pick on the latency budget:

1. **Classify-most** (if an LLM call per turn is affordable): keep a trivial **empty/no-content
   guard → converse** (it's the only thing classify-always got wrong), drop the two script
   rules, classify everything else. Best accuracy.
2. **Tuned heuristic** (if plain-Mandarin turns must stay LLM-free): apply the two targeted
   fixes below. They target *exactly* the 10 cases classify-always fixed, so the data predicts
   they recover most of the gain without taxing every turn — but that's a prediction to verify
   with its own before/after run, not a measured result.

## Follow-on changes (tracked, harness-evidenced by this surface)

1. **Decide the latency budget**, then pick path 1 or 2 above.
2. **Heuristic refinement (path 2)** — short English affirmations → converse; interrogative
   Han-only turns (吗/什么/为什么/怎么/呢/？) → classifier; keep the empty guard. Re-run this
   surface before/after; the before is `results/voice_intent.md`.
3. **Proper-noun policy** — decide whether proper nouns stay in conversation; if yes, add the
   prompt carve-out (Finding 3). Affects both paths (the classifier currently keeps them in
   converse, deviating from its prompt).
