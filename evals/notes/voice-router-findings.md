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

## Open question: "should we just use the classifier for every turn?"

Tempting read of Finding 1: the heuristic causes 100% of the errors, so drop it and classify
everything. **On the current evidence this is not a fair conclusion.**

**Why the evidence doesn't support it.** The eval never ran the classifier on the 30
heuristic-resolved turns — the English glue and the Mandarin questions. "The classifier would
fix those" is an untested extrapolation from 10 cases (6 uncontested). It's a *plausible*
hypothesis (the prompt literally lists "and you?" as converse), but a hypothesis, not a result.

**Why it's probably the wrong design even if it scored well.**

- **Latency is the whole reason the heuristic exists.** It resolves 75% of turns with zero LLM
  round-trip. Classify-always taxes *every* turn — including the overwhelmingly common
  plain-Mandarin conversation turn — with a classifier call, on a pipeline the plan fought to
  keep fast (someone is holding a mic).
- **It could *increase* the jarring failure on the common path.** On plain Mandarin the
  heuristic is a guaranteed-correct, instant "converse". Handing those to a nondeterministic
  temp-0.2 LLM introduces a nonzero chance of misrouting normal chat to an English lecture —
  where today that chance is exactly zero.
- **The classifier has failure modes the heuristic doesn't** — timeouts / malformed output
  (it falls back to converse on error). Fine as a tiebreaker; wasteful and riskier as the
  sole router.

**The better-supported move** is not "nuke the heuristic" but "widen *when the classifier
fires*": carve short English affirmations/glue out of `Latin→coach`, and escalate Han-only
turns that look interrogative (吗 / 什么 / 为什么 / 怎么 / 呢 / ？) to the classifier instead of
auto-converse. That keeps the latency win on the easy ~90% and spends the LLM call only on the
genuinely ambiguous turns.

## How we'll actually settle it — the "classify-always" arm (planned)

Add a second arm to `voice_intent_eval` that runs `classify_turn_intent` over **all 40** turns
(ignoring the heuristic) and compare against the current router. It's ~40 cheap calls and turns
the hypothesis into evidence. Decision rule:

- **classify-always wins big on accuracy AND per-turn latency is tolerable** → reconsider the
  architecture.
- **it merely ties a tuned-heuristic path** → latency breaks the tie; keep the heuristic and
  apply the two targeted fixes above.

Because the classifier is nondeterministic, run the arm a few times (or pin `temperature=0`
for the eval) and report the spread, not a single number.

## Follow-on changes (tracked, harness-evidenced by this surface)

1. **Heuristic refinement** — short English affirmations → converse; interrogative Han-only
   turns → classifier. Re-run this surface before/after; the before is `results/voice_intent.md`.
2. **Proper-noun policy** — decide whether proper nouns stay in conversation; if yes, add the
   prompt carve-out (Finding 3).
3. **classify-always arm** — the experiment above, to answer the open question with data.
