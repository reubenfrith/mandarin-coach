"""Tone auto-logging surface → results/tone_assessment.{md,json}.

The gate the plan calls non-negotiable: measure the PRECISION of the tone-error auto-logger
before its writes are trusted, and set the confidence threshold from data.

WHAT PRODUCTION DOES.  On a single-syllable target the coach compares the DSP's predicted
tone to the KNOWN target tone and logs an error whenever they differ (pronounce_api.py —
`if not v["ok"]: _log_tone_error(...)`, category="tones", source="voice"). That write lands
in the same per-user corpus the text coach mines, so — exactly like the structured-extraction
surface — a FALSE POSITIVE (a syllable said acceptably, logged as a tone mistake) is the
dangerous class and PRECISION is the headline. A false negative just means one real slip
isn't logged that turn.

WHAT WE MEASURE.  Over a labeled synthetic set (datagen/tone_dataset.json, rendered here
through the real pYIN pipeline) we score the effective logging predicate and SWEEP a
confidence gate on it. The gate is the classifier's MARGIN on a mismatch —
`dist(target) - dist(predicted)`, i.e. how much better the wrong tone fits the audio than
the intended tone. A large margin = a confident cross-tone error worth logging; a small
margin = an ambiguous near-miss we should stay silent on to protect the corpus. Threshold 0
reproduces production exactly (log on ANY label mismatch); the sweep finds the smallest
threshold that reaches the precision target, which is the value we wire back.

HONEST SCOPE.  Gold labels are perturbation-defined on clean synthetic voicing (we chose
both the distortion and its label), so every number here is an UPPER BOUND on real-L2
precision, not a human-accuracy figure — creaky/L2 validation with CREPE is Phase 2. The
`clean` band is separable by construction (a sanity floor); the `borderline` band —
near-miss same-category vs neighbour-crossing, especially T2<->T3 — is where the threshold
is actually decided, and is reported separately.

Run:      uv run python evals/surfaces/tone_assessment_eval.py
Re-agg:   uv run python evals/surfaces/tone_assessment_eval.py --from-rows   (no synthesis)
Prereq:   evals/datagen/tone_dataset.json  (build with datagen/generate_tone_dataset.py)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma isolation

import argparse  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

import tone_analysis as ta  # noqa: E402

DATASET = _env.DATAGEN / "tone_dataset.json"
RESULTS = _env.RESULTS

SR = 22050
DUR = 0.5
# Precision we require of the auto-logger before trusting its corpus writes. A false
# positive poisons a per-user corpus, so we hold precision high and let recall give.
PRECISION_TARGET = float(os.environ.get("TONE_PRECISION_TARGET", "0.98"))
WORKERS = int(os.environ.get("EVAL_CONCURRENCY", "4"))


# --------------------------------------------------------------------------- #
# Recipe -> audio -> pitch.  Same additive-harmonic synthesis as the unit test
# (tests/test_tone_analysis.py); a recipe is a Chao-level sequence + synth params.
# --------------------------------------------------------------------------- #
def synth(levels, *, jitter, noise, seed) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    f0 = ta._levels_to_contour(levels)(t / DUR)
    if jitter:
        f0 = f0 * (1 + jitter * rng.standard_normal(len(t)).cumsum() / len(t) ** 0.5)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = sum((1.0 / k) * np.sin(k * phase) for k in range(1, 17))
    sig = (np.hanning(len(t)) ** 0.3) * sig + noise * rng.standard_normal(len(t))
    return (sig / np.max(np.abs(sig))).astype(np.float32)


def _wav_bytes(samples: np.ndarray) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, samples, SR, format="WAV")
    return buf.getvalue()


def analyse_case(case: dict) -> dict:
    """Render a recipe through the REAL decode+pYIN path and classify it, exactly as the
    production single-syllable branch does. Returns the per-case row (no thresholding yet)."""
    samples = synth(case["produced_levels"], jitter=case["jitter"],
                    noise=case["noise"], seed=case["seed"])
    # extract_f0 is the production entry point (decodes the WAV the browser would send).
    _, f0 = ta.extract_f0(_wav_bytes(samples))
    target = case["target_tone"]

    row = {
        "id": case["id"], "band": case["band"], "target_tone": target,
        "produced_levels": case["produced_levels"], "gold_wrong": case["gold_wrong"],
        "note": case["note"],
    }
    if np.asarray(f0).size < 2:  # production returns no per-syllable verdict → never logs
        row.update({"voiced": False, "predicted_tone": None, "dists": None,
                    "margin": None, "score": None, "mismatch": False})
        return row

    predicted, dists, _ = ta.classify_contour(f0)
    dists = {int(k): float(v) for k, v in dists.items()}
    margin = dists[target] - dists[predicted]  # 0 iff predicted==target, else >0 (confidence)
    row.update({
        "voiced": True,
        "predicted_tone": int(predicted),
        "dists": {k: round(v, 4) for k, v in dists.items()},
        "margin": round(margin, 4),
        "score": ta._score(dists[target]),
        "mismatch": bool(predicted != target),
    })
    return row


# --------------------------------------------------------------------------- #
# Thresholded predicate + metrics
# --------------------------------------------------------------------------- #
def would_log(row: dict, threshold: float) -> bool:
    """The effective auto-log predicate at a given margin gate. threshold=0 == production
    today (log on ANY label mismatch)."""
    if not row.get("voiced") or not row["mismatch"]:
        return False
    return row["margin"] >= threshold


def _outcome(gold_wrong: bool, logged: bool) -> str:
    if gold_wrong:
        return "TP" if logged else "FN"
    return "FP" if logged else "TN"


def _prf(rows: list[dict], threshold: float) -> dict:
    tp = fp = fn = tn = 0
    for r in rows:
        o = _outcome(r["gold_wrong"], would_log(r, threshold))
        tp += o == "TP"; fp += o == "FP"; fn += o == "FN"; tn += o == "TN"
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None
    return {"threshold": round(threshold, 4), "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": precision, "recall": recall, "f1": f1}


def sweep(rows: list[dict]) -> list[dict]:
    """Evaluate the predicate at threshold 0 (production today) plus the MIDPOINT between
    every pair of adjacent mismatch-margins. Midpoints, not the margins themselves, so a
    recommended threshold lands in the GAP between a false-positive margin and the next
    true-positive margin — robust under `margin >= threshold`, not pinned to a data point
    that `>=` would re-admit. Captures every distinct confusion matrix on the frontier."""
    margins = sorted({r["margin"] for r in rows if r.get("voiced") and r["mismatch"]})
    mids = [(a + b) / 2 for a, b in zip(margins, margins[1:])]
    thresholds = [0.0] + mids + ([margins[-1] + 0.01] if margins else [])
    return [_prf(rows, round(t, 4)) for t in thresholds]


def recommend(grid: list[dict]) -> dict:
    """Smallest threshold reaching the precision target (max recall subject to precision).
    Raising the gate only ever removes logs, so precision is monotonic up / recall down."""
    ok = [g for g in grid if g["precision"] is not None and g["precision"] >= PRECISION_TARGET]
    if ok:
        return min(ok, key=lambda g: g["threshold"])
    return max(grid, key=lambda g: (g["precision"] or 0, g["recall"] or 0))


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def summarise(rows: list[dict]) -> dict:
    grid = sweep(rows)
    base = _prf(rows, 0.0)                        # production predicate today
    rec = recommend(grid)
    gate_needed = rec["threshold"] > 0.0

    def band_prf(band, threshold):
        return _prf([r for r in rows if r["band"] == band], threshold)

    return {
        "n_cases": len(rows),
        "n_correct": sum(1 for r in rows if not r["gold_wrong"]),
        "n_wrong": sum(1 for r in rows if r["gold_wrong"]),
        "precision_target": PRECISION_TARGET,
        "baseline": base,                         # threshold 0 == current production
        "recommended": rec,
        "gate_needed": gate_needed,
        "log_margin": rec["threshold"] if gate_needed else 0.0,
        "sweep": grid,
        "by_band_baseline": {b: band_prf(b, 0.0) for b in ("clean", "borderline")},
        "by_band_recommended": {b: band_prf(b, rec["threshold"]) for b in ("clean", "borderline")},
        "unvoiced_n": sum(1 for r in rows if not r.get("voiced")),
    }


def _fp_fn(rows, threshold):
    fps = [r for r in rows if not r["gold_wrong"] and would_log(r, threshold)]
    fns = [r for r in rows if r["gold_wrong"] and not would_log(r, threshold)]
    return fps, fns


def render_md(summary: dict, rows: list[dict]) -> str:
    def pct(x):
        return "—" if x is None else f"{x:.3f}"

    base, rec = summary["baseline"], summary["recommended"]
    gate = summary["gate_needed"]
    fps0, _ = _fp_fn(rows, 0.0)
    fps_r, fns_r = _fp_fn(rows, rec["threshold"])

    decision = (
        f"**Decision — add a margin gate at `LOG_MARGIN = {rec['threshold']:.3f}`.** "
        f"The production predicate (log on any label mismatch, threshold 0) scores "
        f"precision {pct(base['precision'])} with {base['FP']} false positive(s); gating on "
        f"classifier margin ≥ {rec['threshold']:.3f} lifts precision to {pct(rec['precision'])} "
        f"(recall {pct(base['recall'])}→{pct(rec['recall'])}). Wire it into the "
        f"`if not v['ok']` branch of `pronounce_api.py`."
        if gate else
        f"**Decision — no gate needed; the hard-label predicate is validated.** Logging on "
        f"any label mismatch (threshold 0) already scores precision {pct(base['precision'])} "
        f"≥ target {summary['precision_target']:.2f} with {base['FP']} false positive(s), so "
        f"production's `if not v['ok']` predicate stands as-is and `WEAK_SCORE` remains a "
        f"UI-only flag. The margin is exposed for inspection but does not gate logging."
    )

    lines = [
        "# Tone auto-logging eval — `pronounce_api._log_tone_error`",
        "",
        "The gate before the pronunciation coach is trusted to write tone errors into the "
        "learner's corpus. We score the **effective logging predicate** — *would this syllable "
        "be logged as a tone error?* — on a labeled synthetic set, and sweep a confidence gate "
        "on it. **Precision is the headline**: a false positive logs a correctly-said syllable "
        "as a mistake and poisons the per-user corpus (same discipline as the extraction surface).",
        "",
        "> **Scope / honesty.** Gold labels are *perturbation-defined* on clean synthetic "
        "voicing — we chose both the distortion and its label — so these are an **upper bound** "
        "on real-L2 precision, not a human-accuracy figure. The `clean` band is separable by "
        "construction (a sanity floor); the `borderline` band (near-miss same-category vs "
        "neighbour-crossing, esp. T2↔T3) is where the threshold is decided. Creaky/L2 "
        "validation (CREPE, real recordings) is Phase 2.",
        "",
        decision,
        "",
        f"Dataset: **{summary['n_cases']}** cases "
        f"({summary['n_correct']} correct / {summary['n_wrong']} wrong), "
        f"{summary['unvoiced_n']} unvoiced. See `results/README.md` to re-derive any number.",
        "",
        "## Predicate: production (margin 0) vs recommended gate",
        "",
        "| | Threshold | TP | FP | FN | TN | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|---|---|---|",
        f"| **Production today** | {base['threshold']:.3f} | {base['TP']} | {base['FP']} | "
        f"{base['FN']} | {base['TN']} | **{pct(base['precision'])}** | {pct(base['recall'])} | {pct(base['f1'])} |",
        f"| **Recommended** | {rec['threshold']:.3f} | {rec['TP']} | {rec['FP']} | "
        f"{rec['FN']} | {rec['TN']} | **{pct(rec['precision'])}** | {pct(rec['recall'])} | {pct(rec['f1'])} |",
        "",
        "## By band",
        "",
        "| Band | Precision @0 | Recall @0 | Precision @rec | Recall @rec |",
        "|---|---|---|---|---|",
    ]
    for b in ("clean", "borderline"):
        b0 = summary["by_band_baseline"][b]
        br = summary["by_band_recommended"][b]
        lines.append(f"| **{b}** | {pct(b0['precision'])} | {pct(b0['recall'])} | "
                     f"{pct(br['precision'])} | {pct(br['recall'])} |")
    lines += [
        "",
        "The `clean` band is separable by construction — if precision dips there the DSP is "
        "broken, not miscalibrated. The `borderline` band carries the real signal.",
        "",
        "## Margin sweep (the calibration curve)",
        "",
        "Each row raises the confidence gate to just above one observed mismatch-margin; "
        "raising it only ever removes a log, so precision climbs and recall falls monotonically.",
        "",
        "| Threshold | TP | FP | FN | TN | Precision | Recall |",
        "|---|---|---|---|---|---|---|",
    ]
    for g in summary["sweep"]:
        star = "  ← recommended" if abs(g["threshold"] - rec["threshold"]) < 1e-6 else ""
        lines.append(f"| {g['threshold']:.3f} | {g['TP']} | {g['FP']} | {g['FN']} | {g['TN']} | "
                     f"{pct(g['precision'])} | {pct(g['recall'])} |{star}")
    lines.append("")

    if fps0:
        lines += ["## False positives at threshold 0 (correct syllable that production would log)", ""]
        for r in fps0:
            gated = "" if would_log(r, rec["threshold"]) else " — dropped by the gate"
            lines.append(f"- `{r['id']}` ({r['band']}): target {r['target_tone']} → predicted "
                         f"{r['predicted_tone']}, margin {r['margin']}{gated}. {r['note']}")
        lines.append("")
    if fns_r:
        lines += ["## False negatives at the recommended gate (real error not logged)", ""]
        for r in fns_r:
            lines.append(f"- `{r['id']}` ({r['band']}): target {r['target_tone']} → predicted "
                         f"{r['predicted_tone']}, margin {r['margin']}. {r['note']}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-rows", action="store_true",
                    help="recompute summary + re-render md from saved rows (no synthesis)")
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    if args.from_rows:
        rows = json.loads((RESULTS / "tone_assessment.json").read_text())["rows"]
    else:
        cases = json.loads(DATASET.read_text())["cases"]
        print(f"Tone auto-logging surface: rendering {len(cases)} cases through pYIN "
              f"(workers={WORKERS})...")
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            rows = list(ex.map(analyse_case, cases))

    summary = summarise(rows)
    (RESULTS / "tone_assessment.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / "tone_assessment.md").write_text(render_md(summary, rows))

    b, r = summary["baseline"], summary["recommended"]
    print(f"\nDone. {summary['n_cases']} cases.")
    print(f"  production (margin 0): precision {b['precision']} recall {b['recall']} "
          f"(FP {b['FP']}, FN {b['FN']})")
    if summary["gate_needed"]:
        print(f"  → RECOMMEND gate LOG_MARGIN = {r['threshold']:.4f}: "
              f"precision {r['precision']} recall {r['recall']} (FP {r['FP']})")
    else:
        print(f"  → no gate needed; hard-label predicate validated at precision {b['precision']}")
    print(f"  wrote {RESULTS / 'tone_assessment.md'} and .json")


if __name__ == "__main__":
    main()
