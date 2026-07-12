# Mandarin Coach — Progress Status

_Last updated: 2026-07-12. Cert due ~2026-07-16. App is LIVE at https://34-129-227-111.nip.io (GCP VM, Docker, LangGraph, auth, persistent disk)._

This file is the single source of truth for resuming work. See also `progress/DECISIONS.md` for the non-obvious gotchas.

---

## Where we are

Working on **Task 5: Evaluation Harness** (15 pts). Pivoted from bespoke metrics to the **standard RAGAS suite** (user's explicit request). Evaluator judge = **OpenAI gpt-4o-mini**. Models under test = deepseek (default) / glm / qwen via OpenRouter.

Three eval surfaces planned; **1 of 3 built**.

---

## DONE

### App
- **Production timeout + fallback guard** (`app/config.py`, `app/agent.py`, `app/main.py`).
  - `get_llm(..., timeout=90s)` → `request_timeout` on ChatLiteLLM.
  - `run_agent` wraps each turn in `asyncio.wait_for(AGENT_TURN_TIMEOUT=180s)`; on timeout/any error falls back to `glm`; both-down → friendly message.
  - `build_agent` now returns `CoachAgent(primary, fallback)` (each own MemorySaver). Verified with 6 unit checks + 1 live turn.
- **LangSmith project routing**: app traces → `mandarin-coach`; eval traces → `mandarin-coach-evals` (was all `default`).

### Evals — Generation 1 (custom metrics, pre-RAGAS)
- `evals/preflight_typec.py` → `results/preflight_typec.md` — thesis preflight (can agent aggregate at scale).
- `evals/eval_harness.py` + `llm_judge.py` + `agg_parse.py` + `seed_data.py` + `generate_dataset.py` → `results/head_to_head.{md,json}`.
  - Agent vs naked-LLM head-to-head, all 3 case types. Type A correct-fix 36/37 vs 32/39; retrieval recall@3/MRR = 1.0; Type C aggregation 10/10 vs 7/10 (⚠️ **run-unstable** — a re-run gave 6/6; honest story = agent is exact oracle, naked is noisy).

### Evals — Generation 2 (RAGAS rebuild) — **RAG surface only**
- `evals/_env.py` — bootstrap: `.env`, chroma isolation, **RAGAS vertexai import shim**, eval trace project.
- `evals/ragas_rag.py` → `results/ragas_rag.{md,json}` — 6 standard RAGAS metrics over `grammar_rule_fetcher`, 40 Type A cases, judge=gpt-4o-mini, generation=glm.
  - ContextRecall 0.90 · ContextRelevance 0.84 · Faithfulness 0.84 · ResponseGroundedness 0.98 · NoiseSensitivity 0.23 · AnswerAccuracy 0.83 · deterministic recall@3/MRR = 1.0.

---

## TODO (in priority order)

1. **RAGAS agentic-metric surface** (task #8) — NOT built.
   - Prereq: capture the agent's **tool-call message trace** (currently `run_agent` returns only final text). Need the LangGraph message list → build `ragas.messages` MultiTurnSample.
   - Metrics: **ToolCallAccuracy** (ref tool sequence per case), **AgentGoalAccuracyWithReference**, **TopicAdherence**.
   - Use classic `ragas.metrics` path (see DECISIONS) with the same gpt-4o-mini wrapper.
2. **Structured-extraction surface** — NOT built.
   - Eval `extract_and_log_error` (`app/agent.py`): `had_error` precision/recall, category-classification accuracy, correction validity. This is the "hidden" surface that poisons the corpus if wrong.
3. **Task 6** (Advanced Retrieval, separate task) — NOT built.
   - Retrieval sweep: baseline OpenAI embed vs Qwen3-Embedding-8B vs BGE-M3 vs hybrid BM25+semantic vs +rerank. Metric: ContextRecall@3/@6 + deterministic recall + latency.
   - Model bake-off: deepseek/glm/qwen with quality + **latency + timeout-rate** columns → this is where the **keep/drop-deepseek** decision gets made (see DECISIONS).
4. **README Task 5 write-up** + Loom video + Task 7. Deferred UX: mode chat profiles, model selection in UI.

---

## How to run

```bash
uv run python evals/ragas_rag.py            # RAG surface, all 40 Type A cases
uv run python evals/ragas_rag.py --limit 4  # cheap slice
uv run python evals/eval_harness.py         # Gen-1 head-to-head
uv run python evals/generate_dataset.py     # rebuild test_dataset.json
```
Env knobs: `REQUEST_TIMEOUT`, `AGENT_TURN_TIMEOUT`, `RAG_GEN_MODEL`, `RAGAS_EVALUATOR`, `JUDGE_MODEL`, `EVAL_CONCURRENCY`, `LANGSMITH_PROJECT`.
