# RAG-metric surface — grammar_rule_fetcher

Evaluator: **gpt-4o-mini** · generation: **glm** · retrieval depth k=3 · 40 A_stateless cases (24 with a ground-truth rule id).

## RAGAS metrics (0–1, higher is better)
| Metric | Mean | Measures |
|---|---|---|
| ContextRecall | 0.929 | retrieval pulled context sufficient to answer |
| ContextRelevance | 0.887 | retrieved rule is about this error |
| Faithfulness | 0.834 | answer grounded in retrieved rule |
| ResponseGroundedness | 0.975 | (RAGGroundedness) response vs context |
| NoiseSensitivity | 0.200 | picks up unsupported claims (lower=better) |
| AnswerAccuracy | 0.825 | answer correct vs the reference (graded 0/0.5/1) |

> **AnswerAccuracy is reference-anchored**: gpt-4o-mini rates the answer against the one canonical correction on a 0 / 0.5 / 1 scale — more forgiving than exact match, but a valid *alternative* fix (e.g. rewriting a 把 sentence as a 被 passive) can still be marked down. Read it alongside the LLM-judge `judge_correction` (accepts any linguistically valid fix); the gap between them quantifies how often the model picks a valid alternative.

## Deterministic cross-check (exact rule-id match)
| Metric | Value |
|---|---|
| recall@3 | 1.000 |
| MRR | 0.951 |

> The deterministic recall validates RAGAS's LLM-judged ContextRecall; close agreement is the signal that the judged metric is trustworthy.