# Task 6.1 — Retrieval sweep

43 fresh non-circular queries over the 98-rule grammar corpus. Deterministic exact gold rule-id match (no LLM judge). Higher recall/MRR is better; lower latency is better.

| Config | recall@1 | recall@3 | recall@5 | MRR | latency p50 (ms) | latency p95 (ms) |
|---|---|---|---|---|---|---|
| baseline | 0.488 | 0.744 | 0.837 | 0.628 | 310.4 | 437.0 |
| bge_m3 | 0.465 | 0.698 | 0.744 | 0.612 | 27.3 | 375.7 |
| hybrid | 0.558 | 0.767 | 0.884 | 0.698 | 318.6 | 456.3 |

> **baseline** = OpenAI text-embedding-3-small, dense (production default). **bge_m3** = BAAI/bge-m3 local dense (Axis 1). **hybrid** = BM25 (jieba) + OpenAI dense, RRF (Axis 2). **Qwen3-Embedding-8B** (Axis 1) was not run — ~8B params needs a dedicated GPU endpoint, out of scope for the build machine.

> Latency note: OpenAI figures include the embedding-API round-trip (network); BGE-M3 is local CPU encode with no per-call fee. That is the real per-query trade once quality is close.
