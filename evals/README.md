# evals/

This directory contains all evaluation code and data (Tasks 5 and 6).

## Files

| File | Purpose | Status |
|---|---|---|
| `_env.py` | Shared bootstrap: loads `.env`, isolates ChromaDB to `.eval_chroma/`, puts `app/` on the path. Imported first by every eval script. | DONE |
| `seed_data.py` | Per-category error examples + the deterministic Type C corpus builder (60 records with a designed, non-trivial trend). | DONE |
| `generate_dataset.py` | Builds `test_dataset.json` — Type A **derived from the reference corpus** (ground-truth corrections + retrieval targets by construction), Type B/C from `seed_data`. | DONE |
| `test_dataset.json` | 60 cases: 40 Type A (stateless), 10 Type B (small-scale memory), 10 Type C (at-scale aggregation). | DONE |
| `llm_judge.py` | Boolean LLM-as-judge (correction, personalisation) + extract-then-check scorers (aggregation, grounding), temp 0, independent judge. | DONE |
| `eval_harness.py` | Runs every case through the agent AND a naked-LLM control arm; writes `results/head_to_head.{md,json}`. | DONE |
| `preflight_typec.py` | The load-bearing thesis check (see `results/preflight_typec.md`). | DONE |
| `results/` | Output tables + audit JSON (every stored answer is inspectable). | DONE |

## How to run

```bash
uv run python evals/generate_dataset.py      # (re)build test_dataset.json
uv run python evals/eval_harness.py          # full 60-case head-to-head
uv run python evals/eval_harness.py --limit 2 --types C   # cheap partial run
```

## Methodology notes (decisions made during the build)

- **Head-to-head by design.** Every case runs through the full agent and a *naked-LLM
  control arm* (same model, best-effort prompt; for memory cases the learner's raw
  records handed straight into context). The claim only counts if it survives this.
- **Boolean / extractive scoring, not 1–5.** Constrained-int score fields (`ge=1,le=5`)
  came back garbled to their minimum on the OpenRouter models, while boolean and named-
  scalar fields are reliable. So metrics are booleans (correct-fix, references-history)
  and exact extract-then-check (aggregation, grounding) — less noisy than a judge score.
- **Independent judge.** Judging uses a non-reasoning model (`glm`) distinct from the
  arms under test (`deepseek`) — faster, and no self-preference. Override with `JUDGE_MODEL`.
- **Deterministic retrieval metrics.** Because Type A cases carry a ground-truth
  `expected_rule_id`, context recall@3 / MRR are computed by exact id match against the
  retriever's output — stronger and cheaper than RAGAS's LLM-approximated relevance, and
  exactly the retriever-level signal Task 6 will vary.

## Retrieval strategies to evaluate (Task 6)

| Strategy | Status |
|---|---|
| Baseline — semantic only (OpenAI text-embedding-3-small) | TODO |
| Qwen3-Embedding-8B (MTEB #1 multilingual) | TODO |
| BGE-M3 (best open-source Chinese embeddings) | TODO |
| Hybrid search — BM25 + semantic | TODO |
| Semantic + Cohere Rerank | TODO |
| Multi-query retrieval | TODO |

## Model comparison (Task 6)

| Model | BenchLM Chinese Score | Eval Score | Status |
|---|---|---|---|
| DeepSeek V3 | 87 | TBD | TODO |
| GLM-5 | 81 | TBD | TODO |
| Qwen3.5-235B | 79 | TBD | TODO |
