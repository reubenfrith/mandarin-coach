# Changelog

Session-level record of what changed and why. Deeper rationale lives in `DECISIONS.md`;
current state in `STATUS.md`.

## 2026-07-13 — Reference-corpus expansion (full HSK + Chinese Grammar Wiki)

Two open-source ingests, both attributed, both keeping the evals valid.

**HSK vocabulary 22 → 4,991** (`data/hsk_vocab.json` via new `build_hsk_vocab.py`) from
drkameleon/complete-hsk-vocabulary (MIT; CC-CEDICT glosses), old HSK 1–6 standard, curated
examples preserved. Payoff: `dictionary_lookup` now grounds HSK level for ~5k words, not 22.
Fixed `load_reference_data` to batch `col.add` (OpenAI embeddings reject >2048 inputs/call).

**Grammar +217 Chinese Grammar Wiki points** (`data/grammar_patterns.json`) ingested via
chanind/cn-grammar-matcher (matcher MIT; content © AllSet Learning / Chinese Grammar Wiki,
CC BY-NC-SA, non-commercial use, attributed). Per advisor guidance, kept in a **separate
`grammar_patterns` collection** so the 98-rule `grammar_rules` every eval depends on is
untouched; `grammar_rule_fetcher` (via `query_grammar_rules_hybrid`) now **unions both**
collections (BM25+dense RRF over the union). The Task 6 sweep is **frozen** (measured on the
curated 98 only) — the single-gold-id queries would collide with CGW near-duplicates, so
re-running would mismeasure; technique selection (hybrid>dense) is corpus-size-independent.
No fabricated HSK levels: CGW points carry `hsk_level=0` (unknown) and the fetcher omits the
"(HSK …)" tag rather than printing a guess. README Task 3 + data/README.md credit both sources.

**Coverage check** (`evals/surfaces/coverage_check.py` → `results/coverage_check.md`, README §6.1b):
proves the +217 is upside-only. Coverage: 15 CGW-only topics go from curated-only **0/15** →
union **recall@3 0.87**. Precision retention: curated-gold recall@3 **0.767→0.744** (unchanged) —
of 11 curated golds outside top-3, 10 were ALREADY sweep misses; only **1 new drop (R38)**, which
had a valid alternative. So more coverage at the same precision, no eval-decision impact.

## 2026-07-13 — Task 6.2 model bake-off (keep/drop-deepseek RESOLVED)

`evals/surfaces/model_bakeoff.py` → `results/model_bakeoff.{md,json}`. 12 grounded-correction
cases per model, run SEQUENTIALLY (concurrency=1) for clean per-turn latency, judge=glm fixed.

Design catch during build: first version ran the FULL agent per model, but `drill_generator`
internally calls `get_llm()` with the DEFAULT model (deepseek) → deepseek's latency/hangs leaked
into glm's numbers (glm turns showed 44–62s). Rewrote to grounded-correction generation (same
retrieved rules for every model, only the model varies) so the model is the only variable.

Results: **quality ties** (correct_fix 1.00 for deepseek/glm/qwen, 0 misleading — quality is NOT
the differentiator). Latency p50/p95: deepseek 6.1/13.4s (tightest), glm 5.2/35.4s (long tail),
qwen 11.3/52.6s (slowest). Calibration probe: glm & qwen run as REASONING models (emit thinking
blocks) → the long tails; deepseek answers directly. timeout_rate 0/12 all — deepseek did NOT hang
in-sample, reported WITH the caveat that 12 cases can't rule out the rare 30-min tail.

**Decision: keep deepseek default + the turn-timeout/glm-fallback guard (the guard is what makes it
safe), glm stays fallback, drop qwen (slowest, no edge).** Updated agent memory `deepseek-reliability-fallback`.

## 2026-07-13 — Task 6 retrieval sweep (advanced retriever + embedding swap)

Built the Task 6 retrieval half. First finding: the Task 5 "retrieval is saturated at
recall@1=1.0" story was **circular** — each A_stateless query is a rule's own
`incorrect_example`, which `_grammar_text` embeds verbatim inside the target doc, so it
measured lexical overlap, not semantics. Fix (non-gaming):
- **Corpus 24→98 genuine grammar rules** (`data/grammar_rules.json`), dense with real
  near-neighbours (aspect particles, 有/是/在, 再/又, 只要/只有, complements, degree adverbs).
- **43 fresh non-circular queries** (`evals/datagen/retrieval_queries.json` + builder) — new
  vocab, mapped by construction to the best-fit rule. Baseline drops to recall@1 0.49 (real headroom).
- Pinned `generate_dataset.py` type-A to the first 24 rules so Task 5's frozen 40-case dataset
  still reproduces exactly (verified: git diff empty).

**Sweep result** (`evals/surfaces/retrieval_sweep.py`, deterministic exact rule-id match + latency):
- **Hybrid (BM25 jieba + dense, RRF) WINS quality** — recall@1 0.49→0.56, recall@3 0.74→0.77,
  MRR 0.63→0.70. Mechanism = Chinese particle exact-match (the Task 3 hypothesis), and it's NOT the
  circularity bug (queries are fresh; BM25 matches the shared *particle*, not a verbatim sentence).
  → the "advanced retriever" deliverable.
- **BGE-M3 = latency/cost trade, quality tie** — recall@1 0.47 (~baseline), but p50 27ms local vs
  310ms OpenAI network + no API fee. → the "one other change" (embedding swap) deliverable.
- Qwen3-Embedding-8B NOT run (needs GPU endpoint; documented, not hidden).

**Task 5 re-based on 98 rules** (2A, per user — one consistent corpus, no separate surfaces):
re-ran RAG surface → ContextRecall 0.93 / ContextRelevance 0.89 / Faithfulness 0.83 / NoiseSens 0.20 /
AnswerAcc 0.83; deterministic recall@3 1.0, **MRR 1.0→0.95** (2/24 near-neighbour slips over the bigger
corpus — honest, reported). README Surface 2 updated.

Eval-only heavy deps (sentence-transformers/torch, rank-bm25, jieba) added as `pyproject` `[task6]`
extra — kept OUT of the prod Docker image. NEXT: model bake-off (deepseek/glm/qwen quality + latency +
timeout-rate).

## 2026-07-13 — Extraction guard + README Task 4 / auth alignment

Two things this session, both off the STATUS TODO.

**1. Extraction guard (STATUS TODO #2, DECISIONS #13).** Wrapped `extract_and_log_error`
(`app/agent.py`) in a retry / field-validation / fail-safe loop that directly addresses the
Task 5 finding (glm returns `had_error=True` with `correction`/`category`/`explanation`
dropped, or malformed JSON that raises — provider-side non-determinism, not a capability
limit). Behaviour:
- retry up to `EXTRACTION_MAX_ATTEMPTS` (default 3) on a dropped-field record OR a raising call;
- trust a confident `had_error=False` immediately (a correct sentence is a valid result — no retry);
- log ONLY a complete record (`had_error AND original AND correction`); if none is ever obtained, log nothing (fail-safe, unchanged from before);
- each attempt bounded by `asyncio.wait_for(EXTRACTION_TIMEOUT=60s)` so the retry loop can't compound a provider hang (DECISIONS #4 — litellm's own timeout doesn't reliably interrupt one).
- Factored the single call into `_extract_record` (shared with the eval sibling). `extract_error_record` stays **un-guarded on purpose** — the extraction surface measures the *raw* pre-guard reliability. Model config left as-is (deepseek default) per user.
- Verified by `tests/test_extraction_guard.py` (NEW) — 14 deterministic checks, no network (stubs `_extract_record` + `memory.add_personal_error`). All pass.

**2. README Task 4 + auth alignment.** Wrote the Task 4 Prototype section (was a placeholder)
documenting the live deployed app, and corrected four stale Google-OAuth references to the
username/password auth the app actually ships. Committed `a37b810`.

## 2026-07-13 — Structured-extraction surface (Task 5, third of three)

Built the last eval surface: `extract_and_log_error`, the hidden post-turn call that
mines each learner turn into a structured record and appends it to their error corpus.
It never surfaces to a user, but a wrong record silently poisons the B_small/C_scale memory the
other two surfaces depend on — so this eval is what justifies trusting them.

Net result — the guardrail is **perfect (precision 1.00, 0 false positives)**: no clean
sentence, question, or English message is ever logged as an error. The real finding is
**glm structured-output UNRELIABILITY (not a capability limit)**: run-variable field
omission (drops `correction`+`category`+`explanation` together on ~12–18/33 logged records)
plus intermittent malformed JSON (`null` string fields → parse error). Proven flakiness —
the same inputs return complete, correct records on retry, the correction is present in the
coach reply the extractor reads, it's ~0.95 valid when non-empty, and it reproduces on both
`json_mode` and `function_calling`. **Fix = a retry/validation guard around the extraction
call, NOT a model swap.** (An earlier draft wrongly framed this as "glm can't do multi-field
extraction / drop deepseek" — corrected after probing `explanation` + retries, see below.)

### Files changed

- **`app/agent.py`** — added `extract_error_record(user_input, agent_answer, model=None)`.
  - *Why:* the eval needs the raw `ErrorExtraction` (incl. `had_error`/`category` even when
    a record wouldn't be logged) WITHOUT the `memory.add_personal_error` side effect and
    without the `_has_chinese` guard (applied eval-side so guard-skips are scored
    deterministically). Mirrors the `invoke_with_trace` precedent; app behaviour unchanged.

- **`evals/datagen/generate_extraction_dataset.py`** + **`evals/datagen/extraction_dataset.json`** — NEW.
  34 positives (labels from test_dataset, coach replies reused from head_to_head — free +
  faithful) + 17 negatives. **6 corpus inputs carrying English meaning-annotations** (e.g.
  "（meaning: I have tried…）") are EXCLUDED as invalid inputs — the "error" only exists relative
  to leaked intent a learner never types; stripping would relabel a grammatical sentence as an
  error. Correct-sentence/question negatives get a REAL generated coach reply (glm) frozen in —
  an empty/grammar-discussing reply would prime false positives (DECISIONS #13).

- **`evals/surfaces/extraction_eval.py`** → `results/extraction.{md,json}` — NEW. Scores the effective
  `would_log` predicate (had_error P/R/F1), category accuracy (specific golds only), and
  correction validity (deterministic exact-match + focused bare-sentence judge). Extraction
  failures are scored the way production behaves (retry-once, then fail-safe → not logged) and
  never dropped. Splits every miss into OMISSION vs malformed-JSON vs wrong-value. `--from-rows`
  re-aggregates saved rows with no model calls.

- **`progress/STATUS.md`, `progress/DECISIONS.md` (#13), `evals/README.md`,
  `evals/results/README.md`, memory** — updated: 3-of-3 surfaces DONE, the corrected finding,
  run commands.

### Verification

- Smoke slice (3+3) → full run (34+17, all 51 rows present, none dropped). Confusion matrix
  re-derived independently from the raw rows: precision 1.00.
- **Cause investigated, not assumed** (an advisor review caught the first draft asserting a
  capability limit): dumped the full `ErrorExtraction` incl. `explanation` on the dropped cases
  → all secondary fields drop together; re-probing returned complete records → run-variable, not
  deterministic; tested `function_calling` method AND temperature 0 → same behaviour (A18 gave
  different outputs for the same input at temp 0 → provider-side non-determinism, not sampling temp).
  Conclusion: structured-output reliability, fixable with a retry/validation guard, not a model
  swap and not just lowering temperature.

## 2026-07-12 — RAGAS agentic-metric surface (Task 5 #8)

Built the second of three eval surfaces: standard RAGAS **agentic** metrics over the
agent's tool-call trace. Net result — the surface runs clean on all 60 cases; the load-
bearing signal is a deterministic **required-tool recall of 0.992** (the agent reliably
grounds + checks history), and a genuine finding that **topic adherence is weak**.

### Files changed

- **`app/agent.py`** — added `invoke_with_trace(graph, user_input, thread_id)`.
  - *Why:* the agentic metrics need the full LangGraph message list (Human / AI[tool_calls]
    / Tool), but `run_agent` returns only final text AND silently falls back to a different
    model on a stall (corrupting provenance). New fn does a single-graph, timeout-bounded
    invoke and returns `(final_text, raw_messages)`. Returns **langchain** messages — the
    live app must never import ragas, so the ragas conversion stays in the eval file.

- **`evals/surfaces/ragas_agentic.py`** — NEW. Agentic surface → `results/ragas_agentic.{md,json}`.
  - ToolCallAccuracy, AgentGoalAccuracy (WithoutReference), off-topic deflection, each paired
    with a deterministic cross-check (the repo's signature move).
  - Agent-under-test = glm (reproducible; deepseek hangs — see DECISIONS #4).

- **`progress/STATUS.md`, `progress/DECISIONS.md` (#8–#12), `evals/README.md`** — updated to
  mark the surface DONE and record the metric gotchas + the judge-model deviation.

- **`~/.claude/.../memory/ragas-agentic-metric-gotchas.md`** — NEW memory of the traps below.

### Non-obvious decisions & why (full detail in DECISIONS #9–#12)

1. **ToolCallAccuracy is an exact tool-SET match, not recall.** `strict_order` defaults True
   → set False; args stripped to `{}` on both sides (default ExactMatch arg-compare would
   zero every case on free-text query wording). It scores 0 for any missing OR extra tool,
   so the agent's sanctioned drills tank it — hence the deterministic required-tool-recall +
   extra-tool-rate cross-checks carry the real signal.

2. **`AgentGoalAccuracyWithReference` is unusable → use `WithoutReference`.** Its compare-
   outcome prompt rates identical outcomes "different" (fails on gpt-4o too). WithoutReference
   measures task **completion, not correctness** (`agg_parse` stays the correctness authority).

3. **Reasoning judges use gpt-4o, NOT the gpt-4o-mini of DECISIONS #3** (⚠️ deviation, flagged
   to user). gpt-4o-mini's goal verdict coin-flips on multi-part answers; gpt-4o is stable.
   Env `RAGAS_AGENTIC_EVALUATOR`. Scoped to the agentic reasoning metrics only.

4. **`TopicAdherenceScore` demoted — too unstable to headline** (oscillates 0.0↔0.67 on a
   clearly on-topic case even on gpt-4o). Raw number kept in JSON; headline is a focused
   gpt-4o FULFILLED/DECLINED deflection judge. An earlier deterministic `has_chinese` proxy
   was WRONG (the coach fulfils off-domain asks AND adds Mandarin, so it read as a "redirect"
   every time) — replaced after reading the actual answers.

### Verification

- End-to-end smoke tests confirmed ToolCallAccuracy predictions (exact-set match), AGA
  stability on gpt-4o, and the deflection judge on all 4 probes before the full run.
- Full 60-case run: 0 failures (one transient OpenRouter timeout auto-retried).
- Scratch probe/smoke files removed; `results/ragas_agentic.{md,json}` are the artifacts.
