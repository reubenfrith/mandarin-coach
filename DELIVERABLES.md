# Deliverables — Traceability

Every rubric line item, mapped to the exact place it is addressed: the write-up
section in [`README.md`](README.md) and, where the deliverable is code or a data
artifact, the file and named symbol that implements it. Code locations are given
as **file → `symbol()`** so they stay greppable across edits (line numbers are a
convenience, current as of this commit).

- **Repo:** https://github.com/reubenfrith/mandarin-coach
- **Live app:** https://34-129-227-111.nip.io
- **Written document:** [`README.md`](README.md) (answers every deliverable below)

---

## Task 1 — Problem, Audience & Scope

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| Succinct 1-sentence problem description | 1 | [Problem statement](README.md#problem-statement) | — (prose) |
| 1–2 paragraphs on why it's a problem for this user | 3 | [Why this is a problem](README.md#why-this-is-a-problem) | — (prose) |
| Workflow diagram: how the user solves it today | 3 | [How learners handle it today](README.md#how-learners-handle-it-today) | Mermaid `flowchart TD`, `README.md:44` |
| Evaluation questions / input–output pairs | 2 | [Evaluation questions](README.md#evaluation-questions) | 8-pair table `README.md:69`; realized as the Task 5 datasets under `evals/datagen/` |

---

## Task 2 — Propose a Solution

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| Solution in one sentence | 1 | [Solution statement](README.md#solution-statement) | — (prose) |
| Infrastructure diagram + one sentence per tooling choice | 7 | [Infrastructure](README.md#infrastructure) | Mermaid `flowchart TD` `README.md:120`; per-component "why" table `README.md:145` |
| Agent workflow diagram, end to end | 7 | [Agent workflow](README.md#agent-workflow) | Mermaid `flowchart TD` `README.md:185`; realized in `app/agent.py` → `build_agent()` / `run_agent()` and `app/tools.py` → `make_tools()` |

---

## Task 3 — Dealing with the Data

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| Describe all data sources & external APIs + their use | 5 | [Data sources](README.md#data-sources) | Reference data in `data/` (`grammar_rules.json`, `grammar_patterns.json`, `hsk_vocab.json`, `error_patterns.json`, `cedict.txt`); embedded by `data/load_data.py` → `app/memory.py` `load_reference_data()`. External APIs: CC-CEDICT via `app/tools.py` `dictionary_lookup` + `_load_cedict()`; Tavily via `app/tools.py` `web_search`. **Note:** the `.txt`/Anki upload source named here is *not wired in v1* — see [Task 4 deviations](README.md#task-4-prototype) and Task 7 item 1. |
| Default chunking strategy + why | 5 | [Chunking strategy](README.md#chunking-strategy) | One-doc-per-record (no splitting), realized in `app/memory.py` `_grammar_text()` / `_grammar_pattern_text()` / `_vocab_text()` / `_error_pattern_text()` (each source record → one document) |

---

## Task 4 — Build End-to-End Prototype

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| End-to-end prototype, deployed with a front end | 15 | [Task 4: Prototype](README.md#task-4-prototype) | **Live:** https://34-129-227-111.nip.io. **Front end + auth:** `app/main.py` (`auth_callback`, `starters`, `on_chat_start`, `on_message`). **Accounts:** `app/users.py`. **Agent:** `app/agent.py` (`build_agent`, `run_agent`, `extract_and_log_error`). **Model gateway:** `app/config.py` `get_llm()`. **Tools:** `app/tools.py` `make_tools()`. **Memory/vector store:** `app/memory.py` (`error_stats`, `add_personal_error`, query fns). **Deploy:** `Dockerfile`, `docker-compose.yml`, `Caddyfile`, [`DEPLOY.md`](DEPLOY.md) |

---

## Task 5 — Evals

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| Prepare a test data set | 2 | [Test set design](README.md#test-set-design) | Generators: `evals/datagen/generate_dataset.py` → `test_dataset.json` (60: 40/10/10), `generate_extraction_dataset.py` → `extraction_dataset.json` (51: 34+17), `seed_data.py` (C_scale corpus). Metric scorers: `evals/lib/llm_judge.py`, `evals/lib/agg_parse.py` |
| Evaluation harness relevant to the problem | 10 | [Results](README.md#results) | Four surfaces: `evals/surfaces/eval_harness.py` (head-to-head), `ragas_rag.py`, `ragas_agentic.py`, `extraction_eval.py`. Outputs in `evals/results/*.{md,json}`; recompute guide `evals/results/README.md` |
| Conclusions about pipeline performance | 3 | [Conclusions](README.md#conclusions) + [per-surface result tables](README.md#results) | Backed by `evals/results/head_to_head.md`, `ragas_rag.md`, `ragas_agentic.md`, `extraction.md` |

---

## Task 6 — Improving Your Prototype

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| Advanced retrieval technique + why (1–2 sentences) | 6 | [6.1 Advanced retrieval: hybrid search](README.md#61-advanced-retrieval-hybrid-search) | Hybrid BM25(jieba)+dense RRF, in production: `app/memory.py` `query_grammar_rules_hybrid()` / `_get_grammar_index()`; swept in `evals/surfaces/retrieval_sweep.py`; non-circular query set built by `evals/datagen/build_retrieval_queries.py` → `retrieval_queries.json` (43) |
| Performance vs original RAG, in a table | 2 | [6.1 sweep table](README.md#61-advanced-retrieval-hybrid-search) | `evals/results/retrieval_sweep.{md,json}` |
| Change to ≥1 other piece, harness-evidenced | 6 | [6.2 Grammar coverage](README.md#62-grammar-coverage-tripled) **and** [6.3 Extraction guard](README.md#63-extraction-guard) | **6.2** coverage ×3 (98→315 docs): ingest `data/grammar_patterns.json` via `app/memory.py` `_grammar_pattern_text()`, measured by `evals/surfaces/coverage_check.py` → `results/coverage_check.*`. **6.3** extraction retry/validation guard: `app/agent.py` `extract_and_log_error()` / `_extract_record()` / `_record_complete()`, before/after via `extraction_eval.py --guarded` → `results/extraction_guarded.*`, unit-checked by `tests/test_extraction_guard.py`. (Also: model bake-off `evals/surfaces/model_bakeoff.py` → `results/model_bakeoff.*`.) |

---

## Task 7 — Next Steps

| Deliverable | Pts | Write-up (README §) | Code / artifact |
|---|---|---|---|
| Reflection: what to keep vs change for Demo Day | 2 | [Task 7: Next Steps](README.md#task-7-next-steps) | — (prose; each item anchored to a specific eval finding) |

---

## Final Submission

| Deliverable | Pts | Location |
|---|---|---|
| Public GitHub repo | — | https://github.com/reubenfrith/mandarin-coach |
| ≤10-minute demo video (live demo + use case) | 10 | https://www.youtube.com/watch?v=IvJwwyUeerg (linked at `README.md:6`) |
| Written document addressing each deliverable | 10 | [`README.md`](README.md) — one section per task; rubric→section map at the top of the file |
| All relevant code | 0 | App: `app/`. Reference data + loaders: `data/`. Evals (harness, datasets, results): `evals/`. Tests: `tests/`. Deploy: `Dockerfile`, `docker-compose.yml`, `Caddyfile`, `DEPLOY.md` |
