# evals/

All evaluation code and data for **Task 5** (evaluation harness) and **Task 6**
(retrieval + model bake-off). The Task 5 write-up with results and conclusions lives in
the root [`README.md`](../README.md#results--what-was-actually-built-and-what-it-showed);
this file is the **map of the folder** — what each file is and how the pieces fit together.

## The folder, at a glance

```
evals/
  lib/        shared modules, imported not run   (_env.py, llm_judge.py, agg_parse.py)
  datagen/    dataset builders + frozen data     (seed_data.py, generate_*.py, *.json)
  surfaces/   the 5 runnable evaluations         (preflight_typec, eval_harness, ragas_*, extraction_eval)
  results/    every surface's output + its own README (verification recipes)
```

## The pipeline, in order

Data flows in one direction: shared bootstrap → build the frozen datasets → run the
surfaces → read the results. Every runnable script starts by putting `evals/` on the path
and importing `lib._env` (the bootstrap), and the surfaces read the datasets the generators
produce.

```
lib/_env.py ─┐  (bootstrap: .env, isolated ChromaDB, app/ on path, RAGAS shim, path constants)
             │
datagen/seed_data.py ──▶ datagen/generate_dataset.py ──────▶ datagen/test_dataset.json ─────┐
                         datagen/generate_extraction_dataset.py ─▶ datagen/extraction_dataset.json ─┐
                                                                                │                    │
   ┌────────────────────────────────────────────────────────────────────────  ┘                    │
   ▼                                                                                                 ▼
surfaces/preflight_typec   surfaces/eval_harness   surfaces/ragas_rag   surfaces/ragas_agentic   surfaces/extraction_eval
(thesis check)             (head-to-head)          (RAG metrics)        (agentic metrics)        (corpus-writer)
   │                            │                       │                    │                        │
   └────────────────────────────┴──────────── results/ ────────────────────┴────────────────────────┘
        (each surface writes a .md summary + a .json with every raw answer)
```

## Files by role

### `lib/` — shared foundations (imported by the scripts, not run directly)

| File | What it is |
|---|---|
| `_env.py` | Bootstrap **and** the single source of truth for eval paths: loads `.env`, isolates ChromaDB to `.eval_chroma/`, puts `app/` on the path, applies the RAGAS shim, and exports `EVALS` / `DATAGEN` / `RESULTS` / `APP_DATA` so no script recomputes paths. Imported first by every script. |
| `llm_judge.py` | The LLM-as-judge scorers (boolean correction / personalisation) + extract-then-check scorers (aggregation, grounding), all at temp 0 with an independent judge model. |
| `agg_parse.py` | Deterministic parser for C_scale aggregation answers — the correctness authority the aggregation judge is checked against. |

### `datagen/` — dataset builders and the frozen data they produce

| File | What it is |
|---|---|
| `seed_data.py` | Per-category error examples + the deterministic C_scale corpus builder (60 records with a designed, non-trivial trend). |
| `generate_dataset.py` | Builds `test_dataset.json` — A_stateless **derived from the reference corpus** (ground-truth corrections + retrieval targets by construction); B_small/C_scale from `seed_data`. |
| `test_dataset.json` | The 60 head-to-head cases: 40 A_stateless (stateless), 10 B_small (small-scale memory), 10 C_scale (at-scale aggregation). |
| `generate_extraction_dataset.py` | Builds `extraction_dataset.json`: 34 positives (labels from `test_dataset.json`, coach replies reused from `results/head_to_head.json`; 6 corpus inputs with English meaning-annotations excluded as invalid) + 17 negatives (correct-sentence/question with generated realistic replies, non-Chinese guard cases). |
| `extraction_dataset.json` | Frozen ground truth for the extraction surface. |

### `surfaces/` — the runnable evaluations (each writes into `results/`)

| File | What it measures | Writes |
|---|---|---|
| `preflight_typec.py` | The load-bearing thesis check: can the agent aggregate at scale at all? Run this first — if it fails, nothing else matters. | `results/preflight_typec.md` |
| `eval_harness.py` | Head-to-head: every case through the full agent **and** a naked-LLM control arm. | `results/head_to_head.{md,json}` |
| `ragas_rag.py` | RAGAS RAG metrics (ContextRecall/Relevance, Faithfulness, ResponseGroundedness, NoiseSensitivity, AnswerAccuracy) over the retriever→grounding chain; judge = gpt-4o-mini. | `results/ragas_rag.{md,json}` |
| `ragas_agentic.py` | RAGAS agentic metrics (ToolCallAccuracy, AgentGoalAccuracy) over the full tool-call trace + deterministic tool-recall and off-topic-deflection cross-checks; reasoning judge = **gpt-4o**. | `results/ragas_agentic.{md,json}` |
| `extraction_eval.py` | The hidden post-turn corpus-writer `extract_and_log_error`: had_error precision/recall/F1, category accuracy, correction validity — each miss split into omission / malformed-JSON / wrong-value. | `results/extraction.{md,json}` |

**Results** — `results/` holds the output of every surface. **Start at
[`results/README.md`](results/README.md)**: it indexes all surfaces and gives copy-paste
recipes to re-derive any headline number and read any case's raw answer.

## How to run

Ordered to match the pipeline above. Datasets are committed, so you only re-run a generator
if you change the seed data.

Run from the repo root (each script puts `evals/` on the path itself, so no `cd` needed).

```bash
# 1. (Re)build the frozen datasets — only needed if seed data changes
uv run python evals/datagen/generate_dataset.py
REQUEST_TIMEOUT=150 uv run python evals/datagen/generate_extraction_dataset.py   # prereq: results/head_to_head.json

# 2. Run the surfaces
uv run python evals/surfaces/preflight_typec.py                                        # thesis check
uv run python evals/surfaces/eval_harness.py                                           # head-to-head (60)
uv run python evals/surfaces/eval_harness.py --limit 2 --types C                       # cheap partial run
uv run python evals/surfaces/ragas_rag.py                                              # RAG surface (40 A_stateless)
REQUEST_TIMEOUT=150 EVAL_CONCURRENCY=3 uv run python evals/surfaces/ragas_agentic.py   # agentic surface (60)
REQUEST_TIMEOUT=150 EVAL_CONCURRENCY=4 uv run python evals/surfaces/extraction_eval.py # extraction surface (34+17)
uv run python evals/surfaces/extraction_eval.py --from-rows                            # re-aggregate saved rows, no model calls
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
- **Deterministic retrieval metrics.** Because A_stateless cases carry a ground-truth
  `expected_rule_id`, context recall@3 / MRR are computed by exact id match against the
  retriever's output — stronger and cheaper than RAGAS's LLM-approximated relevance, and
  exactly the retriever-level signal Task 6 will vary.
- **RAGAS agentic metrics are paired with deterministic cross-checks, and each was vetted
  for fitness.** `ToolCallAccuracy` is an exact tool-*set* match (0 for any missing/extra
  tool), so it is read beside a deterministic *required-tool recall* (0.992 — the agent
  reliably grounds + checks history) and *extra-tool rate* (it proactively offers drills).
  `AgentGoalAccuracyWithReference` was found unusable (its compare-outcome prompt rates
  identical outcomes "different" even on gpt-4o) so the `WithoutReference` variant is used —
  it measures task *completion*, with `agg_parse` as the correctness authority. The two
  multi-turn reasoning judges use **gpt-4o** (gpt-4o-mini's goal verdict is unstable).
  `TopicAdherenceScore` was too unstable to headline, so adherence is reported as a
  deterministic off-topic-deflection check (raw RAGAS number kept in JSON). Showing a metric
  was assessed and found unfit is deliberate methodology, not an omission.
- **The extraction surface scores the LOGGING predicate and separates omission from error.**
  `extract_and_log_error` runs silently after every turn and writes the learner's corpus, so
  precision/recall are computed on the *effective* `would_log` condition the production code uses
  (`has_chinese AND had_error AND original`) — the thing that actually poisons the corpus — not
  the raw bool. Negatives carry a real generated coach reply (a blank reply would fabricate false
  positives). Every miss is split into OMISSION (a field left empty) vs a genuine wrong value,
  because the headline defect turned out to be the former: perfect precision, but glm's
  structured output is unreliable — it drops `correction`/`category` on a run-variable chunk of
  logged records and intermittently emits malformed JSON (a reliability limit fixable with a
  retry/validation guard, not a model swap — DECISIONS #13).

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
