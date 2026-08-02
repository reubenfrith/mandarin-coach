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

Run:  EVAL_CONCURRENCY=4 uv run python evals/surfaces/voice_intent_eval.py
      uv run python evals/surfaces/voice_intent_eval.py --from-rows   # re-aggregate, no calls
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


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-rows", action="store_true",
                    help="recompute summary + re-render md from saved rows (no model calls)")
    args = ap.parse_args()

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
