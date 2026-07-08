# data/

This directory contains all RAG source data loaded into ChromaDB at startup.

## Files to build

| File | Collection | Source | Status |
|---|---|---|---|
| `hsk_vocab.json` | `hsk_vocabulary` | HSK 1–6 official word lists — ~5,000 entries with character, pinyin, English meaning, HSK level, example sentence | TODO |
| `grammar_rules.json` | `grammar_rules` | ~150 curated Mandarin grammar rules — rule name, explanation, common English-speaker mistakes, correct/incorrect examples | TODO |
| `error_patterns.json` | `error_patterns` | ~80 English-speaker error archetypes — error type, why it happens, correct usage, examples | TODO |
| `load_data.py` | All | Script to embed and load all source files into ChromaDB on first run | TODO |

## Notes

- `personal_errors` collection is NOT pre-loaded — it is empty per user and grows as they interact with the app
- Collections are user-namespaced: `{user_id}_personal_errors`
- Grammar rules and error patterns can be partially generated synthetically using Claude before launch
- Embedding model comparison (OpenAI vs Qwen3-Embedding-8B vs BGE-M3) is run against these same collections
