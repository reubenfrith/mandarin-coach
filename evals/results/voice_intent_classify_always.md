# Voice router — classify-always arm

Counterfactual: skip the script heuristic and send **every** turn to the LLM classifier (gpt-4o-mini). Answers "should we just classify everything?". Each of the 40 turns is classified **3×** (classifier temp 0.2 is nondeterministic); the majority vote is the pred and the spread across runs is reported.

## Classify-always vs the production router (majority vote)

| Metric | Router (heuristic+classifier) | Classify-always | Δ |
|---|---|---|---|
| Coach precision (headline) | 1.000 | 0.947 | -0.053 |
| Converse→coach misroute | 0.000 | 0.045 | +0.045 |
| Accuracy | 1.000 | 0.975 | -0.025 |

Classify-always confusion (coach = positive): TP 18 FP 1 FN 0 TN 21.

## Spread across runs (the classifier is nondeterministic)

- Coach precision: **0.947 (min 0.947 / max 0.947)**
- Converse→coach misroute: 0.045 (min 0.045 / max 0.045)
- Accuracy: 0.975 (min 0.975 / max 0.975)
- Unstable turns (votes disagreed across the 3 runs): **0**

## Head-to-head vs the router (per turn)

- **Fixed** (router misrouted → classify-always correct): **0**
- **Regressed** (router correct → classify-always misrouted — the cost of taxing every turn with a nondeterministic LLM): **1**
- Both right: 39 · both wrong: 0 (of 40 compared)

### Regressed (the heuristic was protecting these)

- `z02` (empty, router path: heuristic): `？？？` → FP · _no content_

## Read this with the latency caveat

This surface measures **accuracy only**. Classify-always also puts an LLM call (temp 0.2, nondeterministic) on the critical path of *every* spoken turn — including the plain-Mandarin conversation turns the heuristic resolves instantly and with zero misroute risk. Weigh any accuracy gain here against that per-turn latency + the regressions above before changing the architecture. Full reasoning + decision rule: `notes/voice-router-findings.md`.
