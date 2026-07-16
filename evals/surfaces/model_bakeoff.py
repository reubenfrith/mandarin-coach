"""Task 6.4 — model bake-off: DeepSeek V4 / GLM-5.2 / Qwen3.5 head to head.

Settles the keep/drop-DeepSeek decision deferred from Task 5 by adding the two columns
that decision needs and Task 5 never had: **latency** and **timeout-rate**. Isolates the
model under test: every case retrieves the SAME grammar rules (model-independent), then
each model generates a grounded correction from that identical context — so the only
variable is the model. (Running the full agent instead would confound the result: the
`drill_generator` tool internally calls the DEFAULT model, so deepseek's latency/hangs
would leak into every model's numbers.) DeepSeek's OpenRouter hangs (DECISIONS #4) happen
at the LLM-call level, so a direct call still captures them. Scores:

  correct_fix   reused head-to-head judge (any linguistically valid fix)  [quality]
  misleading    judge flags a materially wrong grammar claim              [quality]
  timeout_rate  turns that breached BAKEOFF_TIMEOUT (the DeepSeek hang)   [reliability]
  error_rate    turns that raised (provider error)                        [reliability]
  latency       per COMPLETED turn: mean / p50 / p95 (ms)                 [speed]

Each turn is bounded by asyncio.wait_for(BAKEOFF_TIMEOUT) so a hung model is COUNTED as
a timeout instead of stranding the run — the hang is the measurement, not a crash. The
judge (JUDGE_MODEL, default glm) is fixed across all three models, so it cannot bias the
comparison between them.

Run:
  REQUEST_TIMEOUT=150 uv run python evals/surfaces/model_bakeoff.py                 # all 3, default cases
  uv run python evals/surfaces/model_bakeoff.py --models glm,qwen --limit 8
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

import memory  # noqa: E402
from agent import answer_text  # noqa: E402
from config import get_llm  # noqa: E402
from lib.llm_judge import judge_correction  # noqa: E402

DATASET = _env.DATAGEN / "test_dataset.json"
RESULTS = _env.RESULTS
MODELS = [m.strip() for m in os.environ.get("BAKEOFF_MODELS", "deepseek,glm,qwen").split(",")]
BAKEOFF_TIMEOUT = float(os.environ.get("BAKEOFF_TIMEOUT", "120"))  # a hung turn past this = timeout
SEM = asyncio.Semaphore(int(os.environ.get("EVAL_CONCURRENCY", "3")))
K = 3  # retrieval depth, matches grammar_rule_fetcher

# Same grounded-correction instruction the RAG surface uses — the coach's core task,
# isolated from tool orchestration so the ONLY variable is the model.
_GEN_SYS = (
    "You are a Mandarin coach. A learner wrote an incorrect sentence. Using the grammar "
    "rules provided as context, (1) give the corrected sentence and (2) briefly explain "
    "the error in English. Be concise."
)


async def run_turn(model: str, learner_input: str, contexts: list[str]):
    """One bounded grounded-correction call on `model`. Returns (answer|None, ms, status)."""
    ctx = "\n".join(f"- {c}" for c in contexts) or "(no rule retrieved)"
    llm = get_llm(model, streaming=False)
    t0 = time.perf_counter()
    try:
        resp = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=_GEN_SYS),
                HumanMessage(content=f"Learner sentence: {learner_input}\n\nRetrieved rules:\n{ctx}"),
            ]),
            timeout=BAKEOFF_TIMEOUT,
        )
        dt = (time.perf_counter() - t0) * 1000
        return answer_text(resp.content) or "(no response)", dt, "ok"
    except asyncio.TimeoutError:
        return None, (time.perf_counter() - t0) * 1000, "timeout"
    except Exception as e:  # noqa: BLE001 — any provider error is a reliability data point
        print(f"    ! error: {type(e).__name__}: {e}")
        return None, (time.perf_counter() - t0) * 1000, "error"


async def eval_case(model: str, case: dict) -> dict:
    async with SEM:
        learner = case["input"]
        reference = f"{case['expected_correction']} — {case.get('reference_explanation', '')}"
        contexts = [h["document"] for h in memory.query_grammar_rules(learner, n=K)]
        answer, latency_ms, status = await run_turn(model, learner, contexts)

        verdict = None
        if answer is not None:
            try:
                v = await judge_correction(learner, reference, answer)
                verdict = {"correct_fix": v.correct_fix, "misleading": v.misleading,
                           "identifies_error": v.identifies_error}
            except Exception as e:  # noqa: BLE001 — judge failure ≠ model failure; leave unscored
                print(f"    ! {case['id']} judge failed: {type(e).__name__}")
        print(f"  [{model}] {case['id']} {status:7} {round(latency_ms)}ms "
              f"fix={verdict['correct_fix'] if verdict else '—'}")
        return {"id": case["id"], "status": status, "latency_ms": round(latency_ms, 1),
                "answer": answer, "verdict": verdict}


def summarise(model: str, rows: list[dict]) -> dict:
    n = len(rows)
    ok = [r for r in rows if r["status"] == "ok"]
    judged = [r for r in ok if r["verdict"]]
    lat = sorted(r["latency_ms"] for r in ok)
    def rate(pred, pool): return round(sum(1 for r in pool if pred(r)) / len(pool), 3) if pool else None
    return {
        "model": model, "n": n,
        "completed": len(ok), "timeouts": sum(1 for r in rows if r["status"] == "timeout"),
        "errors": sum(1 for r in rows if r["status"] == "error"),
        "timeout_rate": round(sum(1 for r in rows if r["status"] == "timeout") / n, 3),
        "correct_fix_rate": rate(lambda r: r["verdict"]["correct_fix"], judged),
        "misleading_count": sum(1 for r in judged if r["verdict"]["misleading"]),
        "n_judged": len(judged),
        "latency_ms": {
            "mean": round(sum(lat) / len(lat), 1) if lat else None,
            "p50": lat[len(lat) // 2] if lat else None,
            "p95": lat[min(int(len(lat) * 0.95), len(lat) - 1)] if lat else None,
        },
    }


def render_md(summaries: list[dict], n_cases: int) -> str:
    def f(v): return "—" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
    lines = [
        "# Task 6.4 — Model bake-off",
        f"\n{n_cases} A_stateless correction cases per model, grounded-correction generation "
        f"(same retrieved rules for every model). Per-turn timeout {int(BAKEOFF_TIMEOUT)}s; "
        f"judge = {os.environ.get('JUDGE_MODEL','glm')} (fixed across models). Latency per COMPLETED turn.\n",
        "| Model | correct_fix | misleading | timeout_rate | errors | latency p50 (ms) | latency p95 (ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lat = s["latency_ms"]
        lines.append(
            f"| {s['model']} | {f(s['correct_fix_rate'])} ({s['n_judged']}) | {s['misleading_count']} "
            f"| {f(s['timeout_rate'])} ({s['timeouts']}/{s['n']}) | {s['errors']} "
            f"| {f(lat['p50'])} | {f(lat['p95'])} |"
        )
    lines.append(
        "\n> **timeout_rate** is the column Task 5 could not provide: turns that breached the "
        f"{int(BAKEOFF_TIMEOUT)}s bound — the operational cost of DeepSeek's OpenRouter hangs "
        "(DECISIONS #4), measured rather than asserted. **correct_fix** count in parens = turns a "
        "verdict was obtained on (timed-out/errored turns produce no answer to judge)."
    )
    return "\n".join(lines)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--limit", type=int, default=12, help="A_stateless cases per model")
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    memory.load_reference_data()  # ensure the eval chroma corpus is present for the tools
    cases = json.loads(DATASET.read_text())["A_stateless"][: args.limit]
    print(f"Bake-off: {len(models)} models × {len(cases)} cases, timeout={int(BAKEOFF_TIMEOUT)}s\n")

    all_rows, summaries = {}, []
    for model in models:
        print(f"--- {model} ---")
        rows = await asyncio.gather(*(eval_case(model, c) for c in cases))
        all_rows[model] = rows
        summaries.append(summarise(model, rows))

    RESULTS.mkdir(exist_ok=True)
    out = {"timeout_s": BAKEOFF_TIMEOUT, "n_cases": len(cases),
           "summaries": summaries, "detail": all_rows}
    (RESULTS / "model_bakeoff.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    md = render_md(summaries, len(cases))
    (RESULTS / "model_bakeoff.md").write_text(md + "\n")
    print("\n" + md)
    print(f"\nWrote {RESULTS/'model_bakeoff.md'} and .json")


if __name__ == "__main__":
    asyncio.run(main())
