# Tone auto-logging eval — `pronounce_api._log_tone_error`

The gate before the pronunciation coach is trusted to write tone errors into the learner's corpus. We score the **effective logging predicate** — *would this syllable be logged as a tone error?* — on a labeled synthetic set, and sweep a confidence gate on it. **Precision is the headline**: a false positive logs a correctly-said syllable as a mistake and poisons the per-user corpus (same discipline as the extraction surface).

> **Scope / honesty.** Gold labels are *perturbation-defined* on clean synthetic voicing — we chose both the distortion and its label — so these are an **upper bound** on real-L2 precision, not a human-accuracy figure. The `clean` band is separable by construction (a sanity floor); the `borderline` band (near-miss same-category vs neighbour-crossing, esp. T2↔T3) is where the threshold is decided. Creaky/L2 validation (CREPE, real recordings) is Phase 2.

**Decision — add a margin gate at `LOG_MARGIN = 0.067`.** The production predicate (log on any label mismatch, threshold 0) scores precision 0.833 with 8 false positive(s); gating on classifier margin ≥ 0.067 lifts precision to 1.000 (recall 1.000→0.950). Wire it into the `if not v['ok']` branch of `pronounce_api.py`.

Dataset: **80** cases (40 correct / 40 wrong), 0 unvoiced. See `results/README.md` to re-derive any number.

## Predicate: production (margin 0) vs recommended gate

| | Threshold | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|
| **Production today** | 0.000 | 40 | 8 | 0 | 32 | **0.833** | 1.000 | 0.909 |
| **Recommended** | 0.067 | 38 | 0 | 2 | 40 | **1.000** | 0.950 | 0.974 |

## By band

| Band | Precision @0 | Recall @0 | Precision @rec | Recall @rec |
|---|---|---|---|---|
| **clean** | 1.000 | 1.000 | 1.000 | 1.000 |
| **borderline** | 0.667 | 1.000 | 1.000 | 0.875 |

The `clean` band is separable by construction — if precision dips there the DSP is broken, not miscalibrated. The `borderline` band carries the real signal.

## Margin sweep (the calibration curve)

Each row raises the confidence gate to just above one observed mismatch-margin; raising it only ever removes a log, so precision climbs and recall falls monotonically.

| Threshold | TP | FP | FN | TN | Precision | Recall |
|---|---|---|---|---|---|---|
| 0.000 | 40 | 8 | 0 | 32 | 0.833 | 1.000 |
| 0.013 | 40 | 7 | 0 | 33 | 0.851 | 1.000 |
| 0.019 | 40 | 6 | 0 | 34 | 0.870 | 1.000 |
| 0.025 | 40 | 5 | 0 | 35 | 0.889 | 1.000 |
| 0.036 | 40 | 4 | 0 | 36 | 0.909 | 1.000 |
| 0.046 | 39 | 4 | 1 | 36 | 0.907 | 0.975 |
| 0.052 | 38 | 4 | 2 | 36 | 0.905 | 0.950 |
| 0.056 | 38 | 3 | 2 | 37 | 0.927 | 0.950 |
| 0.059 | 38 | 2 | 2 | 38 | 0.950 | 0.950 |
| 0.064 | 38 | 1 | 2 | 39 | 0.974 | 0.950 |
| 0.067 | 38 | 0 | 2 | 40 | 1.000 | 0.950 |  ← recommended
| 0.072 | 37 | 0 | 3 | 40 | 1.000 | 0.925 |
| 0.085 | 36 | 0 | 4 | 40 | 1.000 | 0.900 |
| 0.096 | 35 | 0 | 5 | 40 | 1.000 | 0.875 |
| 0.098 | 34 | 0 | 6 | 40 | 1.000 | 0.850 |
| 0.101 | 33 | 0 | 7 | 40 | 1.000 | 0.825 |
| 0.107 | 32 | 0 | 8 | 40 | 1.000 | 0.800 |
| 0.114 | 31 | 0 | 9 | 40 | 1.000 | 0.775 |
| 0.117 | 30 | 0 | 10 | 40 | 1.000 | 0.750 |
| 0.118 | 29 | 0 | 11 | 40 | 1.000 | 0.725 |
| 0.119 | 28 | 0 | 12 | 40 | 1.000 | 0.700 |
| 0.121 | 27 | 0 | 13 | 40 | 1.000 | 0.675 |
| 0.126 | 26 | 0 | 14 | 40 | 1.000 | 0.650 |
| 0.129 | 25 | 0 | 15 | 40 | 1.000 | 0.625 |
| 0.134 | 24 | 0 | 16 | 40 | 1.000 | 0.600 |
| 0.140 | 23 | 0 | 17 | 40 | 1.000 | 0.575 |
| 0.160 | 22 | 0 | 18 | 40 | 1.000 | 0.550 |
| 0.187 | 20 | 0 | 20 | 40 | 1.000 | 0.500 |
| 0.198 | 19 | 0 | 21 | 40 | 1.000 | 0.475 |
| 0.205 | 18 | 0 | 22 | 40 | 1.000 | 0.450 |
| 0.218 | 17 | 0 | 23 | 40 | 1.000 | 0.425 |
| 0.230 | 16 | 0 | 24 | 40 | 1.000 | 0.400 |
| 0.245 | 15 | 0 | 25 | 40 | 1.000 | 0.375 |
| 0.261 | 14 | 0 | 26 | 40 | 1.000 | 0.350 |
| 0.268 | 13 | 0 | 27 | 40 | 1.000 | 0.325 |
| 0.275 | 12 | 0 | 28 | 40 | 1.000 | 0.300 |
| 0.291 | 11 | 0 | 29 | 40 | 1.000 | 0.275 |
| 0.311 | 10 | 0 | 30 | 40 | 1.000 | 0.250 |
| 0.341 | 9 | 0 | 31 | 40 | 1.000 | 0.225 |
| 0.363 | 8 | 0 | 32 | 40 | 1.000 | 0.200 |
| 0.364 | 7 | 0 | 33 | 40 | 1.000 | 0.175 |
| 0.366 | 6 | 0 | 34 | 40 | 1.000 | 0.150 |
| 0.381 | 5 | 0 | 35 | 40 | 1.000 | 0.125 |
| 0.400 | 4 | 0 | 36 | 40 | 1.000 | 0.100 |
| 0.405 | 3 | 0 | 37 | 40 | 1.000 | 0.075 |
| 0.420 | 2 | 0 | 38 | 40 | 1.000 | 0.050 |
| 0.439 | 1 | 0 | 39 | 40 | 1.000 | 0.025 |
| 0.454 | 0 | 0 | 40 | 40 | — | 0.000 |

## False positives at threshold 0 (correct syllable that production would log)

- `bord_ok_t2_0_0` (borderline): target 2 → predicted 1, margin 0.0092 — dropped by the gate. imperfect-but-acceptable T2 rising
- `bord_ok_t2_2_1` (borderline): target 2 → predicted 1, margin 0.02 — dropped by the gate. imperfect-but-acceptable T2 rising
- `bord_ok_t3_0_0` (borderline): target 3 → predicted 1, margin 0.0625 — dropped by the gate. imperfect-but-acceptable T3 dipping
- `bord_ok_t3_0_1` (borderline): target 3 → predicted 1, margin 0.0566 — dropped by the gate. imperfect-but-acceptable T3 dipping
- `bord_ok_t3_1_0` (borderline): target 3 → predicted 1, margin 0.0171 — dropped by the gate. imperfect-but-acceptable T3 dipping
- `bord_ok_t3_1_1` (borderline): target 3 → predicted 1, margin 0.0651 — dropped by the gate. imperfect-but-acceptable T3 dipping
- `bord_ok_t3_2_0` (borderline): target 3 → predicted 1, margin 0.0552 — dropped by the gate. imperfect-but-acceptable T3 dipping
- `bord_ok_t3_2_1` (borderline): target 3 → predicted 1, margin 0.0307 — dropped by the gate. imperfect-but-acceptable T3 dipping

## False negatives at the recommended gate (real error not logged)

- `bord_wrong_t1_1_1` (borderline): target 1 → predicted 2, margin 0.0498. T1 high-level produced →T2 shallow-rise
- `bord_wrong_t2_0_1` (borderline): target 2 → predicted 1, margin 0.0419. T2 rising produced →T1 flat, no rise
