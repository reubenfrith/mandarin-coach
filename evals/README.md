# evals/

This directory contains all evaluation code and data (Tasks 5 and 6).

## Files to build

| File | Purpose | Status |
|---|---|---|
| `test_dataset.json` | 50 input/output pairs — Mandarin sentences with known errors, correct versions, error categories, expected explanations. Generated synthetically using Claude. | TODO |
| `generate_dataset.py` | Script to generate synthetic test data using Claude — produces sentences with specific known error types | TODO |
| `eval_harness.py` | Main evaluation runner — sends each test case through the app, collects outputs, scores with RAGAS + LLM-as-judge | TODO |
| `llm_judge.py` | LLM-as-judge scorer — given (input, correction, explanation), scores correction accuracy and explanation quality 1–5 | TODO |
| `results/` | Directory for eval output tables — baseline vs advanced retrieval comparison | TODO |

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
