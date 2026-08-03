"""Teaching-quality surface (SLICE) → results/teaching_quality_slice.{md,json}.

The head-to-head's correction judges ask "is the coach RIGHT?". This surface asks the
orthogonal thing the learner feels: does the reply TEACH? — on two booleans, `explains_why`
and `explanation_in_english` (see lib/llm_judge.judge_teaching).

But teaching quality is the most SUBJECTIVE axis in the suite, so the headline here is NOT the
coach's score — it is the JUDGE'S RELIABILITY: Cohen's κ between the gpt-4o judge and a human's
labels, per dimension. Only if κ is decent is the coach score (or a future before/after) worth
believing. This inverts the usual order deliberately: validate the instrument, then read it.

Three things get reported:
  1. κ + raw agreement (judge vs human) per dimension — the instrument check.
  2. FLOOR: do the known-bad controls (fix-only / Chinese-only / padded-empty) get caught?
  3. LENGTH-BIAS probe: C2a (long, warm, no rule) vs C2b (one line, states the rule). If the
     judge calls the padded one explains_why=True, it's rewarding length, not teaching.

This is a feasibility slice (n=12, 8 real + 4 authored controls) — read the Caveats in the .md
before quoting κ. The full surface would use only real coach outputs and a larger human-labelled
set, would add the `grounded` dimension (check the cited rule against the retrieved corpus), and
would drive a real before/after between two coach prompts.

Run:  uv run python evals/surfaces/text_coach/teaching_quality_eval.py
      uv run python evals/surfaces/text_coach/teaching_quality_eval.py --from-rows   # re-aggregate, no calls
Prereq: datagen/teaching_slice_dataset.json (build with generate_teaching_slice.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

from lib import llm_judge  # noqa: E402

# Independent, strong judge — NOT a coach model (the coach arm is deepseek). gpt-4o routes
# direct to OpenAI; it's the same independent judge the voice surface settled on.
llm_judge.JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o")

DATASET = _env.DATAGEN / "teaching_slice_dataset.json"
RESULTS = _env.RESULTS
CONCURRENCY = int(os.environ.get("EVAL_CONCURRENCY", "4"))
DIMS = ["explains_why", "explanation_in_english"]
STEM = "teaching_quality_slice"


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def cohen_kappa(human: list[bool], judge: list[bool]) -> float | None:
    """Cohen's κ for two binary raters. None if either rater has no variance (κ undefined —
    every pair agrees or the expected-agreement term degenerates); raw agreement covers that case."""
    n = len(human)
    if n == 0:
        return None
    po = sum(1 for h, j in zip(human, judge) if h == j) / n
    ph, pj = sum(human) / n, sum(judge) / n
    pe = ph * pj + (1 - ph) * (1 - pj)   # expected agreement by chance
    if pe >= 1.0:                        # a rater is constant → κ undefined
        return None
    return (po - pe) / (1 - pe)


def raw_agreement(human: list[bool], judge: list[bool]) -> float:
    return sum(1 for h, j in zip(human, judge) if h == j) / len(human) if human else 0.0


def confusion(human: list[bool], judge: list[bool]) -> dict:
    """Judge scored against the human label as ground truth."""
    tp = sum(1 for h, j in zip(human, judge) if h and j)
    tn = sum(1 for h, j in zip(human, judge) if not h and not j)
    fp = sum(1 for h, j in zip(human, judge) if not h and j)   # judge said True, human False
    fn = sum(1 for h, j in zip(human, judge) if h and not j)   # judge said False, human True
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
async def eval_case(case: dict) -> dict:
    v = await llm_judge.judge_teaching(case["learner_input"], case["rule_why"], case["reply"])
    return {
        "id": case["id"], "role": case["role"], "rule_name": case.get("rule_name"),
        "note": case.get("note"),
        "human": case["human_labels"],
        "judge": {"explains_why": v.explains_why, "explanation_in_english": v.explanation_in_english},
        "judge_reason": v.reason,
    }


def summarise(rows: list[dict]) -> dict:
    per_dim = {}
    for dim in DIMS:
        human = [bool(r["human"][dim]) for r in rows]
        judge = [bool(r["judge"][dim]) for r in rows]
        per_dim[dim] = {
            "kappa": cohen_kappa(human, judge),
            "raw_agreement": raw_agreement(human, judge),
            "confusion": confusion(human, judge),
            "human_true": sum(human), "judge_true": sum(judge), "n": len(human),
            "disagreements": [r["id"] for r in rows if bool(r["human"][dim]) != bool(r["judge"][dim])],
        }

    controls = [r for r in rows if r["role"] == "control"]
    # FLOOR: every case a human marked explains_why=False must be caught by the judge.
    floor_cases = [r for r in rows if not r["human"]["explains_why"]]
    floor_caught = [r["id"] for r in floor_cases if not r["judge"]["explains_why"]]
    floor_missed = [r["id"] for r in floor_cases if r["judge"]["explains_why"]]

    by_id = {r["id"]: r for r in rows}
    probe = None
    if "C2a_padded_empty" in by_id and "C2b_terse_why" in by_id:
        padded, terse = by_id["C2a_padded_empty"], by_id["C2b_terse_why"]
        probe = {
            "padded_explains_why_judge": padded["judge"]["explains_why"],   # want False
            "terse_explains_why_judge": terse["judge"]["explains_why"],     # want True
            "length_bias_detected": padded["judge"]["explains_why"] is True,
            "discriminates": (padded["judge"]["explains_why"] is False)
                             and (terse["judge"]["explains_why"] is True),
        }

    return {
        "n_cases": len(rows), "n_real": sum(1 for r in rows if r["role"] == "real"),
        "n_control": len(controls), "judge_model": llm_judge.JUDGE_MODEL,
        "per_dim": per_dim,
        "floor": {"n": len(floor_cases), "caught": floor_caught, "missed": floor_missed},
        "length_bias_probe": probe,
    }


def render_md(summary: dict, rows: list[dict]) -> str:
    def k(x):
        return "—" if x is None else f"{x:+.2f}"

    def kappa_word(x):
        if x is None:
            return "undefined (a rater was constant)"
        if x >= 0.81:
            return "almost perfect"
        if x >= 0.61:
            return "substantial"
        if x >= 0.41:
            return "moderate"
        if x >= 0.21:
            return "fair"
        return "poor"

    s = summary
    lines = [
        "# Teaching-quality eval — SLICE (judge feasibility)",
        "",
        f"{s['n_cases']} cases ({s['n_real']} real coach replies + {s['n_control']} authored controls); "
        f"judge = **{s['judge_model']}** (independent of the deepseek coach, temp 0). A **feasibility "
        "slice**: can an LLM judge even operationalize a teaching-quality rubric, or does it default to "
        "\"everything teaches\" / get fooled by verbosity? What it does NOT establish is whether the judge "
        "tracks an *independent* human — see the ⚠️ below and run the blind-label round for that.",
        "",
        "> ⚠️ **The κ below is CIRCULAR — read it as rubric self-consistency, not validation.** The same "
        "author wrote both the human labels *and* the judge's system prompt, from one rubric, in one "
        "sitting; the prompt pre-answers every control. So κ measures \"does the judge obey the instructions "
        "I wrote,\" not \"does the judge's judgment match an independent human's.\" A high κ here is expected "
        "and cheap. The independent number comes from `--emit-blind` → you label blind → `--score-human`.",
        "",
        "## 1. What genuinely survives the circularity",
        "",
        "These retire a real *\"maybe the model can't do this at all\"* risk, because they don't depend on the "
        "judge agreeing with a standard the judge authored:",
        "",
        f"- **Floor caught: {len(s['floor']['caught'])}/{s['floor']['n']}** — the judge does not default to "
        "\"everything teaches\" (fix-only / Chinese-only / padded-empty all flagged `explains_why=False`).",
    ]
    p0 = s["length_bias_probe"]
    if p0:
        if p0["discriminates"]:
            lines.append("- **Length-bias probe: resisted** — a long, warm, rule-free reply scored "
                         "`explains_why=False` while its one-line twin that states the rule scored `True`. "
                         "Verbosity/sycophancy (a named LLM-judge failure mode) did not fool it on this pair.")
        elif p0["length_bias_detected"]:
            lines.append("- **Length-bias probe: FAILED** — the padded rule-free reply scored `True`. The "
                         "judge is rewarding length; do not trust the axis until fixed.")
    lines += [
        "",
        "## 2. Rubric self-consistency (CIRCULAR — not validation) — judge vs. author labels",
        "",
        "| Dimension | Cohen's κ | Agreement | Judge vs author (as truth) | Disagreements |",
        "|---|---|---|---|---|",
    ]
    for dim in DIMS:
        d = s["per_dim"][dim]
        c = d["confusion"]
        conf = f"fp {c['fp']} · fn {c['fn']} (tp {c['tp']}, tn {c['tn']})"
        dis = ", ".join(d["disagreements"]) or "—"
        lines.append(
            f"| `{dim}` | **{k(d['kappa'])}** ({kappa_word(d['kappa'])}) | "
            f"{d['raw_agreement']:.0%} ({d['n'] - len(d['disagreements'])}/{d['n']}) | {conf} | {dis} |"
        )
    lines += [
        "",
        "_These numbers are self-referential (see ⚠️). `fp` = judge over-credited teaching the author "
        "didn't; `fn` = judge missed teaching the author credited. Zero disagreements ≠ a reliable judge — "
        "it means the rubric is internally consistent._",
        "",
        "## 3. The independent test (not yet run) — blind-label round",
        "",
        "The only way to retire the real risk is a standard the judge did **not** author: a human labels "
        "the real replies blind (no judge output shown), then κ is computed judge-vs-that-human, plus "
        "human-vs-author κ as the ceiling the judge is chasing. Run:",
        "",
        "```",
        "uv run python evals/surfaces/text_coach/teaching_quality_eval.py --emit-blind    # writes a blank sheet",
        "#  … fill in results/teaching_blind_labels.json (true/false per dim) …",
        "uv run python evals/surfaces/text_coach/teaching_quality_eval.py --score-human results/teaching_blind_labels.json",
        "```",
    ]
    # Loud warning only if a floor case slipped through (the headline lives in section 1).
    fl = s["floor"]
    if fl["missed"]:
        lines += ["", f"> ⚠️ **{len(fl['missed'])}/{fl['n']} floor case(s) MISSED** "
                  f"(judge called them explains_why=True): {', '.join(fl['missed'])}. "
                  "The judge is being fooled — investigate before trusting the axis."]

    # Per-case detail
    lines += ["", "## Per-case", "",
              "| id | role | author why/en | judge why/en | agree | judge reason |",
              "|---|---|---|---|---|---|"]
    def yn(b):
        return "✓" if b else "✗"
    for r in rows:
        hw, he = r["human"]["explains_why"], r["human"]["explanation_in_english"]
        jw, je = r["judge"]["explains_why"], r["judge"]["explanation_in_english"]
        agree = "✅" if (hw == jw and he == je) else "❌"
        reason = (r["judge_reason"] or "").replace("|", "\\|")[:90]
        lines.append(f"| {r['id']} | {r['role']} | {yn(hw)}/{yn(he)} | {yn(jw)}/{yn(je)} | {agree} | {reason} |")

    lines += [
        "",
        "## Caveats (read before quoting κ)",
        "",
        "- **The κ is CIRCULAR — it is not validation.** One author wrote the labels AND the judge prompt "
        "from one rubric; the prompt pre-answers the controls. So κ measures rubric self-consistency, not "
        "whether the judge matches an *independent* human. This is not merely \"easy cases\" — even hard "
        "cases would inflate, because the standard isn't independent of the instrument. The `--emit-blind` "
        "round fixes exactly this.",
        "- **`explanation_in_english=False` on the all-Chinese replies encodes a contestable premise** — a "
        "learner who writes full Chinese sentences may read Chinese explanations fine. This is precisely the "
        "kind of judgement a second (blind) labeller might overturn; don't treat it as settled.",
        "- **n=13, single author labeller.** κ here is directional. A real surface needs ≥2 labellers "
        "(human–human κ = the ceiling the judge is chasing) and ~40+ real cases.",
        "- **The real coach is consistently strong on `explains_why`** (all 8 real replies explain the why), "
        "so that dimension's variance comes almost entirely from the controls. `explanation_in_english` has "
        "real variance among the real replies and is the more informative dimension here.",
        "- **`grounded` is deferred.** The full surface would add a (deterministic-ish) check that the rule "
        "the coach cites actually matches the retrieved corpus rule — omitted from the slice to avoid the "
        "retrieval plumbing.",
        "- **Judge is gpt-4o (OpenAI).** Same-provider self-preference isn't a risk here (the coach is "
        "deepseek), but a second judge model would still be worth adding to measure judge–judge stability.",
        "",
    ]
    return "\n".join(lines)


BLIND = RESULTS / "teaching_blind_labels.json"


def emit_blind():
    """Write a blank labelling sheet for the REAL replies only (no author labels, no judge output
    shown), so a second person can label blind. Reading material goes in the companion .md."""
    cases = [c for c in json.loads(DATASET.read_text())["cases"] if c["role"] == "real"]
    sheet = [{"id": c["id"], "explains_why": None, "explanation_in_english": None} for c in cases]
    BLIND.write_text(json.dumps(sheet, ensure_ascii=False, indent=2))
    md = ["# Blind teaching-quality labelling sheet",
          "",
          "> **You are grading the COACH'S REPLY (the tutor's explanation in each code block) — NOT the "
          "learner's sentence.** The learner's error and its correction are already known to be right; "
          "your job is to judge *how well the reply teaches*. Do not assess whether the student's sentence "
          "is correct — that is a different task and will produce the wrong labels.",
          "",
          "For each reply below, decide two true/false questions **without looking at the judge's output "
          "or the author's labels**, then fill them into `teaching_blind_labels.json`:",
          "",
          "- `explains_why`: does the reply explain the underlying RULE/PRINCIPLE (why the learner's version "
          "is wrong / the fix is right), or does it only hand over the corrected sentence?",
          "- `explanation_in_english`: is the coach's EXPLANATORY PROSE in English? (Chinese used only for "
          "the example words/sentences is fine — judge the prose it explains *in*.)",
          "",
          "**Worked example.** Suppose the learner wrote `我很喜欢` and the coach replied:",
          "",
          "> *A) \"✅ Correct! 👍\"* → `explains_why=false` (no rule given), `explanation_in_english=true`.",
          "> *B) \"You need 得 here because a verb + degree complement takes 得, e.g. 说得好.\"* → "
          "`explains_why=true`, `explanation_in_english=true`.",
          "> *C) \"这里要用 得，因为动词后面的程度补语用 得。\"* → `explains_why=true` (a rule is given), "
          "`explanation_in_english=false` (the explanation itself is in Chinese).",
          ""]
    for c in cases:
        md += [f"## {c['id']} — learner wrote: {c['learner_input']}", "",
               f"_(grammar point: {c.get('rule_name') or '—'})_", "",
               "```", c["reply"], "```", ""]
    (RESULTS / "teaching_blind_sheet.md").write_text("\n".join(md))
    print(f"Wrote {BLIND} ({len(sheet)} real cases to label) and teaching_blind_sheet.md (the replies).")
    print("Fill in true/false for each, then run: --score-human " + str(BLIND))


def score_human(path: str):
    """Compute the INDEPENDENT numbers: judge-vs-blind-human κ, plus author-vs-human κ (the ceiling)."""
    human = {r["id"]: r for r in json.loads(pathlib.Path(path).read_text())}
    saved = json.loads((RESULTS / f"{STEM}.json").read_text())["rows"]
    rows = [r for r in saved if r["id"] in human and human[r["id"]].get("explains_why") is not None]
    if not rows:
        print(f"No labelled rows in {path} (fill in true/false first).")
        return
    out = {"n": len(rows), "per_dim": {}}
    for dim in DIMS:
        h = [bool(human[r["id"]][dim]) for r in rows]           # blind human
        j = [bool(r["judge"][dim]) for r in rows]               # judge
        a = [bool(r["human"][dim]) for r in rows]               # original author
        out["per_dim"][dim] = {
            "judge_vs_human_kappa": cohen_kappa(h, j),
            "judge_vs_human_agreement": raw_agreement(h, j),
            "author_vs_human_kappa": cohen_kappa(h, a),          # the ceiling the judge chases
            "author_vs_human_agreement": raw_agreement(h, a),
            "judge_human_disagreements": [r["id"] for r in rows if bool(human[r["id"]][dim]) != bool(r["judge"][dim])],
        }
    (RESULTS / "teaching_quality_blind.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Independent calibration on {len(rows)} blind-labelled real cases:")
    for dim in DIMS:
        d = out["per_dim"][dim]
        def kv(x):
            return "—" if x is None else f"{x:+.2f}"
        print(f"  {dim}")
        print(f"    judge  vs blind-human: κ={kv(d['judge_vs_human_kappa'])}  "
              f"agreement={d['judge_vs_human_agreement']:.0%}  "
              f"(disagree: {', '.join(d['judge_human_disagreements']) or 'none'})")
        print(f"    author vs blind-human: κ={kv(d['author_vs_human_kappa'])}  "
              f"agreement={d['author_vs_human_agreement']:.0%}   ← ceiling the judge is chasing")
    print(f"  wrote {RESULTS / 'teaching_quality_blind.json'}")


def _fmt_pct(x):
    return "—" if x is None else f"{x:.0%}"


async def run_secondary():
    """Judge the coach replies for MISLEADING SECONDARY content (hints/drills/tables/side-claims),
    scored against the expert blind labels as gold. Gold `has_secondary_error` = the cases the
    human marked `explains_why=False` (they failed the reply precisely on a wrong supporting claim);
    their note is the human rationale. This is the axis a human found that no other surface sees."""
    if not BLIND.exists():
        print(f"Need the expert blind labels at {BLIND} (run --emit-blind, label, then this).")
        return
    human = {r["id"]: r for r in json.loads(BLIND.read_text())}
    cases = [c for c in json.loads(DATASET.read_text())["cases"]
             if c["role"] == "real" and c["id"] in human and human[c["id"]].get("explains_why") is not None]
    if not cases:
        print("No labelled real cases to score against.")
        return

    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(c):
        async with sem:
            v = await llm_judge.judge_secondary_errors(c["learner_input"], c.get("rule_name") or "—", c["reply"])
            # Gold: the human failed explains_why ⇒ they saw a wrong supporting claim.
            gold = not bool(human[c["id"]]["explains_why"])
            return {"id": c["id"], "rule_name": c.get("rule_name"),
                    "gold_has_error": gold, "gold_note": human[c["id"]].get("notes", ""),
                    "judge_has_error": v.has_error, "judge_errors": v.errors, "judge_reason": v.reason}

    print(f"Secondary-error judge over {len(cases)} real replies (judge={llm_judge.JUDGE_MODEL})...")
    rows = [r for r in await asyncio.gather(*[one(c) for c in cases])]
    order = {c["id"]: i for i, c in enumerate(cases)}
    rows.sort(key=lambda r: order[r["id"]])

    g = [r["gold_has_error"] for r in rows]
    j = [r["judge_has_error"] for r in rows]
    tp = sum(1 for r in rows if r["gold_has_error"] and r["judge_has_error"])
    fp = sum(1 for r in rows if not r["gold_has_error"] and r["judge_has_error"])
    fn = sum(1 for r in rows if r["gold_has_error"] and not r["judge_has_error"])
    tn = sum(1 for r in rows if not r["gold_has_error"] and not r["judge_has_error"])
    summary = {
        "n": len(rows), "judge_model": llm_judge.JUDGE_MODEL,
        "gold_positives": sum(g), "judge_positives": sum(j),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": (tp / (tp + fp)) if (tp + fp) else None,
        "recall": (tp / (tp + fn)) if (tp + fn) else None,
        "agreement": raw_agreement(g, j), "kappa": cohen_kappa(g, j),
        "caught": [r["id"] for r in rows if r["gold_has_error"] and r["judge_has_error"]],
        "missed": [r["id"] for r in rows if r["gold_has_error"] and not r["judge_has_error"]],
        "false_alarms": [r["id"] for r in rows if not r["gold_has_error"] and r["judge_has_error"]],
    }
    out = {"summary": summary, "rows": rows}
    (RESULTS / "teaching_secondary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    (RESULTS / "teaching_secondary.md").write_text(render_secondary_md(summary, rows))

    print(f"\nSecondary-error detection vs expert gold ({summary['gold_positives']} known errors):")
    print(f"  recall  {summary['tp']}/{summary['gold_positives']} caught "
          f"(missed: {', '.join(summary['missed']) or 'none'})   ← did it find what the human found")
    print(f"  precision {_fmt_pct(summary['precision'])} "
          f"(false alarms: {', '.join(summary['false_alarms']) or 'none'})")
    print(f"  agreement {_fmt_pct(summary['agreement'])}  κ={summary['kappa'] if summary['kappa'] is None else round(summary['kappa'],2)}")
    print(f"  wrote {RESULTS / 'teaching_secondary.md'}")


def render_secondary_md(s: dict, rows: list[dict]) -> str:
    def kv(x):
        return "—" if x is None else f"{x:+.2f}"
    lines = [
        "# Teaching-quality — misleading SECONDARY content",
        "",
        f"{s['n']} real coach replies; judge = **{s['judge_model']}** (independent, temp 0). Checks the axis "
        "no other surface sees: factual errors in the reply's SUPPORTING content (hints, drill answers, "
        "example tables, measure-word choices, exception lists) — the headline correction is out of scope. "
        f"**Gold = an expert's independent blind labels** ({s['gold_positives']}/{s['n']} replies carry a "
        "secondary error), so this measures whether the judge catches what a human caught — it is NOT "
        "self-referential.",
        "",
        "## Can the judge find the expert's errors?",
        "",
        f"- **Recall: {s['tp']}/{s['gold_positives']}** known secondary errors caught"
        + (f" — **missed {', '.join(s['missed'])}**" if s["missed"] else " — caught them all") + ".",
        f"- **Precision: {_fmt_pct(s['precision'])}** ({s['tp']} true / {s['tp'] + s['fp']} flagged"
        + (f"; false alarms on {', '.join(s['false_alarms'])}" if s["false_alarms"] else "; no false alarms") + ").",
        f"- Agreement {_fmt_pct(s['agreement'])}, Cohen's κ **{kv(s['kappa'])}** vs the expert.",
        "",
        "> Recall is the headline: a secondary error is spoken to the learner as fact, so a **miss** is the "
        "dangerous outcome. But read each flag's *content* below — a flag that trips for the wrong reason "
        "isn't really a catch.",
        "",
        "## Per-case — judge vs expert (does it flag for the RIGHT reason?)",
        "",
        "| id | grammar | gold | judge | verdict |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        gold, jud = r["gold_has_error"], r["judge_has_error"]
        if gold and jud:
            verdict = "✅ caught"
        elif gold and not jud:
            verdict = "❌ MISSED"
        elif not gold and jud:
            verdict = "⚠️ false alarm"
        else:
            verdict = "✅ clean"
        lines.append(f"| {r['id']} | {r['rule_name'] or '—'} | {'error' if gold else 'clean'} | "
                     f"{'error' if jud else 'clean'} | {verdict} |")

    lines += ["", "## Detail — what each side flagged", ""]
    for r in rows:
        if not (r["gold_has_error"] or r["judge_has_error"]):
            continue
        lines.append(f"### {r['id']} — {r['rule_name'] or '—'}")
        if r["gold_has_error"]:
            lines.append(f"- **Expert:** {r['gold_note']}")
        if r["judge_errors"]:
            for e in r["judge_errors"]:
                lines.append(f"- **Judge:** {e}")
        elif r["judge_has_error"]:
            lines.append(f"- **Judge:** (flagged, no specific error listed) {r['judge_reason']}")
        else:
            lines.append("- **Judge:** (did not flag)")
        lines.append("")

    lines += [
        "## Caveats",
        "",
        "- **n=9, one expert labeller.** Recall/precision are over a handful of known errors — directional, "
        "not a stable rate. The point is feasibility: *can* the judge see this class at all?",
        "- **This is open-ended grammar correctness**, the hardest thing to ask of a judge. A miss doesn't "
        "mean the axis is hopeless — a stronger/reasoning judge model or corpus-grounded checks are the "
        "next lever. Report the miss honestly rather than hiding it.",
        "- **The gold is derived** from the expert's `explains_why=False` labels (they failed those replies "
        "on a wrong supporting claim); the note is their verbatim rationale.",
        "",
    ]
    return "\n".join(lines)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-rows", action="store_true",
                    help="re-aggregate + re-render from saved rows (no model calls)")
    ap.add_argument("--emit-blind", action="store_true",
                    help="write a blank labelling sheet for the real replies (for an independent labeller)")
    ap.add_argument("--score-human", metavar="FILE", default=None,
                    help="score the judge against a filled blind-label sheet (the independent test)")
    ap.add_argument("--secondary", action="store_true",
                    help="judge misleading SECONDARY content vs the expert blind labels (the human-found axis)")
    args = ap.parse_args()

    if args.emit_blind:
        emit_blind()
        return
    if args.score_human:
        score_human(args.score_human)
        return
    if args.secondary:
        await run_secondary()
        return

    if args.from_rows:
        saved = json.loads((RESULTS / f"{STEM}.json").read_text())
        rows = saved["rows"]
        summary = summarise(rows)
        (RESULTS / f"{STEM}.json").write_text(
            json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
        (RESULTS / f"{STEM}.md").write_text(render_md(summary, rows))
        print(f"Re-aggregated {len(rows)} saved rows → {STEM}.{{md,json}} (no model calls).")
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

    print(f"Teaching-quality slice: {len(cases)} cases (judge={llm_judge.JUDGE_MODEL}, "
          f"concurrency {CONCURRENCY})...")
    rows = [r for r in await asyncio.gather(*[guarded(c) for c in cases]) if r is not None]
    order = {c["id"]: i for i, c in enumerate(cases)}
    rows.sort(key=lambda r: order[r["id"]])

    summary = summarise(rows)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{STEM}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / f"{STEM}.md").write_text(render_md(summary, rows))

    print("\nWhat survives the circularity (see .md — κ here is self-referential):")
    fl = summary["floor"]
    print(f"  floor caught: {len(fl['caught'])}/{fl['n']} non-teaching replies"
          + (f"; ⚠️ MISSED {fl['missed']}" if fl["missed"] else ""))
    p = summary["length_bias_probe"]
    if p:
        print(f"  length-bias probe: resisted={p['discriminates']} "
              f"(padded_why={p['padded_explains_why_judge']}, terse_why={p['terse_explains_why_judge']})")
    print("\nRubric self-consistency (CIRCULAR — not validation):")
    for dim in DIMS:
        d = summary["per_dim"][dim]
        kv = "—" if d["kappa"] is None else f"{d['kappa']:+.2f}"
        print(f"  {dim:26s} κ={kv}  agreement={d['raw_agreement']:.0%}  "
              f"(disagree: {', '.join(d['disagreements']) or 'none'})")
    print("\nNext, the INDEPENDENT test:  --emit-blind  → label blind → --score-human")
    print(f"  wrote {RESULTS / (STEM + '.md')} and .json")


if __name__ == "__main__":
    asyncio.run(main())
