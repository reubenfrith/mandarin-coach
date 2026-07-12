# Type C Preflight — Thesis Discrimination Check

**Date:** 2026-07-12 · **Model:** deepseek (DeepSeek V4) · **Embeddings:** OpenAI text-embedding-3-small

The single load-bearing check before building the full harness: does an at-scale
aggregation query (60 mixed-category error records) actually discriminate the agent
from a naked LLM handed the *same* records? And does the deterministic tool fire?

## Setup

- Isolated eval user seeded with a 60-record corpus (`seed_data.build_typec_corpus`)
  with a designed trend: particle **increasing**, tones/vocabulary **decreasing**,
  measure_word/word_order **steady**.
- Query: *"How many mistakes total? Break down by category with exact counts. Most
  frequent? Increasing or decreasing per category?"*
- Naked control arm: same model, **all 60 records dumped into context**, plus a
  strong "count carefully, do not estimate" analyst prompt (the fair baseline).

## Result — the thesis holds, and the gap is large

| | Total | Breakdown by category | Trends |
|---|---|---|---|
| **Ground truth** (`error_stats`) | 60 | particle 15, tones 14, measure_word 12, word_order 10, vocabulary 9 | particle↑, tones↓, vocabulary↓, measure_word/word_order steady |
| **Agent** (tool fired ✓) | ✅ 60 | ✅ **exact** (15/14/12/10/9) | ✅ **all correct** |
| **Naked LLM** (60 records in context) | ✅ 60 | ❌ fabricated **uniform "12 each"** — declared a 5-way tie | ❌ 2/5 wrong (called measure_word & word_order *decreasing*; both steady) |

**Key finding:** `error_pattern_analyser` (→ deterministic `error_stats`) fired
reliably, so the agent's numbers are exact by construction. The naked LLM, even
given every record, did **not** overflow context — it silently defaulted to a
plausible-but-false uniform distribution and mis-called trends. This is precisely
the "database operation, not a language operation" failure the README predicted.

**Consequence for the build:** the head-to-head is worth running in full; the Task 2
prose about at-scale aggregation is supported by evidence (not toned down). Proceed
to author the full 60-case dataset and harness.
