"""RAG-metric surface — the grammar_rule_fetcher retrieval→grounding chain.

Standard RAGAS metrics (collections API, judged by gpt-4o-mini) over the Type A
cases, evaluating the retriever + a grounded generation in isolation (no agent
tool-selection variance):

  ContextRecall        did retrieval pull context sufficient to answer?
  ContextRelevance     is the retrieved context about THIS learner's error?
  Faithfulness         is the coach's answer grounded in the retrieved rule?
  ResponseGroundedness (RAGGroundedness) — same, response-vs-context direction
  NoiseSensitivity     does the answer pick up unsupported claims from noise?
  AnswerAccuracy       is the answer correct vs the reference correction?

Reported ALONGSIDE a deterministic recall@k / MRR computed by exact rule-id match
(Type A cases carry a ground-truth `expected_rule_id`). The deterministic number
validates RAGAS's LLM-judged ContextRecall — a strength to show, not a duplicate.

  uv run python evals/ragas_rag.py            # all Type A cases
  uv run python evals/ragas_rag.py --limit 8  # cheap review slice
"""
import _env  # noqa: F401  — MUST be first: .env, chroma isolation, ragas vertexai shim

import argparse
import asyncio
import json
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    AnswerAccuracy,
    ContextRelevance,
    Faithfulness,
    LLMContextRecall,
    NoiseSensitivity,
    ResponseGroundedness,
)

import memory
from agent import answer_text
from config import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "evals" / "test_dataset.json"
RESULTS = ROOT / "evals" / "results"
EVALUATOR_MODEL = os.environ.get("RAGAS_EVALUATOR", "gpt-4o-mini")
# Generation model for the grounded answer. Defaults to glm (fast, non-reasoning):
# the RAG surface measures the retriever + grounding, not the model (that is Task 6's
# variable), and the reasoning default (deepseek) intermittently hangs 30+ min on
# OpenRouter, which makes a 40-case run non-reproducible. Override with RAG_GEN_MODEL.
GEN_MODEL = os.environ.get("RAG_GEN_MODEL", "glm")
GEN_TIMEOUT = int(os.environ.get("RAG_GEN_TIMEOUT", "150"))  # seconds per generation
K = 3  # retrieval depth — matches grammar_rule_fetcher in production
SEM = asyncio.Semaphore(int(os.environ.get("EVAL_CONCURRENCY", "4")))

# The grounded-generation step: mirror what the agent does when it calls
# grammar_rule_fetcher — answer the learner USING ONLY the retrieved rules, so the
# RAG chain (retriever→generator) is what the metrics judge, not tool selection.
_RAG_GEN_SYS = (
    "You are a Mandarin coach. A learner wrote an incorrect sentence. Using ONLY the "
    "grammar rules provided as context, (1) give the corrected sentence and (2) briefly "
    "explain the error. Do not invent rules that are not in the context. Be concise."
)


def evaluator_llm():
    # Classic ragas path: LangchainLLMWrapper(ChatOpenAI). Chosen over the newer
    # collections/`llm_factory` path because that one drives structured output through
    # `instructor`, which sends gpt-4o-mini into a degenerate-repetition loop on
    # NoiseSensitivity (IncompleteOutputException even on a 184-char response, at any
    # max_tokens). The LangChain function-calling path is stable AND is the canonical,
    # widely-recognised RAGAS usage. max_tokens capped so a runaway can't burn budget.
    llm = ChatOpenAI(model=EVALUATOR_MODEL, temperature=0, max_tokens=4000,
                     api_key=os.environ["OPENAI_API_KEY"])
    return LangchainLLMWrapper(llm)


async def generate_response(learner_input: str, contexts: list[str]) -> str:
    """The coach's answer, grounded in the retrieved rules. Bounded by GEN_TIMEOUT so a
    hung OpenRouter call degrades one case instead of sinking the whole run."""
    ctx = "\n".join(f"- {c}" for c in contexts) or "(no rule retrieved)"
    llm = get_llm(GEN_MODEL, streaming=False)
    resp = await asyncio.wait_for(
        llm.ainvoke(
            [
                SystemMessage(content=_RAG_GEN_SYS),
                HumanMessage(content=f"Learner sentence: {learner_input}\n\nRetrieved rules:\n{ctx}"),
            ]
        ),
        timeout=GEN_TIMEOUT,
    )
    return answer_text(resp.content) or "(no response)"


async def _safe(metric, sample: SingleTurnSample, label: str):
    """Score one metric on a sample; on any failure return None so one bad case
    never sinks the run. Classic single_turn_ascore returns a float directly."""
    try:
        r = await metric.single_turn_ascore(sample)
        return float(r) if r is not None else None
    except Exception as e:  # noqa: BLE001 — log and continue
        print(f"    ! {label} failed: {type(e).__name__}: {e}")
        return None


async def eval_case(case: dict, metrics: dict) -> dict:
    async with SEM:
        learner = case["input"]
        reference = f"{case['expected_correction']} — {case['reference_explanation']}"

        hits = memory.query_grammar_rules(learner, n=K)
        contexts = [h["document"] for h in hits]
        retrieved_ids = [h["id"] for h in hits]
        try:
            response = await generate_response(learner, contexts)
        except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
            print(f"  {case['id']} generation FAILED: {type(e).__name__} — scored on retrieval only")
            response = None

        # One SingleTurnSample; each RAGAS metric reads the fields it needs. Response-
        # dependent metrics are skipped (left None) when generation failed.
        scores = {}
        if response is not None:
            sample = SingleTurnSample(
                user_input=learner, retrieved_contexts=contexts,
                response=response, reference=reference,
            )
            if contexts:  # context-dependent metrics need a non-empty retrieval
                for name in ("ContextRecall", "ContextRelevance", "Faithfulness",
                             "ResponseGroundedness", "NoiseSensitivity"):
                    scores[name] = await _safe(metrics[name], sample, f"{case['id']} {name}")
            scores["AnswerAccuracy"] = await _safe(metrics["AnswerAccuracy"], sample, f"{case['id']} AnswerAccuracy")

        # Deterministic retrieval cross-check — only cases with a ground-truth rule id.
        expected = case.get("expected_rule_id")
        recall_at_k = mrr = None
        if expected:
            hit = expected in retrieved_ids
            recall_at_k = 1.0 if hit else 0.0
            mrr = 1.0 / (retrieved_ids.index(expected) + 1) if hit else 0.0

        print(f"  {case['id']} {case['category']:12} "
              f"recall@{K}={recall_at_k} " + " ".join(
                  f"{k[:4]}={v:.2f}" if v is not None else f"{k[:4]}=—" for k, v in scores.items()))
        return {
            "id": case["id"], "category": case["category"], "input": learner,
            "expected_rule_id": expected, "retrieved_ids": retrieved_ids,
            "response": response, "ragas": scores,
            "recall_at_k": recall_at_k, "mrr": mrr,
        }


def _mean(vals):
    xs = [v for v in vals if v is not None]
    return sum(xs) / len(xs) if xs else None


def summarise(rows: list[dict]) -> dict:
    metric_names = ["ContextRecall", "ContextRelevance", "Faithfulness",
                    "ResponseGroundedness", "NoiseSensitivity", "AnswerAccuracy"]
    ragas_means = {m: _mean([r["ragas"].get(m) for r in rows]) for m in metric_names}
    with_id = [r for r in rows if r["expected_rule_id"]]
    n_gen_failed = sum(1 for r in rows if r["response"] is None)
    return {
        "n_cases": len(rows),
        "n_with_rule_id": len(with_id),
        "n_generation_failed": n_gen_failed,
        "ragas_means": ragas_means,
        "deterministic": {
            f"recall_at_{K}": _mean([r["recall_at_k"] for r in with_id]),
            "mrr": _mean([r["mrr"] for r in with_id]),
        },
    }


def render_md(summary: dict) -> str:
    rm = summary["ragas_means"]
    def fmt(v): return f"{v:.3f}" if v is not None else "—"
    lines = [
        "# RAG-metric surface — grammar_rule_fetcher",
        f"\nEvaluator: **{EVALUATOR_MODEL}** · generation: **{GEN_MODEL}** · retrieval depth k={K} · "
        f"{summary['n_cases']} Type A cases ({summary['n_with_rule_id']} with a ground-truth rule id"
        + (f"; {summary['n_generation_failed']} generation timeouts, scored on retrieval only"
           if summary.get('n_generation_failed') else "") + ").\n",
        "## RAGAS metrics (0–1, higher is better)",
        "| Metric | Mean | Measures |",
        "|---|---|---|",
        f"| ContextRecall | {fmt(rm['ContextRecall'])} | retrieval pulled context sufficient to answer |",
        f"| ContextRelevance | {fmt(rm['ContextRelevance'])} | retrieved rule is about this error |",
        f"| Faithfulness | {fmt(rm['Faithfulness'])} | answer grounded in retrieved rule |",
        f"| ResponseGroundedness | {fmt(rm['ResponseGroundedness'])} | (RAGGroundedness) response vs context |",
        f"| NoiseSensitivity | {fmt(rm['NoiseSensitivity'])} | picks up unsupported claims (lower=better) |",
        f"| AnswerAccuracy | {fmt(rm['AnswerAccuracy'])} | answer correct vs the reference (graded 0/0.5/1) |",
        "\n> **AnswerAccuracy is reference-anchored**: gpt-4o-mini rates the answer against the "
        "one canonical correction on a 0 / 0.5 / 1 scale — more forgiving than exact match, but a "
        "valid *alternative* fix (e.g. rewriting a 把 sentence as a 被 passive) can still be marked "
        "down. Read it alongside the LLM-judge `judge_correction` (accepts any linguistically valid "
        "fix); the gap between them quantifies how often the model picks a valid alternative.",
        "\n## Deterministic cross-check (exact rule-id match)",
        "| Metric | Value |",
        "|---|---|",
        f"| recall@{K} | {fmt(summary['deterministic'][f'recall_at_{K}'])} |",
        f"| MRR | {fmt(summary['deterministic']['mrr'])} |",
        "\n> The deterministic recall validates RAGAS's LLM-judged ContextRecall; "
        "close agreement is the signal that the judged metric is trustworthy.",
    ]
    return "\n".join(lines)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only first N Type A cases")
    args = ap.parse_args()

    data = json.loads(DATASET.read_text())["type_a"]
    if args.limit:
        data = data[: args.limit]

    llm = evaluator_llm()
    metrics = {
        "ContextRecall": LLMContextRecall(llm=llm),
        "ContextRelevance": ContextRelevance(llm=llm),
        "Faithfulness": Faithfulness(llm=llm),
        "ResponseGroundedness": ResponseGroundedness(llm=llm),
        "NoiseSensitivity": NoiseSensitivity(llm=llm),
        "AnswerAccuracy": AnswerAccuracy(llm=llm),
    }
    print(f"RAG surface: {len(data)} cases, evaluator={EVALUATOR_MODEL}, gen={GEN_MODEL}, k={K}\n")
    # return_exceptions so a single unexpected error can never discard the whole batch;
    # any exception row is dropped (eval_case already handles the expected failure modes).
    raw = await asyncio.gather(*(eval_case(c, metrics) for c in data), return_exceptions=True)
    rows = [r for r in raw if isinstance(r, dict)]
    dropped = len(raw) - len(rows)
    if dropped:
        print(f"! {dropped} case(s) raised an unexpected error and were dropped")
    summary = summarise(rows)

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "ragas_rag.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    md = render_md(summary)
    (RESULTS / "ragas_rag.md").write_text(md)
    print("\n" + md)
    print(f"\nWrote {RESULTS/'ragas_rag.md'} and .json")


if __name__ == "__main__":
    asyncio.run(main())
