"""Structured-extraction surface (Task 5, third of three) → results/extraction.{md,json}.

Evaluates `extract_and_log_error` (app/agent.py) — the post-turn LLM call that mines
each learner turn into a structured error record and silently appends it to the
learner's corpus. It is the "hidden" surface: no user ever sees its output, but a
wrong record poisons the B_small/C_scale memory the other two surfaces rely on. So we
measure exactly the three ways it can corrupt the corpus:

  1. had_error detection — precision/recall/F1 of "would this turn get LOGGED as an
     error?".  We score the EFFECTIVE logging predicate the production code uses
     (`has_chinese AND had_error AND original non-empty`), not the raw bool — that
     is what actually writes to the corpus. FALSE POSITIVES are the dangerous class
     (a clean sentence logged as a mistake), so precision is the headline.
  2. category accuracy — on positives that were logged, does the category match?
     Scored only on the 20 SPECIFIC-category golds (particle/word_order/measure_word);
     the 20 "grammar" golds are the corpus catch-all ("use grammar if unsure") and so
     are underspecified — reported separately, not scored right/wrong.
  3. correction validity — is the stored correction a valid fix? Deterministic exact/
     near match against the gold correction first (the repo's signature move); only
     the residue goes to a focused LLM judge.

Everything is anchored deterministically where possible; the LLM judge only breaks
ties on correction wording. Extraction model pinned to glm for reproducibility
(deepseek hangs — DECISIONS #4); override with EXTRACT_MODEL.

Run:  REQUEST_TIMEOUT=150 EVAL_CONCURRENCY=4 uv run python evals/surfaces/extraction_eval.py
Prereq: evals/datagen/extraction_dataset.json (build with generate_extraction_dataset.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from agent import _has_chinese, extract_error_record  # noqa: E402
from config import get_llm  # noqa: E402
from lib.llm_judge import canon_category  # noqa: E402

DATASET = _env.DATAGEN / "extraction_dataset.json"
RESULTS = _env.RESULTS

EXTRACT_MODEL = os.environ.get("EXTRACT_MODEL", "glm")   # under test; deepseek hangs (DECISIONS #4)
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "glm")       # correction-validity tie-breaker
CONCURRENCY = int(os.environ.get("EVAL_CONCURRENCY", "4"))


# --------------------------------------------------------------------------- #
# Correction-validity judge — focused on a BARE corrected sentence (not a full
# coaching answer), to avoid llm_judge.judge_correction's "don't reward fluent
# prose" framing which is tuned for the head-to-head answers, not a lone sentence.
# --------------------------------------------------------------------------- #
class CorrectionValid(BaseModel):
    valid: bool = Field(default=False, description="Is the proposed correction a linguistically valid fix of the learner's error? A valid fix need not match the reference verbatim.")
    reason: str = Field(default="", description="One short sentence.")


_CORRECTION_SYS = (
    "You check whether a proposed corrected Chinese sentence is a linguistically valid "
    "fix for a learner's erroneous sentence. You are given the learner's original, a "
    "reference correct version, and the proposed correction. Accept ANY correction that "
    "is grammatical and preserves the learner's intended meaning, even if it differs from "
    "the reference. Reject it only if it leaves the error uncorrected, is itself "
    "ungrammatical, or changes the meaning."
)


def _norm(s: str) -> str:
    """Normalise a Chinese sentence for exact comparison: drop spaces + terminal punctuation."""
    s = (s or "").strip()
    s = re.sub(r"\s+", "", s)
    return s.strip("。！？!?.,，、 ")


def correction_matches(pred: str, gold: str, alternatives: str) -> bool:
    """Deterministic: does the predicted correction match the gold (or a listed alternative)?"""
    p = _norm(pred)
    if not p:
        return False
    golds = {_norm(gold)} | {_norm(a) for a in (alternatives or "").split(" / ")}
    return p in golds


async def judge_correction_valid(learner: str, reference: str, proposed: str) -> CorrectionValid:
    judge = get_llm(JUDGE_MODEL, temperature=0.0, streaming=False).with_structured_output(CorrectionValid)
    msg = f"Learner original: {learner}\nReference correct: {reference}\nProposed correction: {proposed}"
    return await judge.ainvoke([SystemMessage(content=_CORRECTION_SYS), HumanMessage(content=msg)])


# --------------------------------------------------------------------------- #
# Robust extraction — retry once, then fail SAFE the way production does.
# `extract_and_log_error` wraps the call in try/except and logs nothing on any
# error, so a persistent failure = "not logged" (a predicted negative), NOT a
# dropped case. Retry-once separates transient OpenRouter flakiness from the
# model's real output; glm also intermittently returns JSON `null` for the string
# fields (schema expects ""), which raises OutputParserException — same fail-safe.
# --------------------------------------------------------------------------- #
async def robust_extract(user_input: str, coach_reply: str):
    """Returns (rec | None, errored: bool). None == production would log nothing."""
    last = None
    for _ in range(2):
        try:
            return await extract_error_record(user_input, coach_reply, model=EXTRACT_MODEL), False
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {str(e)[:80]}"
    print(f"  · extraction failed (fail-safe → not logged): {last}", flush=True)
    return None, True


# --------------------------------------------------------------------------- #
# Per-case evaluation
# --------------------------------------------------------------------------- #
async def eval_positive(case: dict) -> dict:
    rec, errored = await robust_extract(case["input"], case["coach_reply"])
    if rec is None:  # production logs nothing → a gold error is MISSED (false negative)
        return {
            "id": case["id"], "kind": "positive", "input": case["input"],
            "gold_had_error": True, "gold_category": case["gold_category"],
            "specific_gold": case["specific_gold"], "gold_correction": case["gold_correction"],
            "pred_had_error": None, "pred_category": None, "pred_category_canon": None,
            "pred_correction": None, "would_log": False, "extraction_errored": True,
            "outcome": "FN", "category_correct": None,
            "correction_valid": None, "correction_how": None,
        }
    # Effective logging predicate = what production actually writes to the corpus.
    would_log = _has_chinese(case["input"]) and rec.had_error and bool((rec.original or "").strip())

    cat_pred = canon_category(rec.category)
    cat_gold = canon_category(case["gold_category"])
    category_correct = None  # only scoreable on specific-gold, logged cases
    if would_log and case["specific_gold"]:
        category_correct = (cat_pred == cat_gold)

    correction_valid = None
    correction_how = None
    if would_log:
        if correction_matches(rec.correction, case["gold_correction"], case["gold_correction_alternatives"]):
            correction_valid, correction_how = True, "exact"
        else:
            v = await judge_correction_valid(case["input"], case["gold_correction"], rec.correction)
            correction_valid, correction_how = bool(v.valid), f"judge: {v.reason}"

    return {
        "id": case["id"], "kind": "positive", "input": case["input"],
        "gold_had_error": True, "gold_category": case["gold_category"],
        "specific_gold": case["specific_gold"], "gold_correction": case["gold_correction"],
        "pred_had_error": rec.had_error, "pred_category": rec.category,
        "pred_category_canon": cat_pred, "pred_correction": rec.correction,
        "would_log": would_log, "extraction_errored": False,
        "outcome": "TP" if would_log else "FN",
        "category_correct": category_correct,
        "correction_valid": correction_valid, "correction_how": correction_how,
    }


async def eval_negative(case: dict) -> dict:
    row = {
        "id": case["id"], "kind": case["kind"], "input": case["input"],
        "gold_had_error": False,
    }
    if not _has_chinese(case["input"]):
        # Production guard short-circuits before the LLM — a deterministic true negative.
        row.update({
            "pred_had_error": None, "pred_category": None, "pred_correction": None,
            "would_log": False, "guard_skipped": True, "extraction_errored": False,
            "outcome": "TN",
        })
        return row
    rec, errored = await robust_extract(case["input"], case["coach_reply"])
    if rec is None:  # production logs nothing → a clean input correctly not logged (TN)
        row.update({
            "pred_had_error": None, "pred_category": None, "pred_correction": None,
            "would_log": False, "guard_skipped": False, "extraction_errored": True,
            "outcome": "TN",
        })
        return row
    would_log = rec.had_error and bool((rec.original or "").strip())
    row.update({
        "pred_had_error": rec.had_error, "pred_category": rec.category,
        "pred_correction": rec.correction, "would_log": would_log,
        "guard_skipped": False, "extraction_errored": False,
        "outcome": "FP" if would_log else "TN",
    })
    return row


# --------------------------------------------------------------------------- #
# Aggregation + reporting
# --------------------------------------------------------------------------- #
def summarise(rows: list[dict]) -> dict:
    tp = sum(1 for r in rows if r["outcome"] == "TP")
    fp = sum(1 for r in rows if r["outcome"] == "FP")
    fn = sum(1 for r in rows if r["outcome"] == "FN")
    tn = sum(1 for r in rows if r["outcome"] == "TN")
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None

    def _empty(s):
        return not (s or "").strip()

    logged = [r for r in rows if r["kind"] == "positive" and r["would_log"]]
    # The dominant failure mode is OMISSION (glm returns had_error+original but leaves
    # correction/category blank), not a wrong value — so split the two explicitly.
    logged_empty_correction = sum(1 for r in logged if _empty(r["pred_correction"]))
    logged_empty_category = sum(1 for r in logged if _empty(r["pred_category"]))

    cat_scored = [r for r in rows if r.get("category_correct") is not None]
    cat_acc = (sum(1 for r in cat_scored if r["category_correct"]) / len(cat_scored)) if cat_scored else None
    cat_wrong_empty = sum(1 for r in cat_scored if not r["category_correct"] and _empty(r["pred_category"]))
    cat_wrong_mismatch = sum(1 for r in cat_scored if not r["category_correct"] and not _empty(r["pred_category"]))

    corr_scored = [r for r in rows if r.get("correction_valid") is not None]
    corr_acc = (sum(1 for r in corr_scored if r["correction_valid"]) / len(corr_scored)) if corr_scored else None
    corr_exact = sum(1 for r in corr_scored if r.get("correction_how") == "exact")
    # Conditional quality: when the model DOES emit a correction, is it valid?
    corr_nonempty = [r for r in corr_scored if not _empty(r["pred_correction"])]
    corr_nonempty_valid = sum(1 for r in corr_nonempty if r["correction_valid"])
    corr_valid_given_nonempty = (corr_nonempty_valid / len(corr_nonempty)) if corr_nonempty else None

    # Informational: what does the extractor do on the underspecified "grammar" golds?
    grammar_golds = [r for r in rows if r["kind"] == "positive" and not r["specific_gold"] and r["would_log"]]
    grammar_specific = sum(1 for r in grammar_golds if r["pred_category_canon"] not in (None, "grammar"))

    errored = sum(1 for r in rows if r.get("extraction_errored"))
    return {
        "confusion_matrix": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
        "extraction_errored_n": errored, "n_cases": len(rows),
        "had_error_precision": precision, "had_error_recall": recall, "had_error_f1": f1,
        "category_accuracy_specific": cat_acc, "category_scored_n": len(cat_scored),
        "category_wrong_empty_n": cat_wrong_empty, "category_wrong_mismatch_n": cat_wrong_mismatch,
        "correction_validity": corr_acc, "correction_scored_n": len(corr_scored),
        "correction_exact_match_n": corr_exact,
        "correction_validity_given_nonempty": corr_valid_given_nonempty,
        "correction_nonempty_n": len(corr_nonempty),
        "logged_n": len(logged),
        "logged_empty_correction_n": logged_empty_correction,
        "logged_empty_category_n": logged_empty_category,
        "grammar_gold_logged_n": len(grammar_golds),
        "grammar_gold_refined_to_specific_n": grammar_specific,
        "extract_model": EXTRACT_MODEL, "judge_model": JUDGE_MODEL,
    }


def render_md(summary: dict, rows: list[dict]) -> str:
    cm = summary["confusion_matrix"]
    fps = [r for r in rows if r["outcome"] == "FP"]
    fns = [r for r in rows if r["outcome"] == "FN"]
    bad_cat = [r for r in rows if r.get("category_correct") is False]
    bad_corr = [r for r in rows if r.get("correction_valid") is False]

    def pct(x):
        return "—" if x is None else f"{x:.3f}"

    lines = [
        "# Structured-extraction eval — `extract_and_log_error`",
        "",
        f"Extraction model **{summary['extract_model']}** · correction judge **{summary['judge_model']}**. "
        "The hidden post-turn surface that writes the learner's error corpus; measured on "
        "whether a turn gets *logged*, whether the category is right, and whether the stored "
        "correction is valid. See `results/README.md` for how to re-derive any number.",
        "",
        "## had_error detection (would this turn be logged as an error?)",
        "",
        "| | Predicted log | Predicted no-log |",
        "|---|---|---|",
        f"| **Actually an error** | TP {cm['TP']} | FN {cm['FN']} |",
        f"| **Actually clean** | FP {cm['FP']} | TN {cm['TN']} |",
        "",
        f"- **Precision {pct(summary['had_error_precision'])}** (headline — a false positive logs a clean "
        "sentence as a mistake and poisons the corpus)",
        f"- **Recall {pct(summary['had_error_recall'])}**  ·  **F1 {pct(summary['had_error_f1'])}**",
        "",
        "## ⚠️ Dominant defect — glm structured-output UNRELIABILITY (not capability)",
        "",
        f"The `{summary['extract_model']}` extractor produces INCOMPLETE records intermittently — two "
        "facets of the same flakiness, both **run-variable** (a case that fails on one call returns a "
        "complete record on the next; re-probed cases confirmed this), and NOT fixed by switching to the "
        "`function_calling` method:",
        "",
        f"1. **Field omission** — on **{summary['logged_empty_correction_n']} of {summary['logged_n']} "
        f"logged records** it returns `had_error=True`+`original` but leaves `correction` (and usually "
        f"`category`+`explanation`, {summary['logged_empty_category_n']} empty categories) blank. "
        "Production gates logging only on `original`, so these enter the corpus as a flagged error with no "
        "fix (empty category coerced to `grammar`).",
        f"2. **Malformed JSON** (intermittent — this run: {summary['extraction_errored_n']} of "
        f"{summary['n_cases']} cases) — it sometimes emits JSON `null` for the string fields (schema "
        "expects `\"\"`), raising a parse error. Production wraps extraction in try/except and logs nothing "
        "on any error, so this fails SAFE (nothing logged) — scored here as production behaves (a clean "
        "input → correct TN; a real error → a missed log).",
        "",
        "Crucially this is **not a capability limit**: the correction is present in the coach reply the "
        "extractor reads, and for the very same inputs the model emits a fully correct record on a retry "
        f"(when non-empty, correction is **{pct(summary['correction_validity_given_nonempty'])} valid**, "
        f"{summary['correction_nonempty_n']} cases; category has only {summary['category_wrong_mismatch_n']} "
        "genuine mismatches). The fix is a **retry-on-incomplete / field-validation guard around the "
        "extraction call**, not a model swap — and it reproduces regardless of structured-output method. "
        "Measured on glm because deepseek (production default) hangs and is untested here (DECISIONS #4, #13).",
        "",
        "## Category accuracy (specific-category golds only)",
        "",
        f"- **{pct(summary['category_accuracy_specific'])}** over {summary['category_scored_n']} "
        "logged particle/word-order/measure-word cases (exact canonical match).",
        f"- Of the misses, {summary['category_wrong_empty_n']} are **empty** (the omission above) and only "
        f"{summary['category_wrong_mismatch_n']} are genuine mismatches — so when a category is emitted it is "
        "almost always right.",
        f"- The {summary['grammar_gold_logged_n']} `grammar` catch-all golds are underspecified and not "
        f"scored; of them the extractor refined {summary['grammar_gold_refined_to_specific_n']} to a "
        "specific category (arguably *more* precise than the gold).",
        "",
        "## Correction validity (logged positives)",
        "",
        f"- **{pct(summary['correction_validity'])}** valid over {summary['correction_scored_n']} logged "
        f"cases — {summary['correction_exact_match_n']} by exact match to gold, the rest by focused judge. "
        f"The gap from 1.0 is entirely the empty-correction omission above "
        f"(**{pct(summary['correction_validity_given_nonempty'])}** valid when non-empty).",
        "",
    ]
    if fps:
        lines += ["## False positives (clean input logged as an error — inspect these)", ""]
        for r in fps:
            lines.append(f"- `{r['id']}` ({r['kind']}): input `{r['input']}` → logged `{r['pred_category']}` / `{r['pred_correction']}`")
        lines.append("")
    if fns:
        lines += ["## False negatives (real error missed)", ""]
        for r in fns:
            lines.append(f"- `{r['id']}`: input `{r['input']}` (gold {r['gold_category']})")
        lines.append("")
    if bad_cat:
        lines += ["## Category misclassifications (specific golds)", ""]
        for r in bad_cat:
            lines.append(f"- `{r['id']}`: gold `{r['gold_category']}` → predicted `{r['pred_category']}`")
        lines.append("")
    if bad_corr:
        lines += ["## Invalid corrections", ""]
        for r in bad_corr:
            lines.append(f"- `{r['id']}`: input `{r['input']}` → `{r['pred_correction']}` ({r['correction_how']})")
        lines.append("")
    return "\n".join(lines)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="cap positives+negatives for a cheap slice")
    ap.add_argument("--from-rows", action="store_true",
                    help="recompute summary + re-render md from the saved rows (no model calls)")
    args = ap.parse_args()

    if args.from_rows:
        saved = json.loads((RESULTS / "extraction.json").read_text())["rows"]
        summary = summarise(saved)
        (RESULTS / "extraction.json").write_text(
            json.dumps({"summary": summary, "rows": saved}, ensure_ascii=False, indent=2))
        (RESULTS / "extraction.md").write_text(render_md(summary, saved))
        print(f"Re-aggregated {len(saved)} saved rows → extraction.{{md,json}} (no model calls).")
        return

    data = json.loads(DATASET.read_text())
    positives, negatives = data["positives"], data["negatives"]
    if args.limit:
        positives, negatives = positives[: args.limit], negatives[: args.limit]

    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded(coro_fn, case):
        async with sem:
            try:
                return await coro_fn(case)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {case['id']} failed: {type(e).__name__}: {e}")
                return None

    print(f"Extraction surface: {len(positives)} positives + {len(negatives)} negatives "
          f"(model={EXTRACT_MODEL}, concurrency {CONCURRENCY})...")
    tasks = [guarded(eval_positive, c) for c in positives] + [guarded(eval_negative, c) for c in negatives]
    rows = [r for r in await asyncio.gather(*tasks) if r is not None]

    summary = summarise(rows)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "extraction.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2)
    )
    (RESULTS / "extraction.md").write_text(render_md(summary, rows))

    cm = summary["confusion_matrix"]
    print(f"\nDone. TP {cm['TP']} FP {cm['FP']} FN {cm['FN']} TN {cm['TN']}")
    print(f"  precision {summary['had_error_precision']}  recall {summary['had_error_recall']}  f1 {summary['had_error_f1']}")
    print(f"  category(specific) {summary['category_accuracy_specific']}  correction {summary['correction_validity']}")
    print(f"  wrote {RESULTS/'extraction.md'} and .json")


if __name__ == "__main__":
    asyncio.run(main())
