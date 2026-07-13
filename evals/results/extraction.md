# Structured-extraction eval — `extract_and_log_error`

Extraction model **glm** · correction judge **glm**. The hidden post-turn surface that writes the learner's error corpus; measured on whether a turn gets *logged*, whether the category is right, and whether the stored correction is valid. See `results/README.md` for how to re-derive any number.

## had_error detection (would this turn be logged as an error?)

| | Predicted log | Predicted no-log |
|---|---|---|
| **Actually an error** | TP 33 | FN 1 |
| **Actually clean** | FP 0 | TN 17 |

- **Precision 1.000** (headline — a false positive logs a clean sentence as a mistake and poisons the corpus)
- **Recall 0.971**  ·  **F1 0.985**

## ⚠️ Dominant defect — glm structured-output UNRELIABILITY (not capability)

The `glm` extractor produces INCOMPLETE records intermittently — two facets of the same flakiness, both **run-variable** (a case that fails on one call returns a complete record on the next; re-probed cases confirmed this), and NOT fixed by switching to the `function_calling` method:

1. **Field omission** — on **12 of 33 logged records** it returns `had_error=True`+`original` but leaves `correction` (and usually `category`+`explanation`, 12 empty categories) blank. Production gates logging only on `original`, so these enter the corpus as a flagged error with no fix (empty category coerced to `grammar`).
2. **Malformed JSON** (intermittent — this run: 0 of 51 cases) — it sometimes emits JSON `null` for the string fields (schema expects `""`), raising a parse error. Production wraps extraction in try/except and logs nothing on any error, so this fails SAFE (nothing logged) — scored here as production behaves (a clean input → correct TN; a real error → a missed log).

Crucially this is **not a capability limit**: the correction is present in the coach reply the extractor reads, and for the very same inputs the model emits a fully correct record on a retry (when non-empty, correction is **0.952 valid**, 21 cases; category has only 2 genuine mismatches). The fix is a **retry-on-incomplete / field-validation guard around the extraction call**, not a model swap — and it reproduces regardless of structured-output method. Measured on glm because deepseek (production default) hangs and is untested here (DECISIONS #4, #13).

## Category accuracy (specific-category golds only)

- **0.500** over 16 logged particle/word-order/measure-word cases (exact canonical match).
- Of the misses, 6 are **empty** (the omission above) and only 2 are genuine mismatches — so when a category is emitted it is almost always right.
- The 17 `grammar` catch-all golds are underspecified and not scored; of them the extractor refined 3 to a specific category (arguably *more* precise than the gold).

## Correction validity (logged positives)

- **0.636** valid over 33 logged cases — 20 by exact match to gold, the rest by focused judge. The gap from 1.0 is entirely the empty-correction omission above (**0.952** valid when non-empty).

## False negatives (real error missed)

- `A32`: input `虽然很贵，我还是买了。` (gold grammar)

## Category misclassifications (specific golds)

- `A07`: gold `measure_word` → predicted ``
- `A09`: gold `particle` → predicted `grammar`
- `A10`: gold `particle` → predicted ``
- `A14`: gold `word_order` → predicted `vocabulary`
- `A15`: gold `word_order` → predicted ``
- `A28`: gold `measure_word` → predicted ``
- `A31`: gold `particle` → predicted ``
- `A40`: gold `particle` → predicted ``

## Invalid corrections

- `A07`: input `我有三书。` → `` (judge: The proposed correction is empty, leaving the original error uncorrected.)
- `A10`: input `他高兴的笑了。` → `` (judge: The proposed correction is empty, so it does not fix the error (using 的 instead of 地).)
- `A15`: input `这个一点儿贵。` → `` (judge: The proposed correction is empty, leaving the original error uncorrected.)
- `A21`: input `虽然很累，我很开心。` → `` (judge: The proposed correction is empty, leaving the original error (missing conjunction) uncorrected.)
- `A25`: input `她把书被他借走了。` → `` (judge: The proposed correction is empty, so it does not fix the learner's error.)
- `A28`: input `三个书、两个纸` → `` (judge: The proposed correction is empty, leaving the learner's error uncorrected.)
- `A31`: input `他跑的很快。` → `` (judge: The proposed correction is empty, leaving the original error uncorrected.)
- `A36`: input `我两个小时看了书。` → `我看了两个小时的书。` (judge: The proposed correction '我看了两个小时的书。' is grammatically correct and preserves the learner's intended meaning. It uses a valid Chinese structure where the duration phrase '两个小时' modifies the noun phrase '书' within the verb-object construction '看...书'. Although it differs from the reference, it is an acceptable alternative correction for the original error involving the placement of the duration phrase and verb-object separation. Therefore, it should be accepted.)
- `A37`: input `你要茶或者咖啡？` → `` (judge: The proposed correction is empty, so it leaves the original error uncorrected. The original sentence uses '或者' (huòzhě), which is typically used in statements, while '还是' (háishì) is required for offering choices in questions. An empty correction does not fix this grammatical issue and is therefore invalid.)
- `A38`: input `我不看懂这本书。` → `` (judge: The proposed correction is empty, so the original error remains uncorrected. A valid fix would be something like 我没看懂这本书。 or 我看不懂这本书。)
- `A39`: input `她是很高。` → `` (judge: The proposed correction is empty, so it does not fix the error in the learner's original sentence.)
- `A40`: input `我很好，你吗？` → `` (judge: The proposed correction is empty, so it does not fix the error in the learner's original sentence.)
