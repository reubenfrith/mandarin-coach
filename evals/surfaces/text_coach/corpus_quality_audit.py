"""Corpus-quality audit → results/corpus_audit.{md,json}.

The secondary-error work found the coach's ONE systematic error (把/被 "never both") traces
straight to a corpus `common_mistake` field that over-flattens the rule — and unlike a
low-frequency sampling slip, a corpus error propagates to EVERY reply grounded on that rule.
So this audits the source: it asks a frontier judge whether each of the 98 reference rules'
`explanation` / `common_mistake` asserts something factually WRONG or materially OVER-BROAD in
standard Mandarin (an absolute never/always/only/cannot with real exceptions), while leaving
beginner-appropriate simplifications alone.

This is a FIRST-PASS triage for a human to adjudicate, not an oracle — the judge (default gpt-5,
which caught exactly this class in the secondary-error head-to-head; see
notes/teaching-quality-findings.md) surfaces candidates; a native/expert reviewer keeps or
rejects each. Fixing a flagged rule fixes every downstream reply at once.

Run:  EVAL_CONCURRENCY=5 uv run python evals/surfaces/text_coach/corpus_quality_audit.py
      uv run python evals/surfaces/text_coach/corpus_quality_audit.py --limit 8    # cheap smoke run
      uv run python evals/surfaces/text_coach/corpus_quality_audit.py --from-rows  # re-render, no calls
      JUDGE_MODEL=gpt-4o uv run python .../corpus_quality_audit.py                 # override the judge
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # evals/ on path
from lib import _env  # noqa: E402,F401  bootstrap

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

from lib import llm_judge  # noqa: E402

llm_judge.JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-5")  # frontier judge — this task needs it
RULES = _env.APP_DATA / "grammar_rules.json"
RESULTS = _env.RESULTS
CONCURRENCY = int(os.environ.get("EVAL_CONCURRENCY", "5"))
STEM = "corpus_audit"
SEV_RANK = {"major": 0, "minor": 1, "none": 2}


def _sev(row):
    s = (row.get("severity") or "").strip().lower()
    if s not in SEV_RANK:
        return "major" if row.get("has_issue") else "none"  # normalise odd strings conservatively
    return s


async def audit_one(rule: dict) -> dict:
    examples = f"incorrect: {rule.get('incorrect_example', '')}  →  correct: {rule.get('correct_example', '')}"
    v = await llm_judge.audit_grammar_rule(
        rule.get("name", rule["id"]), rule.get("explanation", ""),
        rule.get("common_mistake", ""), examples)
    return {"id": rule["id"], "name": rule.get("name"), "category": rule.get("category"),
            "hsk_level": rule.get("hsk_level"),
            "has_issue": v.has_issue, "severity": v.severity, "issues": v.issues, "reason": v.reason,
            "explanation": rule.get("explanation", ""), "common_mistake": rule.get("common_mistake", "")}


def summarise(rows: list[dict]) -> dict:
    flagged = [r for r in rows if r["has_issue"]]
    major = [r for r in flagged if _sev(r) == "major"]
    minor = [r for r in flagged if _sev(r) == "minor"]
    return {"n": len(rows), "judge_model": llm_judge.JUDGE_MODEL,
            "flagged": len(flagged), "major": len(major), "minor": len(minor),
            "major_ids": [r["id"] for r in major], "minor_ids": [r["id"] for r in minor]}


def render_md(summary: dict, rows: list[dict]) -> str:
    flagged = sorted([r for r in rows if r["has_issue"]], key=lambda r: (SEV_RANK.get(_sev(r), 1), r["id"]))
    lines = [
        "# Corpus-quality audit — reference grammar rules",
        "",
        f"{summary['n']} rules audited by **{summary['judge_model']}** (frontier judge, temp 0). Flags "
        "`explanation` / `common_mistake` claims that are factually wrong or materially OVER-BROAD in "
        "standard Mandarin — the class that seeds SYSTEMATIC coach errors (a corpus error propagates to "
        "every reply grounded on the rule). **First-pass triage for a human to adjudicate, not an "
        "oracle** — keep/reject each flag.",
        "",
        f"## Flagged: {summary['flagged']}/{summary['n']}  ·  major {summary['major']}  ·  minor {summary['minor']}",
        "",
        "_major = would teach an advanced learner something false; minor = pedantic edge case._",
        "",
        "| rule | severity | the problem (judge — verify) |",
        "|---|---|---|",
    ]
    for r in flagged:
        issue = (r["issues"][0] if r["issues"] else r["reason"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{r['id']}` {r['name']} | {_sev(r)} | {issue[:180]} |")

    lines += ["", "## Detail — every flag (quote → problem → fix)", ""]
    for r in flagged:
        lines.append(f"### `{r['id']}` — {r['name']}  _({_sev(r)})_")
        lines.append(f"- **common_mistake:** {r['common_mistake'] or '(none)'}")
        for e in r["issues"]:
            lines.append(f"- **flag:** {e}")
        lines.append("")

    lines += [
        "## Caveats",
        "",
        f"- **Triage, not truth.** {summary['judge_model']} is strong on this class (it caught the 把/被 "
        "over-broad claim a weaker judge missed), but it is not infallible — a native/expert reviewer "
        "must confirm each flag before editing the corpus. Read `major` first.",
        "- **Silence is not a guarantee.** An unflagged rule is 'no issue the judge could see', not "
        "'verified correct'. A second judge or human sweep is the way to raise recall.",
        "- Fixing a confirmed flag edits `data/grammar_rules.json`; re-seed the corpus (or wipe "
        "`/var/data` on the VM) so grounded replies pick up the corrected rule.",
        "",
    ]
    return "\n".join(lines)


def _examples(rule: dict) -> str:
    return f"incorrect: {rule.get('incorrect_example', '')}  →  correct: {rule.get('correct_example', '')}"


async def run_rerank():
    """Re-rank the FLAGGED rules (from corpus_audit.json) by actual product harm: would the rule,
    applied literally, make the coach mark a CORRECT level-appropriate learner sentence WRONG? Turns
    the over-inclusive audit into a short to-do list (`corpus_audit_todo.{md,json}`)."""
    audit = json.loads((RESULTS / f"{STEM}.json").read_text())
    flagged = [r for r in audit["rows"] if r["has_issue"]]
    rules = json.loads(RULES.read_text())
    rules = {r["id"]: r for r in (rules if isinstance(rules, list) else rules.get("rules", rules))}
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(r):
        async with sem:
            src = rules.get(r["id"], {})
            try:
                v = await llm_judge.judge_rule_harm(
                    r.get("name") or r["id"], src.get("explanation", r.get("explanation", "")),
                    src.get("common_mistake", r.get("common_mistake", "")), _examples(src))
            except Exception as e:  # noqa: BLE001
                print(f"  ! {r['id']} failed: {type(e).__name__}: {str(e).splitlines()[0][:80]}")
                return None
            return {"id": r["id"], "name": r.get("name"), "audit_severity": _sev(r),
                    "would_reject_correct": v.would_reject_correct, "rejected_example": v.rejected_example,
                    "fix": v.fix, "reason": v.reason,
                    "common_mistake": src.get("common_mistake", r.get("common_mistake", ""))}

    print(f"Harm re-rank over {len(flagged)} flagged rules (judge={llm_judge.JUDGE_MODEL}, conc {CONCURRENCY})...")
    rows = [r for r in await asyncio.gather(*[one(r) for r in flagged]) if r is not None]
    todo = [r for r in rows if r["would_reject_correct"]]
    incomplete = [r for r in rows if not r["would_reject_correct"]]

    summary = {"judge_model": llm_judge.JUDGE_MODEL, "n_flagged": len(flagged), "n_judged": len(rows),
               "n_todo": len(todo), "n_incomplete_only": len(incomplete),
               "todo_ids": [r["id"] for r in todo]}
    lines = [
        "# Corpus audit — harm re-rank (the actionable to-do list)",
        "",
        f"Re-ranked the {len(flagged)} audit-flagged rules by the one criterion that matters: would the "
        f"rule, applied literally, make the coach mark a CORRECT level-appropriate (HSK 1-4) learner "
        f"sentence WRONG? Judge = **{summary['judge_model']}**.",
        "",
        f"## To fix: {len(todo)}/{len(flagged)} flagged rules would reject correct usage",
        "",
        f"_(The other {len(incomplete)} are merely incomplete — they omit advanced/edge-register "
        "exceptions a beginner won't produce; leave them for a beginner tool. Still a human's call.)_",
        "",
        "| rule | correct sentence it would wrongly reject | minimal fix |",
        "|---|---|---|",
    ]
    for r in todo:
        ex = (r["rejected_example"] or "").replace("|", "\\|").replace("\n", " ")
        fix = (r["fix"] or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{r['id']}` {r['name']} | {ex[:120]} | {fix[:160]} |")
    lines += ["", "## Detail", ""]
    for r in todo:
        lines.append(f"### `{r['id']}` — {r['name']}")
        lines.append(f"- **common_mistake (current):** {r['common_mistake'] or '(none)'}")
        lines.append(f"- **would wrongly reject:** {r['rejected_example']}")
        lines.append(f"- **fix:** {r['fix']}")
        lines.append("")
    lines += [
        "## Merely incomplete (not editing for a beginner tool — verify)", "",
        ", ".join(f"`{r['id']}`" for r in incomplete) or "(none)", "",
        "## Caveats", "",
        "- Still a judge's triage — confirm each to-do before editing `data/grammar_rules.json`, then "
        "re-seed the corpus so grounded replies pick up the fix.",
        "- The `level-appropriate` cut is a judgement; a rule parked as 'incomplete' may still be worth "
        "a note if your learners are advanced.",
        "",
    ]
    (RESULTS / "corpus_audit_todo.json").write_text(
        json.dumps({"summary": summary, "todo": todo, "incomplete": incomplete}, ensure_ascii=False, indent=2))
    (RESULTS / "corpus_audit_todo.md").write_text("\n".join(lines))
    print(f"\nTo fix: {len(todo)}/{len(flagged)} would reject correct usage; "
          f"{len(incomplete)} incomplete-only.")
    print(f"  to-do: {', '.join(summary['todo_ids'])}")
    print(f"  wrote {RESULTS / 'corpus_audit_todo.md'}")


async def run_confirm_harm(samples: int = 2):
    """EMPIRICAL harm test: feed each re-rank 'rejected_example' (a correct sentence) to the REAL
    coach `samples` times; a rule is CONFIRMED harmful iff the coach marks the correct sentence wrong
    in >=1 sample. Converges the over-flagged candidate list to what the coach actually misfires on —
    behaviour, not opinion. Reads corpus_audit_todo.json; writes corpus_harm_confirmed.{md,json}."""
    import memory  # noqa: PLC0415 — lazy: other modes don't need the coach/corpus
    from agent import build_agent, invoke_with_trace  # noqa: PLC0415

    todo = json.loads((RESULTS / "corpus_audit_todo.json").read_text())["todo"]
    cases = [r for r in todo if (r.get("rejected_example") or "").strip()]
    # Take the Chinese sentence before any ' — ' / ' (' English gloss.
    def sentence_of(r):
        ex = r["rejected_example"].strip()
        for sep in [" — ", " (", "  ", "\n"]:
            if sep in ex:
                ex = ex.split(sep)[0].strip()
        return ex

    memory.load_reference_data()
    llm_judge.JUDGE_MODEL = "gpt-4o"  # cheap detector; the coach is deepseek (independent)
    sem = asyncio.Semaphore(CONCURRENCY)

    async def run_case(r):
        sent = sentence_of(r)
        rejections = []
        for k in range(samples):
            async with sem:
                uid = f"harm_{r['id']}_{k}"
                try:
                    reply, _ = await invoke_with_trace(build_agent(uid).primary, sent, f"{uid}_t")
                except Exception as e:  # noqa: BLE001
                    rejections.append({"k": k, "marked_wrong": None, "evidence": f"(coach failed: {type(e).__name__})", "reply": ""})
                    continue
            v = await llm_judge.judge_coach_rejected(sent, reply)
            rejections.append({"k": k, "marked_wrong": v.marked_wrong, "evidence": v.evidence, "reply": reply})
        confirmed = any(x["marked_wrong"] for x in rejections)
        n_wrong = sum(1 for x in rejections if x["marked_wrong"])
        return {"id": r["id"], "name": r["name"], "sentence": sent,
                "common_mistake": r.get("common_mistake", ""), "fix": r.get("fix", ""),
                "confirmed_harm": confirmed, "n_marked_wrong": n_wrong, "n_samples": len(rejections),
                "samples": rejections}

    print(f"Empirical harm test: {len(cases)} candidate rules x {samples} coach runs "
          f"(coach=deepseek, detector=gpt-4o, conc {CONCURRENCY})...")
    rows = [r for r in await asyncio.gather(*[run_case(r) for r in cases])]
    confirmed = [r for r in rows if r["confirmed_harm"]]
    clear = [r for r in rows if not r["confirmed_harm"]]
    confirmed.sort(key=lambda r: -r["n_marked_wrong"])

    summary = {"coach": "deepseek", "detector": "gpt-4o", "samples": samples,
               "n_candidates": len(rows), "n_confirmed": len(confirmed), "n_clear": len(clear),
               "confirmed_ids": [r["id"] for r in confirmed]}
    lines = [
        "# Corpus harm — EMPIRICAL confirmation (does the coach actually misfire?)",
        "",
        f"Fed each candidate rule's proposed CORRECT sentence to the real coach (**deepseek**, "
        f"{samples}x each); a rule is CONFIRMED harmful iff the coach marked that correct sentence WRONG "
        f"in >=1 run (detector = gpt-4o). Behaviour, not opinion — this converges the over-flagged "
        f"candidate list ({len(rows)}) to what the coach actually gets wrong.",
        "",
        f"## Confirmed harmful: {len(confirmed)}/{len(rows)}",
        "",
        "| rule | correct sentence | coach misfired | fix |",
        "|---|---|---|---|",
    ]
    for r in confirmed:
        ev = ""
        for x in r["samples"]:
            if x["marked_wrong"]:
                ev = (x["evidence"] or "").replace("|", "\\|").replace("\n", " ")[:80]
                break
        fix = (r["fix"] or "").replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(f"| `{r['id']}` {r['name']} | {r['sentence']} | {r['n_marked_wrong']}/{r['n_samples']}: {ev} | {fix} |")
    lines += [
        "",
        f"## Not confirmed ({len(clear)}) — coach affirmed the sentence in all {samples} runs",
        "",
        ", ".join(f"`{r['id']}`" for r in clear) or "(none)",
        "",
        "## Caveats",
        "",
        f"- Coach runs at temperature; {samples} samples/rule is a first cut. A rule marked 'not "
        "confirmed' may still misfire sometimes (false negatives possible); a 'confirmed' one genuinely "
        "misfired at least once (real). Raise `samples` to tighten.",
        "- Assumes gpt-5's proposed sentence is actually correct — spot-check the confirmed list before "
        "editing `data/grammar_rules.json`.",
        "",
    ]
    (RESULTS / "corpus_harm_confirmed.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / "corpus_harm_confirmed.md").write_text("\n".join(lines))
    print(f"\nConfirmed harmful: {len(confirmed)}/{len(rows)} (coach actually misfired)")
    print(f"  {', '.join(summary['confirmed_ids'])}")
    print(f"  wrote {RESULTS / 'corpus_harm_confirmed.md'}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="audit only the first N rules (smoke run)")
    ap.add_argument("--from-rows", action="store_true", help="re-render from saved rows, no calls")
    ap.add_argument("--rerank", action="store_true",
                    help="harm re-rank the flagged rules into an actionable to-do list (reads corpus_audit.json)")
    ap.add_argument("--confirm-harm", action="store_true",
                    help="EMPIRICAL: run each re-rank sentence through the real coach; confirm which rules it misfires on")
    ap.add_argument("--samples", type=int, default=2, help="coach runs per sentence for --confirm-harm")
    args = ap.parse_args()

    if args.rerank:
        await run_rerank()
        return
    if args.confirm_harm:
        await run_confirm_harm(args.samples)
        return

    if args.from_rows:
        saved = json.loads((RESULTS / f"{STEM}.json").read_text())
        rows = saved["rows"]
        (RESULTS / f"{STEM}.md").write_text(render_md(summarise(rows), rows))
        print(f"Re-rendered {len(rows)} saved rows → {STEM}.md (no calls).")
        return

    rules = json.loads(RULES.read_text())
    rules = rules if isinstance(rules, list) else rules.get("rules", rules)
    if args.limit:
        rules = rules[:args.limit]
    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded(rule):
        async with sem:
            try:
                return await audit_one(rule)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {rule['id']} failed: {type(e).__name__}: {str(e).splitlines()[0][:80]}")
                return None

    print(f"Corpus audit: {len(rules)} rules (judge={llm_judge.JUDGE_MODEL}, concurrency {CONCURRENCY})...")
    rows = [r for r in await asyncio.gather(*[guarded(r) for r in rules]) if r is not None]
    order = {r["id"]: i for i, r in enumerate(rules)}
    rows.sort(key=lambda r: order[r["id"]])

    summary = summarise(rows)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{STEM}.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / f"{STEM}.md").write_text(render_md(summary, rows))

    print(f"\nFlagged {summary['flagged']}/{summary['n']}  (major {summary['major']}, minor {summary['minor']})")
    if summary["major_ids"]:
        print(f"  major: {', '.join(summary['major_ids'])}")
    print(f"  wrote {RESULTS / (STEM + '.md')} and .json")


if __name__ == "__main__":
    asyncio.run(main())
