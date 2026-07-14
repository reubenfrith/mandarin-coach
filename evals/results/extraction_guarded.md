# Structured-extraction eval — `extract_and_log_error`

**Mode: GUARDED** — the production retry/validation guard is active (retry incomplete/raising calls ×3, discard anything still incomplete). Compare against the baseline `extraction.{md,json}` run over the same dataset.

Extraction model **glm** · correction judge **glm**. The hidden post-turn surface that writes the learner's error corpus; measured on whether a turn gets *logged*, whether the category is right, and whether the stored correction is valid. See `results/README.md` for how to re-derive any number.

## had_error detection (would this turn be logged as an error?)

| | Predicted log | Predicted no-log |
|---|---|---|
| **Actually an error** | TP 24 | FN 10 |
| **Actually clean** | FP 0 | TN 17 |

- **Precision 1.000** (headline — a false positive logs a clean sentence as a mistake and poisons the corpus)
- **Recall 0.706**  ·  **F1 0.828**

## ⚠️ Dominant defect — glm structured-output UNRELIABILITY (not capability)

The `glm` extractor produces INCOMPLETE records intermittently — two facets of the same flakiness, both **run-variable** (a case that fails on one call returns a complete record on the next; re-probed cases confirmed this), and NOT fixed by switching to the `function_calling` method:

1. **Field omission** — on **0 of 24 logged records** it returns `had_error=True`+`original` but leaves `correction` (and usually `category`+`explanation`, 0 empty categories) blank. Production gates logging only on `original`, so these enter the corpus as a flagged error with no fix (empty category coerced to `grammar`).
2. **Malformed JSON** (intermittent — this run: 0 of 51 cases) — it sometimes emits JSON `null` for the string fields (schema expects `""`), raising a parse error. Production wraps extraction in try/except and logs nothing on any error, so this fails SAFE (nothing logged) — scored here as production behaves (a clean input → correct TN; a real error → a missed log).

Crucially this is **not a capability limit**: the correction is present in the coach reply the extractor reads, and for the very same inputs the model emits a fully correct record on a retry (when non-empty, correction is **1.000 valid**, 24 cases; category has only 1 genuine mismatches). The fix is a **retry-on-incomplete / field-validation guard around the extraction call**, not a model swap — and it reproduces regardless of structured-output method. Measured on glm because deepseek (production default) hangs and is untested here (DECISIONS #4, #13).

## Category accuracy (specific-category golds only)

- **0.900** over 10 logged particle/word-order/measure-word cases (exact canonical match).
- Of the misses, 0 are **empty** (the omission above) and only 1 are genuine mismatches — so when a category is emitted it is almost always right.
- The 14 `grammar` catch-all golds are underspecified and not scored; of them the extractor refined 3 to a specific category (arguably *more* precise than the gold).

## Correction validity (logged positives)

- **1.000** valid over 24 logged cases — 21 by exact match to gold, the rest by focused judge. The gap from 1.0 is entirely the empty-correction omission above (**1.000** valid when non-empty).

## False negatives (real error missed)

- `A07`: input `我有三书。` (gold measure_word)
- `A09`: input `他写汉字得很漂亮。` (gold particle)
- `A12`: input `我去中国明年。` (gold word_order)
- `A13`: input `我三个小时看书了。` (gold word_order)
- `A15`: input `这个一点儿贵。` (gold word_order)
- `A16`: input `我能说三种语言。` (gold grammar)
- `A21`: input `虽然很累，我很开心。` (gold grammar)
- `A22`: input `你想去北京或者上海？` (gold grammar)
- `A31`: input `他跑的很快。` (gold particle)
- `A32`: input `虽然很贵，我还是买了。` (gold grammar)

## Category misclassifications (specific golds)

- `A14`: gold `word_order` → predicted `vocabulary`
