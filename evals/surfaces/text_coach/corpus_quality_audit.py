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


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="audit only the first N rules (smoke run)")
    ap.add_argument("--from-rows", action="store_true", help="re-render from saved rows, no calls")
    args = ap.parse_args()

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
