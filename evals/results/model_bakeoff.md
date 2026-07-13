# Task 6.2 — Model bake-off

12 A_stateless correction cases per model, grounded-correction generation (same retrieved rules for every model). Per-turn timeout 120s; judge = glm (fixed across models). Latency per COMPLETED turn.

| Model | correct_fix | misleading | timeout_rate | errors | latency p50 (ms) | latency p95 (ms) |
|---|---|---|---|---|---|---|
| deepseek | 1.000 (11) | 0 | 0.000 (0/12) | 0 | 6111.700 | 13378.800 |
| glm | 1.000 (12) | 0 | 0.000 (0/12) | 0 | 5214.600 | 35447.300 |
| qwen | 1.000 (12) | 0 | 0.000 (0/12) | 0 | 11332.400 | 52611.800 |

> **timeout_rate** is the column Task 5 could not provide: turns that breached the 120s bound — the operational cost of DeepSeek's OpenRouter hangs (DECISIONS #4), measured rather than asserted. **correct_fix** count in parens = turns a verdict was obtained on (timed-out/errored turns produce no answer to judge).
