# Voice-router intent eval — `_route_intent`

Classifier model **gpt-4o-mini** (16/40 cases resolved by the zero-latency heuristic with no LLM call; 24 ambiguous turns — Mandarin questions, substantive English, mixed script — hit the classifier). Coach is the positive class: a CONVERSE turn routed to COACH is the jarring false positive the router is tuned to avoid. See `results/README.md` for how to re-derive any number.

## Routing decision (coach = positive)

| | Predicted coach | Predicted converse |
|---|---|---|
| **Actually coach** | TP 18 | FN 0 |
| **Actually converse** | FP 0 | TN 22 |

- **Coach precision 1.000** (headline — a false positive is the jarring converse→coach misroute)
- **Converse→coach misroute rate 0.000** (0 of 22 conversation turns force-routed to a lecture)
- Coach recall 1.000 · Coach F1 1.000 (a missed coach turn degrades gracefully — the partner still corrects inline)
- Converse precision 1.000 · recall 1.000
- Overall accuracy 1.000

## Per-bucket accuracy (script bucket × which stage resolved it)

Bucket = the SCRIPT of the turn; labelled by TRUE intent. The tuned router splits WITHIN a bucket — plain Mandarin statements stay on the heuristic, Mandarin questions go to the classifier — so the heuristic/classifier column shows how each bucket was resolved.

| Bucket | heur/clf | n | Accuracy | FP (→coach) | FN (→converse) |
|---|---|---|---|---|---|
| mandarin | 8/7 | 15 | 1.000 | 0 | 0 |
| english | 5/7 | 12 | 1.000 | 0 | 0 |
| mixed | 0/10 | 10 | 1.000 | 0 | 0 |
| empty | 3/0 | 3 | 1.000 | 0 | 0 |

**Classifier-resolved turns** (24 of 40): 0 FP / 0 FN (TP 18 FP 0 FN 0 TN 6).

## Caveats

- **The classifier is nondeterministic** — it runs at the production temperature (`get_llm` default 0.2), so the classifier-resolved turns can differ run to run. The heuristic-resolved turns are deterministic.
- **Small, single dataset (n=40), our labels.** Four mixed proper-noun turns (`去 Melbourne 玩`, `Netflix`, `Starbucks`, `David`) are labelled **converse**, which contests the deployed `INTENT_CLASSIFIER_PROMPT` (it mandates coach for ALL code-switching). If the product wants proper nouns left in conversation, that's a prompt carve-out — see the findings note.
- **Full narrative, the classify-always counterfactual, latency, and the routing history are in [`notes/voice-router-findings.md`](../../notes/voice-router-findings.md).**
