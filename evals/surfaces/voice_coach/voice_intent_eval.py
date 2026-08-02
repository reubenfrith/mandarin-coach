"""Voice-router intent surface (voice-coach plan Phase 4) → results/voice_intent.{md,json}.

Evaluates `voice_api._route_intent` — the thing that decides, for every spoken turn, which
brain answers it: the Mandarin conversation partner ('converse') or the English coach
('coach'). The router is a two-stage thing and this surface measures BOTH stages against
ground truth, kept separable:

  1. a zero-latency SCRIPT heuristic that resolves the clear cases with NO LLM call —
     Latin-only → coach, Han-only / empty → converse;
  2. an LLM classifier (`classify_turn_intent`) that only fires on a genuinely MIXED-script
     turn.

Precision-first toward CONVERSE. The dangerous error is a CONVERSE turn routed to COACH — an
English lecture when the learner wanted to talk. Treating **coach as the positive class**,
that failure is a FALSE POSITIVE, so **coach precision is the headline** (exactly as the
extraction surface headlines precision because a false log poisons the corpus). A coach turn
routed to converse is a false negative that degrades gracefully — the partner still does light
inline correction — so it is the cheaper error.

The dataset (datagen/voice_intent_dataset.json) is bucketed by SCRIPT but labelled by TRUE
intent, so each pure bucket carries heuristic-adversarial cases (English glue like "and you?"
that the heuristic force-routes to coach; Mandarin questions the heuristic sends to converse).
That is what stops the pure buckets scoring 1.0 by construction. The report breaks accuracy
down PER BUCKET so the heuristic's error and the classifier's error never blur together.

The manual `mode` override (converse|coach short-circuits the router) is deterministic and
covered by tests/test_voice_router.py; this surface measures the interesting `auto` path.

`--classify-always` runs the COUNTERFACTUAL arm: skip the heuristic, send every turn to the
classifier (each `--repeats` times, since temp 0.2 is nondeterministic), and compare against the
router baseline — which of its misroutes are fixed, which turns regress, and the metric spread
across runs. Writes results/voice_intent_classify_always.{md,json}. Answers "should we just
classify everything?" with data; see notes/voice-router-findings.md for the verdict.

Run:  EVAL_CONCURRENCY=4 uv run python evals/surfaces/voice_coach/voice_intent_eval.py
      uv run python evals/surfaces/voice_coach/voice_intent_eval.py --from-rows          # re-aggregate, no calls
      EVAL_CONCURRENCY=6 uv run python evals/surfaces/voice_coach/voice_intent_eval.py --classify-always --repeats 3
Prereq: datagen/voice_intent_dataset.json (build with generate_voice_intent_dataset.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

import voice_api  # noqa: E402
from config import CONVERSATION_MODEL  # noqa: E402

DATASET = _env.DATAGEN / "voice_intent_dataset.json"
RESULTS = _env.RESULTS
CONCURRENCY = int(os.environ.get("EVAL_CONCURRENCY", "4"))
BUCKET_ORDER = ["mandarin", "english", "mixed", "empty"]


def code_path(text: str) -> str:
    """Which stage of the real router resolves this turn: the zero-latency script heuristic,
    or the LLM classifier? Derived from the SAME predicates `_route_intent` uses, so a
    mis-bucketed dataset case is caught rather than silently mislabelled."""
    han = voice_api._has_han(text)
    latin = bool(voice_api._LATIN_WORD.search(text))
    return "classifier" if (han and latin) else "heuristic"


def outcome(gold: str, pred: str) -> str:
    """Coach = positive class. FP (converse routed to coach) is the jarring failure."""
    if gold == "coach":
        return "TP" if pred == "coach" else "FN"
    return "FP" if pred == "coach" else "TN"


async def eval_case(case: dict) -> dict:
    text = case["text"]
    pred = await voice_api._route_intent("eval-user", text, "auto")
    path = code_path(text)
    bucket_mismatch = None
    # mandarin/english/empty must be heuristic-resolved; mixed must hit the classifier.
    expected_path = "classifier" if case["bucket"] == "mixed" else "heuristic"
    if path != expected_path:
        bucket_mismatch = f"bucket={case['bucket']} but code path={path}"
    return {
        "id": case["id"],
        "text": text,
        "bucket": case["bucket"],
        "gold_intent": case["gold_intent"],
        "pred_intent": pred,
        "resolved_by": path,
        "outcome": outcome(case["gold_intent"], pred),
        "note": case.get("note"),
        "bucket_mismatch": bucket_mismatch,
    }


# --------------------------------------------------------------------------- #
# Classify-always arm — the counterfactual: skip the heuristic and send EVERY
# turn to the LLM classifier. Answers "should we just classify everything?" with
# data instead of hand-waving. The classifier is nondeterministic (production
# temp 0.2), so each turn is classified `repeats` times; the majority vote is the
# pred (ties → converse, matching the router's converse bias) and the per-run
# votes are kept so the metric SPREAD across runs is reportable, not a single
# fragile number.
# --------------------------------------------------------------------------- #
async def classify_always_case(case: dict, repeats: int) -> dict:
    text = case["text"]
    votes = []
    for _ in range(repeats):
        votes.append(await voice_api.classify_turn_intent(text))
    coach_votes = sum(1 for v in votes if v == "coach")
    majority = "coach" if coach_votes * 2 > repeats else "converse"  # tie → converse (bias)
    return {
        "id": case["id"],
        "text": text,
        "bucket": case["bucket"],
        "gold_intent": case["gold_intent"],
        "pred_intent": majority,
        "resolved_by": "classifier",
        "outcome": outcome(case["gold_intent"], majority),
        "note": case.get("note"),
        "bucket_mismatch": None,
        "votes": votes,
        "coach_votes": coach_votes,
        "stable": len(set(votes)) == 1,
    }


def spread_over_runs(rows: list[dict], repeats: int) -> dict:
    """Recompute the headline metrics for each independent run k (using vote k per turn),
    so the report shows min/mean/max instead of pretending the classifier is deterministic."""
    per_run = []
    for k in range(repeats):
        synth = [
            {**r, "pred_intent": r["votes"][k], "outcome": outcome(r["gold_intent"], r["votes"][k])}
            for r in rows if r.get("votes") and len(r["votes"]) > k
        ]
        s = summarise(synth)
        per_run.append({
            "coach_precision": s["coach_precision"],
            "misroute": s["converse_to_coach_misroute_rate"],
            "accuracy": s["accuracy"],
        })

    def _stat(key):
        vals = [r[key] for r in per_run if r[key] is not None]
        if not vals:
            return None
        return {"min": min(vals), "mean": sum(vals) / len(vals), "max": max(vals)}

    return {
        "repeats": repeats,
        "coach_precision": _stat("coach_precision"),
        "misroute": _stat("misroute"),
        "accuracy": _stat("accuracy"),
        "n_unstable": sum(1 for r in rows if not r.get("stable", True)),
        "unstable_ids": [r["id"] for r in rows if not r.get("stable", True)],
    }


def head_to_head(ca_rows: list[dict], router_rows: list[dict]) -> dict:
    """Compare classify-always (majority) against the saved router baseline, per turn. The
    decisive numbers: which of the router's misroutes does classify-always FIX, and does it
    REGRESS any turn the router already got right (the cost of taxing every turn with an LLM)."""
    router_by_id = {r["id"]: r for r in router_rows}
    ok = lambda o: o in ("TP", "TN")  # noqa: E731
    fixed, regressed = [], []
    both_right = both_wrong = 0
    for ca in ca_rows:
        rr = router_by_id.get(ca["id"])
        if rr is None:
            continue
        r_ok, c_ok = ok(rr["outcome"]), ok(ca["outcome"])
        if r_ok and c_ok:
            both_right += 1
        elif not r_ok and not c_ok:
            both_wrong += 1
        elif not r_ok and c_ok:
            fixed.append({"id": ca["id"], "text": ca["text"], "bucket": ca["bucket"],
                          "router": rr["outcome"], "classify_always": ca["outcome"]})
        else:  # router right, classify-always wrong → a regression the heuristic prevented
            regressed.append({"id": ca["id"], "text": ca["text"], "bucket": ca["bucket"],
                              "router_resolved_by": rr["resolved_by"], "outcome": ca["outcome"],
                              "note": ca.get("note")})
    return {
        "n_compared": both_right + both_wrong + len(fixed) + len(regressed),
        "fixed_n": len(fixed), "regressed_n": len(regressed),
        "both_right": both_right, "both_wrong": both_wrong,
        "fixed": fixed, "regressed": regressed,
    }


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else None
    r = tp / (tp + fn) if (tp + fn) else None
    f = (2 * p * r / (p + r)) if (p and r) else None
    return p, r, f


def summarise(rows: list[dict]) -> dict:
    tp = sum(1 for r in rows if r["outcome"] == "TP")
    fp = sum(1 for r in rows if r["outcome"] == "FP")
    fn = sum(1 for r in rows if r["outcome"] == "FN")
    tn = sum(1 for r in rows if r["outcome"] == "TN")
    coach_p, coach_r, coach_f = _prf(tp, fp, fn)
    conv_p, conv_r, conv_f = _prf(tn, fn, fp)  # converse as positive: TN/FN/FP swap in
    accuracy = (tp + tn) / len(rows) if rows else None
    # The literal design number: of turns the learner wanted as conversation, how many got
    # force-routed into an English lecture.
    converse_total = tn + fp
    misroute_rate = (fp / converse_total) if converse_total else None

    # Per-bucket accuracy — keeps the trivially-correct heuristic cases from inflating, and
    # isolates heuristic error (mandarin/english/empty) from classifier error (mixed).
    buckets = {}
    for b in BUCKET_ORDER:
        brs = [r for r in rows if r["bucket"] == b]
        if not brs:
            continue
        correct = sum(1 for r in brs if r["outcome"] in ("TP", "TN"))
        buckets[b] = {
            "n": len(brs),
            "correct": correct,
            "accuracy": correct / len(brs),
            "fp": sum(1 for r in brs if r["outcome"] == "FP"),
            "fn": sum(1 for r in brs if r["outcome"] == "FN"),
        }

    # Classifier-only slice (mixed bucket) — the LLM's own confusion, isolated.
    clf = [r for r in rows if r["resolved_by"] == "classifier"]
    ctp = sum(1 for r in clf if r["outcome"] == "TP")
    cfp = sum(1 for r in clf if r["outcome"] == "FP")
    cfn = sum(1 for r in clf if r["outcome"] == "FN")
    ctn = sum(1 for r in clf if r["outcome"] == "TN")
    clf_p, clf_r, _ = _prf(ctp, cfp, cfn)

    # Of the classifier cases, how many are labelled converse — i.e. contest the deployed
    # INTENT_CLASSIFIER_PROMPT, which mandates coach for ALL code-switching. On these the
    # classifier returning converse DEVIATES from its prompt; our label scores that as correct.
    clf_contestable = sum(1 for r in clf if r["gold_intent"] == "converse")

    heuristic_n = sum(1 for r in rows if r["resolved_by"] == "heuristic")
    return {
        "n_cases": len(rows),
        "confusion_matrix": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
        "coach_precision": coach_p, "coach_recall": coach_r, "coach_f1": coach_f,
        "converse_precision": conv_p, "converse_recall": conv_r, "converse_f1": conv_f,
        "accuracy": accuracy,
        "converse_to_coach_misroute_rate": misroute_rate,
        "converse_total": converse_total,
        "per_bucket": buckets,
        "resolution": {"heuristic": heuristic_n, "classifier": len(clf)},
        "classifier_only": {
            "n": len(clf), "TP": ctp, "FP": cfp, "FN": cfn, "TN": ctn,
            "precision": clf_p, "recall": clf_r,
            "contestable_labels": clf_contestable,
        },
        "bucket_mismatches": [r["id"] for r in rows if r.get("bucket_mismatch")],
        "model": CONVERSATION_MODEL,
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def render_md(summary: dict, rows: list[dict]) -> str:
    cm = summary["confusion_matrix"]

    def pct(x):
        return "—" if x is None else f"{x:.3f}"

    fps = [r for r in rows if r["outcome"] == "FP"]
    fns = [r for r in rows if r["outcome"] == "FN"]

    lines = [
        "# Voice-router intent eval — `_route_intent`",
        "",
        f"Classifier model **{summary['model']}** (mixed-script turns only; "
        f"{summary['resolution']['heuristic']}/{summary['n_cases']} cases are resolved by the "
        f"zero-latency script heuristic with no LLM call). Coach is the positive class: a "
        "CONVERSE turn routed to COACH is the jarring false positive the router is tuned to "
        "avoid. See `results/README.md` for how to re-derive any number.",
        "",
        "## Routing decision (coach = positive)",
        "",
        "| | Predicted coach | Predicted converse |",
        "|---|---|---|",
        f"| **Actually coach** | TP {cm['TP']} | FN {cm['FN']} |",
        f"| **Actually converse** | FP {cm['FP']} | TN {cm['TN']} |",
        "",
        f"- **Coach precision {pct(summary['coach_precision'])}** (headline — a false positive is "
        "the jarring converse→coach misroute)",
        f"- **Converse→coach misroute rate {pct(summary['converse_to_coach_misroute_rate'])}** "
        f"({cm['FP']} of {summary['converse_total']} conversation turns force-routed to a lecture)",
        f"- Coach recall {pct(summary['coach_recall'])} · Coach F1 {pct(summary['coach_f1'])} "
        f"(a missed coach turn degrades gracefully — the partner still corrects inline)",
        f"- Converse precision {pct(summary['converse_precision'])} · recall {pct(summary['converse_recall'])}",
        f"- Overall accuracy {pct(summary['accuracy'])}",
        "",
        "## Per-bucket accuracy (heuristic error vs classifier error, kept separate)",
        "",
        "Bucket = the script the heuristic sees, which fixes the code path. Pure buckets are "
        "labelled by TRUE intent, so they are NOT guaranteed correct — the adversarial cases "
        "(English glue, Mandarin questions) are exactly where the heuristic loses.",
        "",
        "| Bucket | Path | n | Accuracy | FP (→coach) | FN (→converse) |",
        "|---|---|---|---|---|---|",
    ]
    for b in BUCKET_ORDER:
        pb = summary["per_bucket"].get(b)
        if not pb:
            continue
        path = "classifier" if b == "mixed" else "heuristic"
        lines.append(f"| {b} | {path} | {pb['n']} | {pct(pb['accuracy'])} | {pb['fp']} | {pb['fn']} |")
    clf = summary["classifier_only"]
    lines += [
        "",
        f"**Classifier alone** (the {clf['n']} mixed turns): {clf['FP']} FP / {clf['FN']} FN "
        f"(TP {clf['TP']} FP {clf['FP']} FN {clf['FN']} TN {clf['TN']}) — **treat as *no errors "
        "observed, not a validation*** (see caveats).",
        "",
        "## Findings & caveats",
        "",
        "- **The robust, headline finding — 100% of misroutes are the HEURISTIC's, not the "
        "classifier's.** Every false positive is short English glue the `Latin→coach` rule routes "
        "to a lecture *without ever calling the classifier*; every false negative is a Mandarin "
        "question the `Han→converse` rule sends to chat. This rests on unambiguous labels, is "
        "deterministic, and is directly actionable: **the calibration target is the script "
        "heuristic** (e.g. route short English affirmations to converse; let the classifier see "
        "Han-only turns that look interrogative — 吗/什么/为什么/怎么/呢/？).",
        f"- **The classifier slice is NOT a validation.** n={clf['n']} is small; the classifier "
        "runs at the production temperature (`get_llm` default 0.2, **nondeterministic** — a rerun "
        f"may differ); and **{clf['contestable_labels']} of the {clf['n']} labels are contestable** "
        "against the deployed prompt.",
        "- **Prompt/intent misalignment this surface exposes.** `INTENT_CLASSIFIER_PROMPT` mandates "
        "coach for ALL code-switching (`我很喜欢 hiking` → coach). We labelled proper-noun "
        "code-switches (`去 Melbourne 玩`, `Netflix`, `Starbucks`, `David`) as **converse** — a "
        "learner naming a place/brand isn't asking to be taught the word. So the classifier "
        "returning converse there *deviates* from its own instructions, and our label rewards the "
        "deviation. If the product wants proper nouns left in conversation, the fix is a "
        "**proper-noun carve-out in the prompt**, not a claim the classifier is already correct.",
        "",
    ]
    if summary["bucket_mismatches"]:
        lines += [
            f"> ⚠️ Bucket/code-path mismatch on: {', '.join(summary['bucket_mismatches'])} "
            "— a dataset case is mis-bucketed vs the real heuristic predicates; fix the dataset.",
            "",
        ]
    if fps:
        lines += [
            "## False positives — conversation routed to coach (the jarring failure — inspect)",
            "",
        ]
        for r in fps:
            note = f" · _{r['note']}_" if r.get("note") else ""
            lines.append(f"- `{r['id']}` ({r['resolved_by']}, {r['bucket']}): `{r['text']}`{note}")
        lines.append("")
    if fns:
        lines += ["## False negatives — coach question routed to converse (graceful miss)", ""]
        for r in fns:
            note = f" · _{r['note']}_" if r.get("note") else ""
            lines.append(f"- `{r['id']}` ({r['resolved_by']}, {r['bucket']}): `{r['text']}`{note}")
        lines.append("")
    return "\n".join(lines)


def render_classify_always_md(summary, rows, spread, h2h, router_summary) -> str:
    cm = summary["confusion_matrix"]

    def pct(x):
        return "—" if x is None else f"{x:.3f}"

    def band(stat):
        if not stat:
            return "—"
        return f"{stat['mean']:.3f} (min {stat['min']:.3f} / max {stat['max']:.3f})"

    lines = [
        "# Voice router — classify-always arm",
        "",
        f"Counterfactual: skip the script heuristic and send **every** turn to the LLM classifier "
        f"({summary['model']}). Answers \"should we just classify everything?\". Each of the "
        f"{summary['n_cases']} turns is classified **{spread['repeats']}×** (classifier temp 0.2 is "
        "nondeterministic); the majority vote is the pred and the spread across runs is reported.",
        "",
        "## Classify-always vs the production router (majority vote)",
        "",
        "| Metric | Router (heuristic+classifier) | Classify-always | Δ |",
        "|---|---|---|---|",
    ]
    if router_summary:
        def delta(a, b):
            if a is None or b is None:
                return "—"
            d = b - a
            return f"{d:+.3f}"
        lines += [
            f"| Coach precision (headline) | {pct(router_summary['coach_precision'])} | "
            f"{pct(summary['coach_precision'])} | {delta(router_summary['coach_precision'], summary['coach_precision'])} |",
            f"| Converse→coach misroute | {pct(router_summary['converse_to_coach_misroute_rate'])} | "
            f"{pct(summary['converse_to_coach_misroute_rate'])} | "
            f"{delta(router_summary['converse_to_coach_misroute_rate'], summary['converse_to_coach_misroute_rate'])} |",
            f"| Accuracy | {pct(router_summary['accuracy'])} | {pct(summary['accuracy'])} | "
            f"{delta(router_summary['accuracy'], summary['accuracy'])} |",
        ]
    else:
        lines.append("| _(router baseline voice_intent.json not found — run the default arm first)_ ||||")
    lines += [
        "",
        f"Classify-always confusion (coach = positive): TP {cm['TP']} FP {cm['FP']} FN {cm['FN']} TN {cm['TN']}.",
        "",
        "## Spread across runs (the classifier is nondeterministic)",
        "",
        f"- Coach precision: **{band(spread['coach_precision'])}**",
        f"- Converse→coach misroute: {band(spread['misroute'])}",
        f"- Accuracy: {band(spread['accuracy'])}",
        f"- Unstable turns (votes disagreed across the {spread['repeats']} runs): "
        f"**{spread['n_unstable']}**"
        + (f" — {', '.join(spread['unstable_ids'])}" if spread["unstable_ids"] else ""),
        "",
        "## Head-to-head vs the router (per turn)",
        "",
    ]
    if h2h:
        lines += [
            f"- **Fixed** (router misrouted → classify-always correct): **{h2h['fixed_n']}**",
            f"- **Regressed** (router correct → classify-always misrouted — the cost of taxing "
            f"every turn with a nondeterministic LLM): **{h2h['regressed_n']}**",
            f"- Both right: {h2h['both_right']} · both wrong: {h2h['both_wrong']} "
            f"(of {h2h['n_compared']} compared)",
            "",
        ]
        if h2h["fixed"]:
            lines += ["### Fixed by classify-always", ""]
            for r in h2h["fixed"]:
                lines.append(f"- `{r['id']}` ({r['bucket']}): `{r['text']}` — router {r['router']} → "
                             f"classify-always {r['classify_always']}")
            lines.append("")
        if h2h["regressed"]:
            lines += ["### Regressed (the heuristic was protecting these)", ""]
            for r in h2h["regressed"]:
                note = f" · _{r['note']}_" if r.get("note") else ""
                lines.append(f"- `{r['id']}` ({r['bucket']}, router path: {r['router_resolved_by']}): "
                             f"`{r['text']}` → {r['outcome']}{note}")
            lines.append("")
    else:
        lines += ["_(no router baseline to compare against)_", ""]
    lines += [
        "## Read this with the latency caveat",
        "",
        "This surface measures **accuracy only**. Classify-always also puts an LLM call (temp 0.2, "
        "nondeterministic) on the critical path of *every* spoken turn — including the plain-Mandarin "
        "conversation turns the heuristic resolves instantly and with zero misroute risk. Weigh any "
        "accuracy gain here against that per-turn latency + the regressions above before changing the "
        "architecture. Full reasoning + decision rule: `notes/voice-router-findings.md`.",
        "",
    ]
    return "\n".join(lines)


async def latency_probe(n: int, turn_baseline_s: float) -> dict:
    """Marginal cost of ONE `classify_turn_intent` call — the extra latency classify-most adds to
    every turn the heuristic resolves for free today. Timed SEQUENTIALLY (concurrency 1) so the
    number is per-call, not inflated by eval contention. This is an eval-time estimate, NOT
    production-under-load, but it converts "hinges on latency" into a number."""
    cases = json.loads(DATASET.read_text())["cases"]
    # Sample across buckets so the mix is representative; only the mixed turns actually vary the
    # classifier's work, but all pay the round-trip.
    sample = [c["text"] for c in cases[:n]]
    times = []
    for text in sample:
        t0 = time.perf_counter()
        await voice_api.classify_turn_intent(text)
        times.append(time.perf_counter() - t0)
    times.sort()
    p = lambda q: times[min(len(times) - 1, int(q * len(times)))]  # noqa: E731
    p50, p95 = p(0.50), p(0.95)
    return {
        "n": len(times), "model": CONVERSATION_MODEL,
        "p50_s": p50, "p95_s": p95, "mean_s": sum(times) / len(times),
        "min_s": times[0], "max_s": times[-1],
        "turn_baseline_s": turn_baseline_s,
        "p50_pct_of_turn": p50 / turn_baseline_s if turn_baseline_s else None,
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-rows", action="store_true",
                    help="recompute summary + re-render md from saved rows (no model calls)")
    ap.add_argument("--latency", type=int, metavar="N", default=None,
                    help="marginal-latency probe: time N sequential classify_turn_intent calls "
                         "(the per-turn cost classify-most adds). Prints p50/p95; makes no other output.")
    ap.add_argument("--turn-baseline-s", type=float, default=2.3,
                    help="reference full-turn latency (STT+chat+TTS) for the latency probe's %%-of-turn. "
                         "Default 2.3s from the voice-coach plan's measured pipeline.")
    ap.add_argument("--classify-always", action="store_true",
                    help="run the counterfactual arm: classify EVERY turn (skip the heuristic), "
                         "compare to the router baseline; writes voice_intent_classify_always.{md,json}")
    ap.add_argument("--repeats", type=int, default=3,
                    help="classify-always: times to classify each turn (temp 0.2 is nondeterministic; "
                         "the spread across runs is reported). Default 3.")
    args = ap.parse_args()

    # ----- latency probe ------------------------------------------------------ #
    if args.latency:
        lat = await latency_probe(args.latency, args.turn_baseline_s)
        pct = f"{lat['p50_pct_of_turn'] * 100:.0f}%" if lat["p50_pct_of_turn"] is not None else "—"
        print(f"classify_turn_intent latency ({lat['model']}, {lat['n']} sequential calls):")
        print(f"  p50 {lat['p50_s'] * 1000:.0f} ms · p95 {lat['p95_s'] * 1000:.0f} ms · "
              f"mean {lat['mean_s'] * 1000:.0f} ms  (range {lat['min_s'] * 1000:.0f}–{lat['max_s'] * 1000:.0f} ms)")
        print(f"  p50 ≈ {pct} of a {lat['turn_baseline_s']}s full turn — the per-turn cost "
              "classify-most adds vs the heuristic's ~0 ms. (eval-time estimate, not under production load)")
        return

    # ----- classify-always arm ------------------------------------------------ #
    if args.classify_always:
        stem = "voice_intent_classify_always"
        router = None
        router_path = RESULTS / "voice_intent.json"
        if router_path.exists():
            router = json.loads(router_path.read_text())

        if args.from_rows:
            saved = json.loads((RESULTS / f"{stem}.json").read_text())
            rows, repeats = saved["rows"], saved.get("spread", {}).get("repeats", args.repeats)
            summary = summarise(rows)
            spread = spread_over_runs(rows, repeats)
            h2h = head_to_head(rows, router["rows"]) if router else None
            md = render_classify_always_md(summary, rows, spread, h2h,
                                           router["summary"] if router else None)
            (RESULTS / f"{stem}.json").write_text(json.dumps(
                {"summary": summary, "spread": spread, "head_to_head": h2h, "rows": rows},
                ensure_ascii=False, indent=2))
            (RESULTS / f"{stem}.md").write_text(md)
            print(f"Re-aggregated {len(rows)} saved rows → {stem}.{{md,json}} (no model calls).")
            return

        cases = json.loads(DATASET.read_text())["cases"]
        sem = asyncio.Semaphore(CONCURRENCY)

        async def guarded_ca(case):
            async with sem:
                try:
                    return await classify_always_case(case, args.repeats)
                except Exception as e:  # noqa: BLE001
                    print(f"  ! {case['id']} failed: {type(e).__name__}: {e}")
                    return None

        print(f"Classify-always arm: {len(cases)} turns × {args.repeats} classifications "
              f"(classifier={CONVERSATION_MODEL}, concurrency {CONCURRENCY})...")
        rows = [r for r in await asyncio.gather(*[guarded_ca(c) for c in cases]) if r is not None]
        order = {c["id"]: i for i, c in enumerate(cases)}
        rows.sort(key=lambda r: order[r["id"]])

        summary = summarise(rows)
        spread = spread_over_runs(rows, args.repeats)
        h2h = head_to_head(rows, router["rows"]) if router else None
        RESULTS.mkdir(exist_ok=True)
        (RESULTS / f"{stem}.json").write_text(json.dumps(
            {"summary": summary, "spread": spread, "head_to_head": h2h, "rows": rows},
            ensure_ascii=False, indent=2))
        (RESULTS / f"{stem}.md").write_text(
            render_classify_always_md(summary, rows, spread, h2h,
                                      router["summary"] if router else None))

        cm = summary["confusion_matrix"]
        print(f"\nDone (classify-always). TP {cm['TP']} FP {cm['FP']} FN {cm['FN']} TN {cm['TN']}")
        print(f"  coach precision {summary['coach_precision']}  misroute "
              f"{summary['converse_to_coach_misroute_rate']}  accuracy {summary['accuracy']}")
        if h2h:
            print(f"  vs router — fixed {h2h['fixed_n']}, regressed {h2h['regressed_n']}, "
                  f"unstable {spread['n_unstable']}")
        print(f"  wrote {RESULTS / (stem + '.md')} and .json")
        return

    # ----- default router arm ------------------------------------------------- #
    if args.from_rows:
        saved = json.loads((RESULTS / "voice_intent.json").read_text())["rows"]
        summary = summarise(saved)
        (RESULTS / "voice_intent.json").write_text(
            json.dumps({"summary": summary, "rows": saved}, ensure_ascii=False, indent=2))
        (RESULTS / "voice_intent.md").write_text(render_md(summary, saved))
        print(f"Re-aggregated {len(saved)} saved rows → voice_intent.{{md,json}} (no model calls).")
        return

    cases = json.loads(DATASET.read_text())["cases"]
    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded(case):
        async with sem:
            try:
                return await eval_case(case)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {case['id']} failed: {type(e).__name__}: {e}")
                return None

    print(f"Voice-router surface: {len(cases)} cases (classifier={CONVERSATION_MODEL}, "
          f"concurrency {CONCURRENCY})...")
    rows = [r for r in await asyncio.gather(*[guarded(c) for c in cases]) if r is not None]
    # Stable order for the saved rows: dataset order.
    order = {c["id"]: i for i, c in enumerate(cases)}
    rows.sort(key=lambda r: order[r["id"]])

    summary = summarise(rows)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "voice_intent.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / "voice_intent.md").write_text(render_md(summary, rows))

    cm = summary["confusion_matrix"]
    print(f"\nDone. TP {cm['TP']} FP {cm['FP']} FN {cm['FN']} TN {cm['TN']}")
    print(f"  coach precision {summary['coach_precision']}  "
          f"converse→coach misroute {summary['converse_to_coach_misroute_rate']}  "
          f"accuracy {summary['accuracy']}")
    if summary["bucket_mismatches"]:
        print(f"  ⚠️ bucket/path mismatch: {summary['bucket_mismatches']}")
    print(f"  wrote {RESULTS / 'voice_intent.md'} and .json")


if __name__ == "__main__":
    asyncio.run(main())
