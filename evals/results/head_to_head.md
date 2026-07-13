# Eval Results — Agent vs Naked LLM

Model: **deepseek** · Judge: **glm** · regenerated after A/B/C → A_stateless/B_small/C_scale rename

## A_stateless — Stateless correction (n=40; parity expected; agent wins grounding)

| Metric | Agent | Naked |
|---|---|---|
| Correction accuracy (correct fix) | 36/37 | 32/39 |
| Retrieval recall@3 | 1.0 | — |
| Retrieval MRR | 1.0 | — |
| Factual grounding (correct/checked) | 0.75 (12/16) | 0.8 (24/30) |

## B_small — Memory-informed, small scale (n=10; fair-baseline sanity check)

| Metric | Agent | Naked |
|---|---|---|
| Correction accuracy (correct fix) | 9/10 | 10/10 |
| References error history | 7/10 | 4/10 |
| Cites a specific count | 0/10 | 0/10 |

## C_scale — At-scale aggregation (the decisive metric)

| Metric | Agent | Naked |
|---|---|---|
| Aggregation accuracy | 10/10 | 7/10 |

### Per-question (C_scale)

| Case | Question | Agent | Naked |
|---|---|---|---|
| C01 | total | ✅ | ❌ |
| C02 | most_frequent | ✅ | ✅ |
| C03 | count_particle | ✅ | ❌ |
| C04 | count_tones | ✅ | ❌ |
| C05 | count_measure_word | ✅ | ✅ |
| C06 | increasing | ✅ | ✅ |
| C07 | decreasing | ✅ | ✅ |
| C08 | particle_trend | ✅ | ✅ |
| C09 | tones_trend | ✅ | ✅ |
| C10 | full_breakdown | ✅ | ✅ |
