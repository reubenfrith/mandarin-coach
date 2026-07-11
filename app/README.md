# app/

This directory contains all application code.

## Files to build

| File | Purpose | Status |
|---|---|---|
| `main.py` | Chainlit entry point — chat UI, Google OAuth, `@cl.on_chat_start` onboarding hook | TODO |
| `agent.py` | LangChain agent — intent router, tool orchestration, session memory | TODO |
| `tools.py` | All 5 agent tools: CC-CEDICT lookup, Tavily search, Error Pattern Analyser, Grammar Rule Fetcher, Drill Generator | TODO |
| `memory.py` | ChromaDB setup — 4 collections, user-namespaced, load/query/write helpers + deterministic error_stats aggregation | DONE |
| `config.py` | LiteLLM + OpenRouter config — model switching for 3-model experiment (DeepSeek V4, GLM-5.2, Qwen3.5-397B) | DONE (thin slice) |
| `prompts.py` | All system and tool prompts | TODO |
