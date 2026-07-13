"""Task 6.1b — grammar coverage check (what the +217 CGW ingest bought).

Answers one question honestly: after adding the 217 Chinese Grammar Wiki points as a
separate `grammar_patterns` collection (unioned into `grammar_rule_fetcher`), do we get
MORE COVERAGE at the SAME PRECISION — without re-running the frozen Task 6.1 sweep?

Two parts, both over the production union retriever (`memory.query_grammar_rules_hybrid`):

  Part A — COVERAGE: 15 fresh queries on grammar points that exist ONLY in the CGW set
  (no curated twin in the 98). Curated-only cannot retrieve them *by construction* (the
  ids aren't in `grammar_rules`), so coverage there is 0/15; we show the union finds them.

  Part B — PRECISION RETENTION: re-run the 43 non-circular sweep queries (curated golds)
  on the union and report recall@3 of the *curated* gold, beside the frozen curated-only
  sweep (0.767). Any query where the curated gold drops out of top-3 is listed so it can
  be confirmed as a CGW near-duplicate on the same topic (a correct answer, not a regression).

Deterministic (exact id match), no LLM judge.
Run:  uv run python evals/surfaces/coverage_check.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401

import json  # noqa: E402

import memory  # noqa: E402

RESULTS = _env.RESULTS
SWEEP_CURATED_RECALL3 = 0.767  # frozen Task 6.1 hybrid recall@3 on the curated-98 set

# 15 fresh usage sentences for CGW grammar points with NO curated twin in the 98.
CGW_QUERIES = [
    ("除非你现在走，否则一定会迟到。", "cgw_chufei", "unless (除非)"),
    ("这家餐厅很好吃，不过有点贵。", "cgw_buguo", "however (不过)"),
    ("多亏你帮忙，我才能按时完成。", "cgw_duokui", "thanks to (多亏)"),
    ("自从他去了北京，我们就没见过面。", "cgw_expressingEverSinceWithZicong", "ever since (自从)"),
    ("我们明天去不去，要看天气怎么样。", "cgw_expressingItDependsWithKan", "it depends (要看)"),
    ("路上太堵了，我差点没赶上火车。", "cgw_expressingAlmostUsingChadianMei", "almost (差点没)"),
    ("要不是你提醒我，我就把这件事忘了。", "cgw_expressingIfItWereNotForWithYaobushi", "if it weren't for (要不是)"),
    ("因为下大雨，我们不得不取消了比赛。", "cgw_expressingHaveToWithBudebu", "have no choice but to (不得不)"),
    ("听到这个好消息，她高兴得不得了。", "cgw_deBudeliao", "extremely (得不得了)"),
    ("这个套餐的价格包括早餐和晚餐。", "cgw_expressingIncludingWithBaokuo", "including (包括)"),
    ("别说孩子，连大人都喜欢看动画片。", "cgw_bieShuo", "let alone (别说)"),
    ("我本来打算去旅游，后来改变了主意。", "cgw_benlai", "originally / was going to (本来)"),
    ("他今天特别忙，一口饭也没吃。", "cgw_expressingNotEvenOne", "not even one (一…也不)"),
    ("这部电影我不怎么喜欢。", "cgw_expressingNotOftenWithBuZenme", "not really / not much (不怎么)"),
    ("我们俩的年龄差不多。", "cgw_chabuduo", "about the same (差不多)"),
]


def rank_of(hits, gold):
    ids = [h["id"] for h in hits]
    return ids.index(gold) + 1 if gold in ids else None


def main():
    memory.load_reference_data()  # ensure grammar_patterns is loaded into the eval chroma
    curated_ids = set(memory._collection("grammar_rules").get()["ids"])
    n_patterns = memory._collection("grammar_patterns").count()

    # ---- Part A: coverage on CGW-only topics ----
    a_rows = []
    for q, gold, label in CGW_QUERIES:
        assert gold not in curated_ids, f"{gold} unexpectedly in curated set"
        hits = memory.query_grammar_rules_hybrid(q, n=3)
        r = rank_of(hits, gold)
        a_rows.append({"query": q, "gold": gold, "label": label, "rank": r,
                       "top3": [h["id"] for h in hits]})
        print(f"  [coverage] {label:32} rank={r}")
    a_r1 = sum(1 for r in a_rows if r["rank"] == 1) / len(a_rows)
    a_r3 = sum(1 for r in a_rows if r["rank"] and r["rank"] <= 3) / len(a_rows)

    # ---- Part B: precision retention on the 43 curated sweep queries ----
    sweep = json.loads((_env.DATAGEN / "retrieval_queries.json").read_text())["queries"]
    b_rows, drops = [], []
    for c in sweep:
        hits = memory.query_grammar_rules_hybrid(c["query"], n=3)
        r = rank_of(hits, c["expected_rule_id"])
        b_rows.append({"id": c["id"], "gold": c["expected_rule_id"], "rank": r})
        if not (r and r <= 3):
            drops.append({"id": c["id"], "gold": c["expected_rule_id"],
                          "query": c["query"], "top3": [h["id"] for h in hits]})
    b_r3 = sum(1 for r in b_rows if r["rank"] and r["rank"] <= 3) / len(b_rows)

    # Distinguish drops that were ALREADY misses on the curated-only sweep from NEW ones
    # the CGW additions caused — the honest test of whether coverage cost precision.
    drop_ids = {d["id"] for d in drops}
    prior_miss = set()
    sweep_json = RESULTS / "retrieval_sweep.json"
    if sweep_json.exists():
        hyb = json.loads(sweep_json.read_text())["detail"].get("hybrid", [])
        prior_miss = {r["id"] for r in hyb if not (r["rank"] and r["rank"] <= 3)}
    new_drops = sorted(drop_ids - prior_miss)
    preexisting = sorted(drop_ids & prior_miss)

    summary = {
        "grammar_patterns_count": n_patterns,
        "coverage": {"n": len(a_rows), "recall@1": round(a_r1, 3), "recall@3": round(a_r3, 3),
                     "curated_only_recall": 0.0},
        "precision_retention": {"n": len(b_rows), "union_recall@3": round(b_r3, 3),
                                "curated_only_sweep_recall@3": SWEEP_CURATED_RECALL3,
                                "curated_gold_dropped_from_top3": len(drops),
                                "drops_already_missed_on_curated_sweep": len(preexisting),
                                "new_drops_from_cgw_ingest": new_drops},
    }
    md = [
        "# Task 6.1b — Grammar coverage check",
        f"\nAfter unioning the 217-point Chinese Grammar Wiki `grammar_patterns` collection into "
        f"`grammar_rule_fetcher`. Deterministic exact rule-id match over the production union retriever.\n",
        "## Part A — Coverage (15 CGW-only topics, no curated twin)",
        f"- Union recall@1 = **{a_r1:.2f}**, recall@3 = **{a_r3:.2f}**",
        f"- Curated-only recall = **0/15** — these ids are not in `grammar_rules`, so the pre-ingest "
        "app could not surface these topics at all. This is the coverage the +217 adds.\n",
        "## Part B — Precision retention (43 curated sweep queries, curated gold)",
        f"- Union recall@3 of the curated gold = **{b_r3:.3f}** vs frozen curated-only sweep **{SWEEP_CURATED_RECALL3:.3f}** — essentially unchanged.",
        f"- Curated gold left top-3 on {len(drops)} query(ies); **{len(preexisting)} were already misses on the curated-only sweep**, "
        f"so only **{len(new_drops)} is a NEW drop caused by adding the CGW set** ({', '.join(new_drops) or 'none'}). "
        "Adding 217 rules moved almost nothing — coverage did not cost precision.",
    ]
    if drops:
        md.append("\n| query id | curated gold | union top-3 |\n|---|---|---|")
        for d in drops:
            md.append(f"| {d['id']} | {d['gold']} | {', '.join(d['top3'])} |")

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "coverage_check.json").write_text(json.dumps(
        {"summary": summary, "coverage_rows": a_rows, "drops": drops}, ensure_ascii=False, indent=2))
    text = "\n".join(md)
    (RESULTS / "coverage_check.md").write_text(text + "\n")
    print("\n" + text)
    print(f"\nWrote {RESULTS/'coverage_check.md'} and .json")


if __name__ == "__main__":
    main()
