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

**So the classifier is clearly competent enough** — the two blunt script rules (`Latin→coach`,
`Han→converse`) cost more than they save. This proved the *fix* is real; it did NOT prove that
*classify-everything* is the right design, because that trades latency on every turn (next). (The
`Router` column above = the ORIGINAL router; `voice_intent.json` now holds the **tuned** router,
so a fresh `--classify-always` run compares against that — see "Implemented" below.)

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

## Implemented: the tuned heuristic (before/after)

We replaced the two blunt rules with a **fast-path-the-unambiguous** heuristic (`_heuristic_route`
in `app/voice_api.py`): a plain Mandarin **statement**, a short English aside (≤ 2 words), and an
empty turn resolve instantly to converse; **Mandarin questions** (吗/什么/为什么/怎么/呢/？…),
**longer English**, and **mixed script** go to the classifier. Before/after on this surface:

| Metric | Original router | **Tuned heuristic** | Classify-always (ceiling) |
|---|---|---|---|
| Coach precision | 0.72 | **1.00** | 0.95 |
| Converse→coach misroute | 0.23 | **0.00** | 0.045 |
| Accuracy | 0.75 | **1.00** | 0.975 |

- **Tuned = 1.00 across 3 runs** (stable — the classifier-resolved turns didn't flip). It even
  edges out classify-always, because the empty guard catches `？？？` (classify-always's lone regression).
- **Re-running `--classify-always` against the tuned router now shows fixed 0, regressed 1.** So
  classifying every turn no longer helps and is strictly *worse* (regresses `？？？`, +0.8 s on every
  turn). The tuned heuristic **dominates**: equal-or-better accuracy at a fraction of the classifier calls.
- **Routes 24/40 to the classifier on THIS set, 16/40 on the heuristic** — but the set is adversarially
  dense with questions/English/mixed. In real traffic plain-Mandarin **statements** dominate, so the
  heuristic share is much higher and the ~0.8 s call lands only when the surface form is genuinely
  ambiguous. That is the whole point.

### Caveats on the 1.00

- **n=40, our labels, incl. the 4 contestable proper-noun turns** (Finding 3): the classifier routes
  them to converse, matching our labels but *deviating from the deployed prompt*. Under the prompt's
  own rule (code-switch → coach) those 4 would be FN, dropping accuracy to ~0.90 — but **coach
  precision stays 1.00 either way** (no FP). So "perfect" rests partly on a labelling choice; resolve
  the proper-noun policy to make it unconditional.
- **The classifier-resolved turns are nondeterministic** (temp 0.2); 3× stable here is decent, not proof.

## Follow-on changes (tracked)

1. **Proper-noun policy** — decide whether proper nouns stay in conversation. If yes, add a carve-out
   to `INTENT_CLASSIFIER_PROMPT` so the classifier's converse verdict on `去 Melbourne 玩` follows the
   prompt instead of contradicting it. This is the one open labelling ambiguity behind the 1.00.
2. **In-browser confirmation** — the surface proves routing on transcripts; confirm on real mic audio
   that a Mandarin question triggers the coach without a jarring pause from the added classifier call.
3. **Knobs if real traffic shows misses** — `_ENGLISH_GLUE_MAX_WORDS` and the `_ZH_QUESTION_MARKERS`
   set are single dials in `voice_api.py`, re-scored by this surface. If ever moving to classify-most,
   switch `classify_turn_intent`'s error fallback from `converse` to the heuristic first (an outage
   would otherwise make the coach unreachable for English questions).
