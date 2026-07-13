# Mandarin Coach — Progress Status

_Last updated: 2026-07-13. Cert due ~2026-07-16. App is LIVE at https://34-129-227-111.nip.io (GCP VM, Docker, LangGraph, auth, persistent disk)._

This file is the single source of truth for resuming work. See also `progress/DECISIONS.md` for the non-obvious gotchas and `progress/CHANGELOG.md` for the per-session record of what changed and why.

---

## Where we are

**Task 5: Evaluation Harness (15 pts) — CODE COMPLETE + WRITTEN UP + committed/pushed to `main` (commit `cdb588e`).** Pivoted from bespoke metrics to the **standard RAGAS suite** (user's explicit request). Evaluator judge = **OpenAI gpt-4o-mini**; the two agentic reasoning judges use **gpt-4o** (deviation kept — user confirmed). Models under test = deepseek (default, hangs) / glm (reproducible) / qwen via OpenRouter.

**3 of 3 eval surfaces built** (RAG ✓, agentic ✓, structured-extraction ✓), plus:
- Root `README.md` Task 5 **results write-up** done (four-surface story + every conclusion's why).
- `evals/` **restructured** into `lib/` (shared), `datagen/` (builders + data), `surfaces/` (5 runnable evals), `results/`; paths centralized in `lib/_env.py`.
- Case types **renamed** A/B/C → `A_stateless` / `B_small` / `C_scale` everywhere (IDs like `A01` and `--types` letters kept).

**Left on Task 5:** just the **Loom video** (walkthrough of the harness + findings). Everything else is Task 6 / Task 7 / a small optional app fix — see TODO.

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

## DONE this session (all on `main`, commit `cdb588e`)

- ✅ **RAGAS agentic surface** (`evals/surfaces/ragas_agentic.py`) — DECISIONS #9–#12. gpt-4o reasoning-judge deviation **kept (user confirmed)**.
- ✅ **Structured-extraction surface** (`evals/surfaces/extraction_eval.py` + `datagen/generate_extraction_dataset.py`) — DECISIONS #13. Finding: perfect precision; glm structured-output unreliable (run-variable field-drop + null-JSON) → needs a retry/validation guard, not a model swap.
- ✅ **Root README Task 5 write-up** (four surfaces, results, every why).
- ✅ **evals/ restructure** (`lib`/`datagen`/`surfaces`/`results`, paths centralized in `lib/_env.py`) + **A/B/C → A_stateless/B_small/C_scale rename**.

## TODO (in priority order)

1. **Loom video** — the last Task 5 deliverable. Walk through: the head-to-head design + the four surfaces, the deterministic-cross-check methodology, and the headline results (C_scale 10/10 vs 7/10; extraction precision 1.00 + the glm reliability finding).
2. ✅ **DONE — extraction guard** (`app/agent.py`): `extract_and_log_error` now retries on a dropped-field/raising call (`EXTRACTION_MAX_ATTEMPTS=3`), trusts `had_error=False` immediately, logs only a complete record (else fail-safe), each attempt bounded by `EXTRACTION_TIMEOUT=60s`. Eval sibling `extract_error_record` left un-guarded (measures raw baseline). Verified by `tests/test_extraction_guard.py` (14 checks, no network). Model config unchanged (deepseek default). See DECISIONS #13 + CHANGELOG.
3. **Task 6** (Advanced Retrieval) — **retrieval sweep DONE; model bake-off NEXT.**
   - ✅ **Retrieval sweep DONE** (`evals/surfaces/retrieval_sweep.py` → `results/retrieval_sweep.{md,json}`). Fixed the Task 5 circularity (query = rule's own `incorrect_example`, embedded in target doc): expanded grammar corpus 24→98 genuine rules + authored 43 **non-circular** fresh-error queries (`evals/datagen/retrieval_queries.json`, built by `build_retrieval_queries.py`). Baseline no longer saturated (recall@1 0.49). Result: **hybrid (BM25+dense RRF) WINS on quality** (recall@1 0.49→0.56, MRR 0.63→0.70 — particle exact-match, the real Task 3 hypothesis) = the "advanced retriever". **BGE-M3 = latency/cost trade** (recall@1 0.47 ~tie, but p50 27ms vs 310ms OpenAI network, no API fee) = the "one other change". Qwen3-Embedding-8B not run (needs GPU endpoint). Task 5 RAG surface **re-based on 98 rules** (ContextRecall 0.93, det. recall@3 1.0 / MRR **0.95** — 2/24 near-neighbour slips). Task 6 eval deps in `pyproject` `[task6]` extra (`uv sync --extra task6`), kept out of the prod image.
   - ✅ **Model bake-off DONE** (`evals/surfaces/model_bakeoff.py` → `results/model_bakeoff.{md,json}`, 12 grounded-correction cases/model, sequential for clean latency, judge=glm fixed). **Quality ties** (correct_fix 1.00 all three, 0 misleading). **Latency** p50/p95: deepseek 6.1s/13.4s (tightest), glm 5.2s/35.4s (long tail — glm+qwen run as reasoning models), qwen 11.3s/52.6s. **timeout_rate 0/12 all** — deepseek didn't hang in-sample, but that's too small to rule out the rare catastrophic tail (reported as caveat, not "reliable"). **DECISION: keep deepseek default + guard (guard is what makes it safe), glm fallback, drop qwen.** Bake-off = grounded generation per model NOT full agent (drill_generator internally calls DEFAULT model → would leak deepseek latency). Task 6 write-up in README §6.1/§6.2.
   - Decision pending for user: wire hybrid into production `grammar_rule_fetcher` (adds rank-bm25+jieba to the image). And a separate README/reality gap flagged: Task 3 data table claims hsk_vocab ~5,000 / error_patterns ~80 but actual corpus is 22 / 16 (grammar now 98).
4. **Task 7** + deferred UX: mode chat profiles, model selection in UI.

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
