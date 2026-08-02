"""Voice-coach quality surface → results/voice_coach_quality.{md,json}.

Scores `agent.run_voice_coach` — the spoken coaching brain — on the behaviours the
text-coach evals don't cover, because the voice coach has extra rules the reference-based
correction judge can't see:

  * FORMAT: a spoken TL;DR on line 1 (one short English sentence, no markdown), then the
    breakdown below. `_split_spoken` reads line 1 aloud, so a malformed first line is a
    real defect (the learner hears markdown / a paragraph).
  * ENGLISH: explain in English even when the learner spoke Mandarin (Chinese only for
    examples).
  * NOISE: on a garbled / mis-transcribed turn, ask to repeat rather than inventing a
    correction for noise (STT is lossy on a voice product).
  * HISTORY: resolve a referential turn ("why was that wrong?") from the recent spoken
    context, without asking the learner to repeat.

Each case runs through the REAL run_voice_coach (gpt-4o-mini + the grammar tools). Scoring
is two-layered, matching the repo's methodology:
  - DETERMINISTIC (code decides): spoken line is English + markdown-free, a breakdown exists,
    spoken-line speakability (word count). No LLM, no flakiness.
  - JUDGE (LLM decides, temp 0): meets_expectation / misleading / explanation_in_english /
    asks_to_repeat, scored against each case's authored EXPECTATION by an independent judge
    (`JUDGE_MODEL`, default glm — not the gpt-4o-mini under test). `--verify-judge MODEL`
    re-scores with a second judge and reports agreement, so the judge itself is vetted.

The headline is **misleading rate** (a wrong grammar claim spoken aloud is the dangerous
error — precision-first, like the extraction + router surfaces) alongside meets_expectation.

Run:  EVAL_CONCURRENCY=4 uv run python evals/surfaces/voice_coach/voice_coach_quality_eval.py
      uv run python evals/surfaces/voice_coach/voice_coach_quality_eval.py --from-rows        # re-aggregate, no calls
      uv run python evals/surfaces/voice_coach/voice_coach_quality_eval.py --verify-judge gpt-4o-mini
Prereq: datagen/voice_coach_dataset.json (build with generate_voice_coach_dataset.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

import memory  # noqa: E402
from agent import VOICE_COACH_MODEL, build_voice_coach, run_voice_coach  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from lib import llm_judge  # noqa: E402

# This surface's judge is gpt-4o (independent + reliable), chosen after two rejections:
#   - glm (the repo default) left the `reason` field empty and produced ~4/20 false negatives
#     — the structured-output unreliability the extraction surface also hit.
#   - gpt-4o-mini fills verdicts reliably BUT is the same model as the coach under test, and a
#     gpt-4o cross-check (`--verify-judge gpt-4o`) proved that mattered: gpt-4o-mini excused 3
#     borderline MISLEADING claims on its own outputs (sc04, g02, g03) that the stronger,
#     independent gpt-4o flags. Same-model self-preference, exactly on the headline metric.
# gpt-4o is stronger than the gpt-4o-mini coach and graded it STRICTER, so it isn't colluding
# (same-provider is the residual caveat; a cross-provider judge — qwen — stalls on OpenRouter).
# Override with JUDGE_MODEL.
llm_judge.JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o")

DATASET = _env.DATAGEN / "voice_coach_dataset.json"
RESULTS = _env.RESULTS
CONCURRENCY = int(os.environ.get("EVAL_CONCURRENCY", "4"))
TYPE_ORDER = ["sentence_coach", "question", "referential", "garbled"]
SPEAK_MAX_WORDS = 40   # a spoken headline over this is too long to be "one short sentence"
SPOKEN_HAN_MAX = 0.15  # the spoken line should be English; allow a quoted char/word

_HAN = re.compile(r"[一-鿿]")
_MD_CHARS = set("*#`|")
_LIST_PREFIX = re.compile(r"^\s*([-*+]\s|\d+\.\s)")


# --------------------------------------------------------------------------- #
# Deterministic checks (no LLM)
# --------------------------------------------------------------------------- #
def han_ratio(s: str) -> float:
    chars = [c for c in s if not c.isspace()]
    if not chars:
        return 0.0
    return sum(1 for c in chars if _HAN.match(c)) / len(chars)


def spoken_word_count(spoken: str) -> int:
    # English words by whitespace, plus each Han char counts as a "word" (worst case for length).
    return len(re.findall(r"\S+", re.sub(r"[一-鿿]", " ", spoken))) + len(_HAN.findall(spoken))


def det_checks(spoken: str, full: str) -> dict:
    spoken = (spoken or "").strip()
    full = (full or "").strip()
    present = bool(spoken) and spoken != "……"
    md_free = not any(ch in spoken for ch in _MD_CHARS) and not _LIST_PREFIX.match(spoken)
    breakdown_present = full != spoken  # something below the spoken headline
    wc = spoken_word_count(spoken)
    return {
        "spoken_present": present,
        "spoken_english": han_ratio(spoken) <= SPOKEN_HAN_MAX,
        "spoken_md_free": bool(md_free),
        "breakdown_present": breakdown_present,
        "spoken_word_count": wc,
        "spoken_speakable": wc <= SPEAK_MAX_WORDS,
        # Format validity applies to substantive coaching, not a "please repeat" clarification.
        "split_ok": present and bool(md_free),
    }


def context_text(history: list[dict]) -> str:
    return "\n".join(f"{h['role']}: {h['content']}" for h in history)


def history_messages(history: list[dict]) -> list:
    out = []
    for h in history:
        out.append(HumanMessage(content=h["content"]) if h["role"] == "user"
                   else AIMessage(content=h["content"]))
    return out


# --------------------------------------------------------------------------- #
# One case
# --------------------------------------------------------------------------- #
async def eval_case(graph, case: dict) -> dict:
    spoken, full = await run_voice_coach(graph, history_messages(case["history"]), case["question"])
    det = det_checks(spoken, full)
    verdict = await llm_judge.judge_voice_answer(
        context_text(case["history"]), case["question"], case["expectation"], full)
    return {
        "id": case["id"], "type": case["type"], "question": case["question"],
        "note": case.get("note"),
        "spoken": spoken, "full": full,
        "det": det,
        "meets_expectation": verdict.meets_expectation,
        "misleading": verdict.misleading,
        "explanation_in_english": verdict.explanation_in_english,
        "asks_to_repeat": verdict.asks_to_repeat,
        "judge_reason": verdict.reason,
    }


async def rejudge_case(cases_by_id: dict, row: dict) -> dict:
    """Re-score one saved row with the CURRENT judge model (for --verify-judge)."""
    case = cases_by_id[row["id"]]
    v = await llm_judge.judge_voice_answer(
        context_text(case["history"]), case["question"], case["expectation"], row["full"])
    return {"id": row["id"], "meets_expectation": v.meets_expectation, "misleading": v.misleading,
            "asks_to_repeat": v.asks_to_repeat, "explanation_in_english": v.explanation_in_english}


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _rate(rows, key):
    return (sum(1 for r in rows if r[key]) / len(rows)) if rows else None


def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    non_garbled = [r for r in rows if r["type"] != "garbled"]
    garbled = [r for r in rows if r["type"] == "garbled"]
    referential = [r for r in rows if r["type"] == "referential"]

    def det_rate(rs, k):
        return (sum(1 for r in rs if r["det"][k]) / len(rs)) if rs else None

    # Speakability over the substantive (non-garbled) spoken lines.
    wcs = sorted(r["det"]["spoken_word_count"] for r in non_garbled)
    def pct(q):
        return wcs[min(len(wcs) - 1, int(q * len(wcs)))] if wcs else None

    per_type = {}
    for t in TYPE_ORDER:
        trs = [r for r in rows if r["type"] == t]
        if not trs:
            continue
        per_type[t] = {
            "n": len(trs),
            "meets_expectation": _rate(trs, "meets_expectation"),
            "misleading_n": sum(1 for r in trs if r["misleading"]),
            "english": _rate(trs, "explanation_in_english"),
            "asks_to_repeat_n": sum(1 for r in trs if r["asks_to_repeat"]),
        }

    return {
        "n_cases": n,
        "model": VOICE_COACH_MODEL,
        "judge_model": llm_judge.JUDGE_MODEL,
        # headlines
        "meets_expectation_rate": _rate(rows, "meets_expectation"),
        "misleading_n": sum(1 for r in rows if r["misleading"]),
        "misleading_ids": [r["id"] for r in rows if r["misleading"]],
        "english_rate_judge": _rate(rows, "explanation_in_english"),
        # deterministic format
        "spoken_english_rate": det_rate(rows, "spoken_english"),
        "spoken_md_free_rate": det_rate(rows, "spoken_md_free"),
        "split_ok_rate": det_rate(non_garbled, "split_ok"),
        "breakdown_present_rate": det_rate(non_garbled, "breakdown_present"),
        "speakable_rate": det_rate(non_garbled, "spoken_speakable"),
        "spoken_wc_p50": pct(0.50), "spoken_wc_p95": pct(0.95),
        "spoken_wc_max": (wcs[-1] if wcs else None),
        # behaviour slices
        "noise_ask_repeat_rate": _rate(garbled, "asks_to_repeat") if garbled else None,
        "noise_meets_rate": _rate(garbled, "meets_expectation") if garbled else None,
        "referential_meets_rate": _rate(referential, "meets_expectation") if referential else None,
        "referential_wrong_repeat_n": sum(1 for r in referential if r["asks_to_repeat"]),
        "per_type": per_type,
    }


def render_md(summary: dict, rows: list[dict]) -> str:
    def p(x):
        return "—" if x is None else f"{x:.3f}"

    fails = [r for r in rows if not r["meets_expectation"]]
    misleads = [r for r in rows if r["misleading"]]
    non_english = [r for r in rows if not r["explanation_in_english"]]

    lines = [
        "# Voice-coach quality eval — `run_voice_coach`",
        "",
        f"{summary['n_cases']} spoken-coach turns through the real voice coach "
        f"(**{summary['model']}** + grammar tools); judge = **{summary['judge_model']}** (independent, "
        "temp 0). Scores the behaviours the text-coach evals don't cover: the spoken-TL;DR format, "
        "English-only explanation, noise→ask-to-repeat, and resolving referential turns from spoken "
        "history. Deterministic checks decide format; the judge decides content against each case's "
        "authored expectation. See `results/README.md` to re-derive any number.",
        "",
        "## Headlines",
        "",
        f"- **Misleading claims: {summary['misleading_n']}/{summary['n_cases']}** "
        f"(the dangerous error — a wrong grammar claim spoken aloud"
        + (f"; ids: {', '.join(summary['misleading_ids'])}" if summary["misleading_ids"] else "") + ")",
        f"- **Meets expectation: {p(summary['meets_expectation_rate'])}** (did the reply do the job "
        "the turn required, per its rubric)",
        f"- **Explanation in English (judge): {p(summary['english_rate_judge'])}** · "
        f"spoken line English (deterministic): {p(summary['spoken_english_rate'])}",
        f"- **Split format valid: {p(summary['split_ok_rate'])}** (spoken line present + markdown-free) "
        f"· breakdown present {p(summary['breakdown_present_rate'])}",
        "",
        "## Spoken-line speakability (non-garbled turns)",
        "",
        f"The first line is read aloud, so it must be one short sentence. Word count — p50 "
        f"**{summary['spoken_wc_p50']}**, p95 **{summary['spoken_wc_p95']}**, max "
        f"**{summary['spoken_wc_max']}** (over {SPEAK_MAX_WORDS} words = too long to speak). "
        f"Speakable rate {p(summary['speakable_rate'])}, markdown-free {p(summary['spoken_md_free_rate'])}.",
        "",
        "## Behaviour slices",
        "",
        f"- **Noise robustness** (garbled turns): correctly handled **{p(summary['noise_meets_rate'])}** "
        "— i.e. asked the learner to clarify instead of inventing a correction for the noise. "
        f"(The `asks_to_repeat` judge flag, {p(summary['noise_ask_repeat_rate'])}, is NOT a reliable "
        "noise signal: the coach's trailing 'try saying …' drill reads to the judge as a repeat "
        "request even when it fabricated a correction — so meets_expectation is the metric here.)",
        f"- **History grounding** (referential turns): meets-expectation "
        f"{p(summary['referential_meets_rate'])}; wrongly asked to repeat "
        f"{summary['referential_wrong_repeat_n']}/{len([r for r in rows if r['type']=='referential'])} "
        "(the context already held the answer).",
        "",
        "## By turn type",
        "",
        "| Type | n | meets_expectation | misleading | English |",
        "|---|---|---|---|---|",
    ]
    for t in TYPE_ORDER:
        pt = summary["per_type"].get(t)
        if not pt:
            continue
        lines.append(f"| {t} | {pt['n']} | {p(pt['meets_expectation'])} | {pt['misleading_n']} | "
                     f"{p(pt['english'])} |")

    if misleads:
        lines += ["", "## Misleading claims (inspect — spoken to the learner)", ""]
        for r in misleads:
            lines.append(f"- `{r['id']}` ({r['type']}): {r['judge_reason']}")
            lines.append(f"  - spoken: `{r['spoken']}`")
    if non_english:
        lines += ["", "## Explanation not in English", ""]
        for r in non_english:
            lines.append(f"- `{r['id']}` ({r['type']}): `{r['spoken']}`")
    if fails:
        lines += ["", "## Did not meet expectation", ""]
        for r in fails:
            note = f" — _{r['note']}_" if r.get("note") else ""
            lines.append(f"- `{r['id']}` ({r['type']}){note}: {r['judge_reason']}")
            lines.append(f"  - spoken: `{r['spoken']}`")
    lines += [
        "",
        "## Caveats",
        "",
        "- **Small hand-authored set (n=20), our rubrics.** Deterministic format/speakability numbers "
        "are exact; the content verdicts are one judge's call — vet with `--verify-judge <model>` "
        "(agreement in the JSON). The garbled slice is only n=4, so its rate is directional.",
        "- **The coach runs at production temperature (0.2), so its replies — and therefore the "
        "judge-based rates — vary run to run.** The findings note reports the spread across repeated "
        "runs; the deterministic format checks are stable.",
        "- **The judge scores against an authored EXPECTATION, not a single reference string** — "
        "multiple correct explanations pass, matching how the text-coach correction judge works.",
        "- **The deterministic spoken-line-English rate understates compliance**: the prompt asks the "
        "headline to include the corrected Chinese sentence, so a legitimate headline can exceed the "
        f"{int(SPOKEN_HAN_MAX*100)}% Han-ratio threshold. The judge's explanation_in_english (on the "
        "prose) is the truer English signal.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-rows", action="store_true",
                    help="re-aggregate + re-render from saved rows (no model calls)")
    ap.add_argument("--verify-judge", metavar="MODEL", default=None,
                    help="re-judge every saved row with a second judge model and report agreement "
                         "on meets_expectation / misleading / asks_to_repeat (vets the judge)")
    args = ap.parse_args()

    stem = "voice_coach_quality"

    if args.from_rows or args.verify_judge:
        saved = json.loads((RESULTS / f"{stem}.json").read_text())
        rows = saved["rows"]
        if args.verify_judge:
            cases = {c["id"]: c for c in json.loads(DATASET.read_text())["cases"]}
            primary = llm_judge.JUDGE_MODEL
            llm_judge.JUDGE_MODEL = args.verify_judge  # _judge() reads this global per call
            sem = asyncio.Semaphore(CONCURRENCY)

            async def guarded(row):
                async with sem:
                    try:
                        return await rejudge_case(cases, row)
                    except Exception as e:  # noqa: BLE001
                        print(f"  ! rejudge {row['id']} failed: {type(e).__name__}: {e}")
                        return None

            print(f"Re-judging {len(rows)} rows with '{args.verify_judge}' (primary was '{primary}')...")
            second = [r for r in await asyncio.gather(*[guarded(r) for r in rows]) if r]
            by_id = {r["id"]: r for r in second}
            keys = ["meets_expectation", "misleading", "asks_to_repeat", "explanation_in_english"]
            agree = {k: 0 for k in keys}
            compared = 0
            for r in rows:
                s = by_id.get(r["id"])
                if not s:
                    continue
                compared += 1
                for k in keys:
                    agree[k] += int(bool(r[k]) == bool(s[k]))
            report = {"primary_judge": primary, "second_judge": args.verify_judge,
                      "n_compared": compared,
                      "agreement": {k: (agree[k] / compared if compared else None) for k in keys},
                      "second_rows": second}
            saved["judge_verify"] = report
            (RESULTS / f"{stem}.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2))
            print(f"Judge agreement ({primary} vs {args.verify_judge}, n={compared}):")
            for k in keys:
                a = report["agreement"][k]
                print(f"  {k}: {a:.3f}" if a is not None else f"  {k}: —")
            return
        summary = summarise(rows)
        (RESULTS / f"{stem}.json").write_text(
            json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
        (RESULTS / f"{stem}.md").write_text(render_md(summary, rows))
        print(f"Re-aggregated {len(rows)} saved rows → {stem}.{{md,json}} (no model calls).")
        return

    memory.load_reference_data()  # seed the grammar corpus so grammar_rule_fetcher works
    graph = build_voice_coach("voice-coach-eval")
    cases = json.loads(DATASET.read_text())["cases"]
    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded(case):
        async with sem:
            try:
                return await eval_case(graph, case)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {case['id']} failed: {type(e).__name__}: {e}")
                return None

    print(f"Voice-coach quality surface: {len(cases)} cases "
          f"(coach={VOICE_COACH_MODEL}, judge={llm_judge.JUDGE_MODEL}, concurrency {CONCURRENCY})...")
    rows = [r for r in await asyncio.gather(*[guarded(c) for c in cases]) if r is not None]
    order = {c["id"]: i for i, c in enumerate(cases)}
    rows.sort(key=lambda r: order[r["id"]])

    summary = summarise(rows)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{stem}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / f"{stem}.md").write_text(render_md(summary, rows))

    print(f"\nDone. meets_expectation {summary['meets_expectation_rate']}  "
          f"misleading {summary['misleading_n']}/{summary['n_cases']}  "
          f"English(judge) {summary['english_rate_judge']}  split_ok {summary['split_ok_rate']}")
    print(f"  noise ask-to-repeat {summary['noise_ask_repeat_rate']}  "
          f"referential meets {summary['referential_meets_rate']}")
    print(f"  wrote {RESULTS / (stem + '.md')} and .json")


if __name__ == "__main__":
    asyncio.run(main())
