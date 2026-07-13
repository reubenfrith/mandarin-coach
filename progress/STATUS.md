# Mandarin Coach — Progress Status

_Last updated: 2026-07-12. Cert due ~2026-07-16. App is LIVE at https://34-129-227-111.nip.io (GCP VM, Docker, LangGraph, auth, persistent disk)._

This file is the single source of truth for resuming work. See also `progress/DECISIONS.md` for the non-obvious gotchas and `progress/CHANGELOG.md` for the per-session record of what changed and why.

---

## Where we are

Working on **Task 5: Evaluation Harness** (15 pts). Pivoted from bespoke metrics to the **standard RAGAS suite** (user's explicit request). Evaluator judge = **OpenAI gpt-4o-mini**. Models under test = deepseek (default) / glm / qwen via OpenRouter.

Three eval surfaces planned; **3 of 3 built** (RAG ✓, agentic ✓, structured-extraction ✓).

---

## DONE

### App
- **Production timeout + fallback guard** (`app/config.py`, `app/agent.py`, `app/main.py`).
  - `get_llm(..., timeout=90s)` → `request_timeout` on ChatLiteLLM.
  - `run_agent` wraps each turn in `asyncio.wait_for(AGENT_TURN_TIMEOUT=180s)`; on timeout/any error falls back to `glm`; both-down → friendly message.
  - `build_agent` now returns `CoachAgent(primary, fallback)` (each own MemorySaver). Verified with 6 unit checks + 1 live turn.
- **LangSmith project routing**: app traces → `mandarin-coach`; eval traces → `mandarin-coach-evals` (was all `default`).

### Evals — Generation 1 (custom metrics, pre-RAGAS)
- `evals/surfaces/preflight_typec.py` → `results/preflight_typec.md` — thesis preflight (can agent aggregate at scale).
- `evals/surfaces/eval_harness.py` + `llm_judge.py` + `agg_parse.py` + `seed_data.py` + `generate_dataset.py` → `results/head_to_head.{md,json}`.
  - Agent vs naked-LLM head-to-head, all 3 case types. A_stateless correct-fix 36/37 vs 32/39; retrieval recall@3/MRR = 1.0; C_scale aggregation 10/10 vs 7/10 (⚠️ **run-unstable** — a re-run gave 6/6; honest story = agent is exact oracle, naked is noisy).

### Evals — Generation 2 (RAGAS rebuild) — **RAG + agentic surfaces**
- `evals/lib/_env.py` — bootstrap: `.env`, chroma isolation, **RAGAS vertexai import shim**, eval trace project.
- `evals/surfaces/ragas_rag.py` → `results/ragas_rag.{md,json}` — 6 standard RAGAS metrics over `grammar_rule_fetcher`, 40 A_stateless cases, judge=gpt-4o-mini, generation=glm.
  - ContextRecall 0.90 · ContextRelevance 0.84 · Faithfulness 0.84 · ResponseGroundedness 0.98 · NoiseSensitivity 0.23 · AnswerAccuracy 0.83 · deterministic recall@3/MRR = 1.0.
- `app/agent.py::invoke_with_trace` — eval-only single-graph invoke returning the raw LangGraph message list (app never imports ragas; conversion is eval-side).
- `evals/surfaces/ragas_agentic.py` → `results/ragas_agentic.{md,json}` — 3 standard RAGAS agentic metrics over the full tool-call trace, all 60 cases, agent-under-test=glm, **reasoning judge=gpt-4o** (see below).
  - ToolCallAccuracy A 0.55 / B 0.10 / C 1.00 (exact-set match — low because agent adds sanctioned drills). Deterministic **required-tool recall 0.992** (only dip: B03 tones case → dictionary_lookup instead of grammar_rule_fetcher, linguistically correct). AGA (completion) 0.80. C_scale completion 0.80 vs deterministic correctness 1.00 (0.80 = judge noise, no real gap). **Topic adherence weak** — agent fulfils off-domain requests (recipe, sports) with a Mandarin twist; only ~2/4 probes declined (focused gpt-4o judge; a guardrail gap worth flagging).
- `app/agent.py::extract_error_record` — eval-only, side-effect-free sibling of `extract_and_log_error` (no memory write, guard applied eval-side, model overridable). App never changes behaviour.
- `evals/datagen/generate_extraction_dataset.py` → `evals/datagen/extraction_dataset.json` — 34 positives (coach replies reused from head_to_head; 6 annotated corpus inputs excluded as invalid) + 17 negatives (correct-sentence + question with freshly generated realistic replies, non-Chinese guard cases).
- `evals/surfaces/extraction_eval.py` → `results/extraction.{md,json}` — the hidden post-turn corpus-writer surface (34 clean positives + 17 negatives). had_error **precision 1.00 / recall ~0.95 / F1 ~0.98** (0 false positives — the guardrail against corpus poisoning is perfect). **Headline defect: glm structured-output is UNRELIABLE (not incapable)** — run-variable field omission (drops `correction`+`category`+`explanation` together on ~12–18/33 logged records) + intermittent malformed JSON (`null` string fields → parse error → production fail-safe = silent no-log). Proven flakiness: same inputs return complete records on retry, correction is present in the coach reply, ~0.95 valid when non-empty, reproduces on both structured-output methods. **Fix = retry/validation guard around the extraction call, NOT a model swap.** Feeds DECISIONS #13 + Task 6.

---

## TODO (in priority order)

1. **RAGAS agentic-metric surface** (task #8) — ✅ BUILT (`evals/surfaces/ragas_agentic.py`). See DECISIONS #9–#12 for the metric gotchas that shaped it. ⚠️ **Deviates from the gpt-4o-mini judge**: the two multi-turn reasoning judges use **gpt-4o** (gpt-4o-mini's goal verdict coin-flips) — flag to user.
2. **Structured-extraction surface** — ✅ BUILT (`evals/surfaces/extraction_eval.py` + `generate_extraction_dataset.py`). See DECISIONS #13. Headline finding: perfect precision, but glm's structured output is unreliable (run-variable field-drop + null-JSON) — needs a retry/validation guard around the extraction call; carry into Task 6.
3. **Task 6** (Advanced Retrieval, separate task) — NOT built.
   - Retrieval sweep: baseline OpenAI embed vs Qwen3-Embedding-8B vs BGE-M3 vs hybrid BM25+semantic vs +rerank. Metric: ContextRecall@3/@6 + deterministic recall + latency.
   - Model bake-off: deepseek/glm/qwen with quality + **latency + timeout-rate** columns → this is where the **keep/drop-deepseek** decision gets made (see DECISIONS).
4. **README Task 5 write-up** + Loom video + Task 7. Deferred UX: mode chat profiles, model selection in UI.

---

## How to run

```bash
uv run python evals/surfaces/ragas_rag.py            # RAG surface, all 40 A_stateless cases
uv run python evals/surfaces/ragas_rag.py --limit 4  # cheap slice
REQUEST_TIMEOUT=150 EVAL_CONCURRENCY=3 uv run python evals/surfaces/ragas_agentic.py           # agentic surface, all 60
uv run python evals/surfaces/ragas_agentic.py --types A --limit 3 --no-topic  # cheap agentic slice
REQUEST_TIMEOUT=150 uv run python evals/datagen/generate_extraction_dataset.py  # rebuild extraction_dataset.json (prereq: head_to_head.json)
REQUEST_TIMEOUT=150 EVAL_CONCURRENCY=4 uv run python evals/surfaces/extraction_eval.py           # structured-extraction surface (40+17)
uv run python evals/surfaces/extraction_eval.py --from-rows   # recompute summary/md from saved rows, no model calls
uv run python evals/surfaces/eval_harness.py         # Gen-1 head-to-head
uv run python evals/datagen/generate_dataset.py     # rebuild test_dataset.json
```
Env knobs: `REQUEST_TIMEOUT`, `AGENT_TURN_TIMEOUT`, `RAG_GEN_MODEL`, `RAGAS_EVALUATOR`, `RAGAS_AGENTIC_EVALUATOR` (agentic reasoning judge, default gpt-4o), `AGENT_MODEL` (agent-under-test, default glm), `EXTRACT_MODEL` (extraction under test, default glm), `AGA_SAMPLES`, `JUDGE_MODEL`, `EVAL_CONCURRENCY`, `LANGSMITH_PROJECT`.
