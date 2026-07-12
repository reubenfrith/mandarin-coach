# app/

This directory contains all application code.

## Files to build

| File | Purpose | Status |
|---|---|---|
| `main.py` | Chainlit entry point — chat UI, username/password auth, `@cl.on_chat_start` onboarding hook | DONE |
| `users.py` | SQLite user store — hashed passwords, per-user profiles (HSK level), auto-create on first login | DONE |
| `agent.py` | LangGraph tool-calling agent (`create_agent`) — MemorySaver checkpointer for per-conversation memory, structured post-turn error logging | DONE |
| `tools.py` | All 5 agent tools: CC-CEDICT lookup, Tavily search, Error Pattern Analyser, Grammar Rule Fetcher, Drill Generator | DONE |
| `memory.py` | ChromaDB setup — 4 collections, user-namespaced, load/query/write helpers + deterministic error_stats aggregation | DONE |
| `config.py` | LiteLLM + OpenRouter config — model switching for 3-model experiment (DeepSeek V4, GLM-5.2, Qwen3.5-397B) | DONE (thin slice) |
| `prompts.py` | All system and tool prompts | DONE |
