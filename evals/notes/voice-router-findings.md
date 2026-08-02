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

### The latency cost, now measured

`--latency 12` (12 sequential `classify_turn_intent` calls, gpt-4o-mini): **p50 ≈ 790 ms, p95
≈ 1.77 s, mean ≈ 910 ms**. Against the plan's ~2.3 s full-turn baseline that's **~34% of a turn
(p50)** added to *every* turn classify-most would take over from the heuristic — i.e. ~0.8 s
tacked onto the plain-Mandarin conversation turns (75% of traffic) that today route in ~0 ms.
The classifier runs *after* STT (it needs the transcript), so this is serial, not hidden. It's
an eval-time marginal estimate, not production-under-load — but it's the real order of
magnitude. Reproduce: `voice_intent_eval.py --latency 12`.

**This tips the default toward the tuned heuristic, not classify-most.** Trading ~0.8 s on
*every* conversational turn for +0.225 accuracy is a poor deal on a mic-held pipeline, when a
tuned heuristic can likely recover the same 10 fixes while paying the classifier only on
genuinely ambiguous turns. Classify-most becomes attractive only if that call is driven down
(temp 0, a faster/cheaper classifier, or overlapping it with STT/response) or the deployment
can absorb the latency.

### What the evidence does NOT settle

- **Scope: n=40, one dataset, our labels** — including the 4 contestable proper-noun labels
  (Finding 3), which classify-always also benefits from. But the core result is robust to them:
  the 10 fixes are all unambiguous, and only `？？？` regresses (the regression count is what
  touches those labels, and it stays at 1).
- **Stability is measured on 3 runs.** More repeats could surface some; 3× identical is decent
  but not proof of determinism at temp 0.2.
- **The head-to-head is majority-of-3 (classify-always) vs a single temp-0.2 draw (the router
  baseline in `voice_intent.json`).** It doesn't affect *this* result — every decisive delta is
  a deterministic heuristic-path turn — but only **heuristic-path deltas are fully trustworthy**.
  If someone re-runs and a *mixed*-path turn flips in the single-draw baseline, the head-to-head
  could show a phantom fix/regression. Regenerate the baseline as majority-of-3 before trusting
  any mixed-path delta.

### Recommended design (harness-evidenced)

1. **Tuned heuristic — the recommended default.** Apply the two targeted fixes below (short
   English affirmations → converse; interrogative Han-only turns → classifier), keeping the
   empty→converse guard. They target *exactly* the 10 cases classify-always fixed, so the data
   predicts they recover most of the gain while keeping the ~0.8 s classifier call off the 75%
   of turns that don't need it. Verify with a before/after run (`before` = `voice_intent.md`).
2. **Classify-most — only if the latency is bought down or affordable.** Keep a trivial
   **empty/no-content guard → converse** (the one thing classify-always got wrong), drop the two
   script rules, classify the rest. Best accuracy (0.975), worst per-turn latency.
   **Critical:** under classify-most the classifier's error/timeout fallback must be the
   **heuristic**, not `converse`. `classify_turn_intent` currently falls back to converse; today
   a classifier outage still routes pure-English→coach via the heuristic, but under classify-most
   an outage would send *everything* to converse — making the coach unreachable for exactly the
   English-question case that matters most.

## Follow-on changes (tracked, harness-evidenced by this surface)

1. **Tuned heuristic (recommended default)** — short English affirmations → converse;
   interrogative Han-only turns (吗/什么/为什么/怎么/呢/？) → classifier; keep the empty guard.
   Re-run this surface before/after; the before is `results/voice_intent.md`. This is the
   latency-preserving path the measured ~0.8 s classifier call points to.
2. **If going classify-most instead** — add the empty→converse guard and switch
   `classify_turn_intent`'s error fallback to the heuristic (not converse); consider driving the
   classifier latency down (temp 0 / faster model / overlap with STT).
3. **Proper-noun policy** — decide whether proper nouns stay in conversation; if yes, add the
   prompt carve-out (Finding 3). Affects both paths (the classifier currently keeps them in
   converse, deviating from its prompt).
4. **Before trusting mixed-path head-to-head deltas** — regenerate `voice_intent.json` as
   majority-of-3 so it denoises the same way the classify-always arm does.
