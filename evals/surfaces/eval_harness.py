"""Head-to-head eval harness (Task 5).

Runs every case through TWO systems and scores them side by side:
  * agent  — the full LangGraph agent (tools + per-user ChromaDB corpus)
  * naked  — the strongest fair control arm: same model, best-effort prompt, and
             for memory cases the learner's raw records handed straight into context.

Metrics
  A_stateless  correction accuracy (judge, both arms) · retrieval recall@3 + MRR (agent's
          retriever, deterministic vs expected_rule_id) · factual grounding (both)
  B_small  correction accuracy · personalisation (judge, both) · grounding
  C_scale  aggregation accuracy (extract-then-check vs frozen truth, both) — decisive

Retrieval note: with exact rule-id ground truth we measure context recall/MRR
deterministically (retriever returns the rule's id), which is stronger and cheaper
than RAGAS's LLM-approximated relevance and is exactly the retriever-level signal
Task 6 will vary.

Run:   uv run python evals/eval_harness.py            # full 60-case run
       uv run python evals/surfaces/eval_harness.py --limit 2  # cheap smoke run per type
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
from collections import defaultdict  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from agent import answer_text, build_agent  # noqa: E402
from config import DEFAULT_MODEL, get_llm  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from lib import agg_parse  # noqa: E402
from lib import llm_judge as J  # noqa: E402
import memory  # noqa: E402
from pypinyin import Style, pinyin  # noqa: E402

DATASET = _env.DATAGEN / "test_dataset.json"
RESULTS_DIR = _env.RESULTS

SEM = asyncio.Semaphore(int(os.environ.get("EVAL_CONCURRENCY", "5")))

NAKED_TUTOR_SYS = (
    "You are an expert Mandarin tutor for English speakers. Given a Chinese sentence, "
    "identify any grammar or word-choice error, give the corrected sentence, and explain "
    "the root cause briefly in English. If pinyin or HSK level is relevant, state it. Be "
    "accurate and concise."
)
NAKED_ANALYST_SYS = (
    "You are a meticulous Mandarin learning analyst. You will be given a learner's COMPLETE "
    "error log. Answer counting and trend questions with exact numbers — count carefully, do "
    "not estimate or round. For trends, compare the more recent half of the log against the "
    "earlier half."
)

_HSK_MAP: dict[str, int] = {}
_ERRORS: list[str] = []

FB_CORR = SimpleNamespace(correct_fix=None, misleading=None)
FB_PERS = SimpleNamespace(references_history=None, cites_number=None)


async def safe(coro, fallback):
    """Run a judge/extract coroutine; on failure record it and return a fallback so
    one bad parse can't abort the whole 60-case run."""
    try:
        return await coro
    except Exception as ex:  # noqa: BLE001
        _ERRORS.append(str(ex).splitlines()[0][:140])
        return fallback


# --------------------------------------------------------------------------- #
# Arm runners
# --------------------------------------------------------------------------- #
async def _agent_once(user_id: str, thread_id: str, text: str) -> str:
    graph = build_agent(user_id)
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=text)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return answer_text(result["messages"][-1].content)


async def agent_run(user_id: str, thread_id: str, text: str) -> str:
    """Fresh agent per case (cheap). Retry once if the reasoning model ends on a
    thinking-only message (answer_text -> ""), which would otherwise be scored as a
    failed correction — a harness artifact, not a real quality signal."""
    ans = await _agent_once(user_id, thread_id, text)
    if not ans.strip():
        ans = await _agent_once(user_id, thread_id + "_retry", text)
    return ans.strip() or "(no response)"


async def naked_run(system: str, user_content: str) -> str:
    resp = await get_llm(streaming=False).ainvoke(
        [SystemMessage(content=system), HumanMessage(content=user_content)]
    )
    return answer_text(resp.content)


def seed_user(user_id: str, records: list[dict]):
    """Reset then seed a user's personal-error corpus with dated records."""
    name = f"{memory._safe_ns(user_id)}_personal_errors"
    try:
        memory.get_client().delete_collection(name)
    except Exception:
        pass
    now = datetime.now(timezone.utc)
    for r in records:
        ts = (now - timedelta(days=r["days_ago"])).isoformat()
        memory.add_personal_error(user_id, r["original"], r["correction"], r["category"], r["explanation"], ts)


def records_as_text(records: list[dict]) -> str:
    now = datetime.now(timezone.utc)
    lines = []
    for i, r in enumerate(records):
        d = (now - timedelta(days=r["days_ago"])).date().isoformat()
        lines.append(f"{i+1}. [{d}] category={r['category']}: \"{r['original']}\" -> \"{r['correction']}\"")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Deterministic checks
# --------------------------------------------------------------------------- #
def retrieval_metrics(learner_input: str, expected_rule_id: str, k: int = 3) -> dict:
    hits = memory.query_grammar_rules(learner_input, n=k)
    ids = [h["id"] for h in hits]
    rank = ids.index(expected_rule_id) + 1 if expected_rule_id in ids else 0
    return {"recall_at_k": 1 if rank else 0, "mrr": (1.0 / rank) if rank else 0.0}


def _ref_pinyin(word: str) -> str:
    syl = pinyin(word, style=Style.TONE)
    return "".join(s[0] for s in syl).lower().replace(" ", "")


def grounding_check(claims: J.GroundingClaims) -> dict:
    """Verify extracted pinyin/HSK claims against pypinyin + the HSK map.

    Only scores claims we can verify (word in HSK map, or pinyin computable);
    returns correct/total so an arm that states nothing is neither rewarded nor
    penalised (total=0).
    """
    checked = correct = 0
    words, pys, hsks = claims.words, claims.pinyins, claims.hsk_levels
    for i, w in enumerate(words):
        w = (w or "").strip()
        if not w:
            continue
        py = pys[i] if i < len(pys) else ""
        if py:
            ref = _ref_pinyin(w)
            got = py.lower().replace(" ", "")
            if ref and got:
                checked += 1
                correct += int(ref == got)
        hsk = hsks[i] if i < len(hsks) else 0
        if hsk and w in _HSK_MAP:
            checked += 1
            correct += int(_HSK_MAP[w] == hsk)
    return {"checked": checked, "correct": correct}


# --------------------------------------------------------------------------- #
# Per-case pipelines
# --------------------------------------------------------------------------- #
async def run_type_a(case: dict) -> dict:
    async with SEM:
        uid = "eval_a_" + case["id"]
        seed_user(uid, [])  # empty corpus — stateless
        a_ans, n_ans = await asyncio.gather(
            agent_run(uid, case["id"], case["input"]),
            naked_run(NAKED_TUTOR_SYS, case["input"]),
        )
        a_corr, n_corr, a_gr_c, n_gr_c = await asyncio.gather(
            safe(J.judge_correction(case["input"], case["expected_correction"], a_ans), FB_CORR),
            safe(J.judge_correction(case["input"], case["expected_correction"], n_ans), FB_CORR),
            safe(J.extract_grounding(a_ans), J.GroundingClaims()),
            safe(J.extract_grounding(n_ans), J.GroundingClaims()),
        )
        row = {
            "id": case["id"], "type": "A_stateless", "input": case["input"],
            "agent": {"correct": a_corr.correct_fix, "misleading": getattr(a_corr, "misleading", None), "grounding": grounding_check(a_gr_c), "answer": a_ans},
            "naked": {"correct": n_corr.correct_fix, "misleading": getattr(n_corr, "misleading", None), "grounding": grounding_check(n_gr_c), "answer": n_ans},
        }
        if case.get("expected_rule_id"):
            row["agent"]["retrieval"] = retrieval_metrics(case["input"], case["expected_rule_id"])
        return row


async def run_type_b(case: dict) -> dict:
    async with SEM:
        uid = "eval_b_" + case["id"]
        seed_user(uid, case["seed"])
        history = records_as_text(case["seed"])
        naked_content = (
            f"Here is the learner's past error history:\n{history}\n\n"
            f"Now correct and respond to their new sentence: {case['input']}"
        )
        a_ans, n_ans = await asyncio.gather(
            agent_run(uid, case["id"], case["input"]),
            naked_run(NAKED_TUTOR_SYS, naked_content),
        )
        a_corr, n_corr, a_pers, n_pers = await asyncio.gather(
            safe(J.judge_correction(case["input"], case["expected_correction"], a_ans), FB_CORR),
            safe(J.judge_correction(case["input"], case["expected_correction"], n_ans), FB_CORR),
            safe(J.judge_personalisation(a_ans), FB_PERS),
            safe(J.judge_personalisation(n_ans), FB_PERS),
        )
        return {
            "id": case["id"], "type": "B_small", "category": case["category"], "input": case["input"],
            "agent": {"correct": a_corr.correct_fix, "references_history": a_pers.references_history, "cites_number": a_pers.cites_number, "answer": a_ans},
            "naked": {"correct": n_corr.correct_fix, "references_history": n_pers.references_history, "cites_number": n_pers.cites_number, "answer": n_ans},
        }


async def run_type_c(case: dict, shared_uid: str) -> dict:
    async with SEM:
        history = records_as_text(case["seed"])
        naked_content = f"Here is my complete error log:\n\n{history}\n\nQuestion: {case['input']}"
        a_ans, n_ans = await asyncio.gather(
            agent_run(shared_uid, case["id"], case["input"]),
            naked_run(NAKED_ANALYST_SYS, naked_content),
        )
        # Deterministic parse (no LLM): reliable and reproducible, where LLM extraction
        # was too flaky on emoji markdown tables and collapsed the head-to-head to noise.
        a_ok, a_why = J.score_aggregation(case["ask"], agg_parse.parse(a_ans, case["ask"]), case["truth"])
        n_ok, n_why = J.score_aggregation(case["ask"], agg_parse.parse(n_ans, case["ask"]), case["truth"])
        return {
            "id": case["id"], "type": "C_scale", "ask": case["ask"], "input": case["input"],
            "agent": {"aggregation_correct": a_ok, "detail": a_why, "answer": a_ans},
            "naked": {"aggregation_correct": n_ok, "detail": n_why, "answer": n_ans},
        }


# --------------------------------------------------------------------------- #
# Aggregation + reporting
# --------------------------------------------------------------------------- #
def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def _rate(rows_, arm, key):
    """Pass-rate 'k/n' string over a boolean field, ignoring None (failed judge)."""
    vals = [r[arm][key] for r in rows_ if r[arm].get(key) is not None]
    return f"{sum(bool(v) for v in vals)}/{len(vals)}" if vals else "0/0"


def summarise(rows: list[dict]) -> dict:
    a = [r for r in rows if r["type"] == "A_stateless"]
    b = [r for r in rows if r["type"] == "B_small"]
    c = [r for r in rows if r["type"] == "C_scale"]
    s: dict = {}

    def grounding_rate(rows_, arm):
        tot = sum(r[arm]["grounding"]["checked"] for r in rows_ if "grounding" in r[arm])
        cor = sum(r[arm]["grounding"]["correct"] for r in rows_ if "grounding" in r[arm])
        return (round(cor / tot, 2), cor, tot) if tot else (None, 0, 0)

    if a:
        s["A_stateless"] = {
            "n": len(a),
            "correct_agent": _rate(a, "agent", "correct"),
            "correct_naked": _rate(a, "naked", "correct"),
            "retrieval_recall@3": _mean([r["agent"]["retrieval"]["recall_at_k"] for r in a if "retrieval" in r["agent"]]),
            "retrieval_mrr": _mean([r["agent"]["retrieval"]["mrr"] for r in a if "retrieval" in r["agent"]]),
            "grounding_agent": grounding_rate(a, "agent"),
            "grounding_naked": grounding_rate(a, "naked"),
        }
    if b:
        s["B_small"] = {
            "n": len(b),
            "correct_agent": _rate(b, "agent", "correct"),
            "correct_naked": _rate(b, "naked", "correct"),
            "references_history_agent": _rate(b, "agent", "references_history"),
            "references_history_naked": _rate(b, "naked", "references_history"),
            "cites_number_agent": _rate(b, "agent", "cites_number"),
            "cites_number_naked": _rate(b, "naked", "cites_number"),
        }
    if c:
        s["C_scale"] = {
            "n": len(c),
            "aggregation_agent": f"{sum(r['agent']['aggregation_correct'] for r in c)}/{len(c)}",
            "aggregation_naked": f"{sum(r['naked']['aggregation_correct'] for r in c)}/{len(c)}",
        }
    return s


def render_markdown(summary: dict, rows: list[dict], stamp: str) -> str:
    L = [f"# Eval Results — Agent vs Naked LLM\n", f"Model: **{DEFAULT_MODEL}** · Judge: **{J.JUDGE_MODEL}** · {stamp}\n"]
    if "A_stateless" in summary:
        s = summary["A_stateless"]
        L += [
            f"## A_stateless — Stateless correction (n={s['n']}; parity expected; agent wins grounding)\n",
            "| Metric | Agent | Naked |", "|---|---|---|",
            f"| Correction accuracy (correct fix) | {s['correct_agent']} | {s['correct_naked']} |",
            f"| Retrieval recall@3 | {s['retrieval_recall@3']} | — |",
            f"| Retrieval MRR | {s['retrieval_mrr']} | — |",
            f"| Factual grounding (correct/checked) | {s['grounding_agent'][0]} ({s['grounding_agent'][1]}/{s['grounding_agent'][2]}) | {s['grounding_naked'][0]} ({s['grounding_naked'][1]}/{s['grounding_naked'][2]}) |\n",
        ]
    if "B_small" in summary:
        s = summary["B_small"]
        L += [
            f"## B_small — Memory-informed, small scale (n={s['n']}; fair-baseline sanity check)\n",
            "| Metric | Agent | Naked |", "|---|---|---|",
            f"| Correction accuracy (correct fix) | {s['correct_agent']} | {s['correct_naked']} |",
            f"| References error history | {s['references_history_agent']} | {s['references_history_naked']} |",
            f"| Cites a specific count | {s['cites_number_agent']} | {s['cites_number_naked']} |\n",
        ]
    if "C_scale" in summary:
        s = summary["C_scale"]
        L += [
            "## C_scale — At-scale aggregation (the decisive metric)\n",
            "| Metric | Agent | Naked |", "|---|---|---|",
            f"| Aggregation accuracy | {s['aggregation_agent']} | {s['aggregation_naked']} |\n",
            "### Per-question (C_scale)\n",
            "| Case | Question | Agent | Naked |", "|---|---|---|---|",
        ]
        for r in [r for r in rows if r["type"] == "C_scale"]:
            L.append(f"| {r['id']} | {r['ask']} | {'✅' if r['agent']['aggregation_correct'] else '❌'} | {'✅' if r['naked']['aggregation_correct'] else '❌'} |")
        L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="cap cases per type (cheap smoke run)")
    ap.add_argument("--types", default="ABC", help="which types to run by first letter, e.g. 'C' (A=stateless, B=small, C=scale)")
    args = ap.parse_args()

    print(f"Loading reference data into eval ChromaDB ({memory.embedding_name()} embeddings)...")
    memory.load_reference_data()
    global _HSK_MAP
    _HSK_MAP = {v["word"]: v["hsk_level"] for v in json.loads((_env.APP_DATA / "hsk_vocab.json").read_text())}

    data = json.loads(DATASET.read_text())
    lim = args.limit

    tasks = []
    if "A" in args.types:
        tasks += [run_type_a(c) for c in data["A_stateless"][:lim]]
    if "B" in args.types:
        tasks += [run_type_b(c) for c in data["B_small"][:lim]]
    if "C" in args.types:
        c_cases = data["C_scale"][:lim]
        if c_cases:
            shared = "eval_c_shared"
            seed_user(shared, c_cases[0]["seed"])  # identical corpus across C cases
            tasks += [run_type_c(c, shared) for c in c_cases]

    print(f"Running {len(tasks)} case-pipelines (concurrency {SEM._value})...")
    rows = await asyncio.gather(*tasks)
    rows.sort(key=lambda r: r["id"])

    summary = summarise(rows)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tag = "_partial" if lim else ""
    (RESULTS_DIR / f"head_to_head{tag}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2)
    )
    md = render_markdown(summary, rows, stamp)
    (RESULTS_DIR / f"head_to_head{tag}.md").write_text(md)

    print("\n" + md)
    if _ERRORS:
        print(f"\n⚠ {len(_ERRORS)} judge/extract call(s) fell back to default:")
        for e in _ERRORS[:5]:
            print(f"   - {e}")
    print(f"\nWrote results to {RESULTS_DIR}/head_to_head{tag}.md and .json")


if __name__ == "__main__":
    asyncio.run(main())
