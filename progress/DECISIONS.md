# Key decisions & gotchas (read before resuming Task 5)

1. **RAGAS import is broken out-of-the-box.** ragas 0.4.3 hard-imports
   `langchain_community.chat_models.vertexai` which lc-community 0.4.2 deleted.
   Fix is a **module shim in `evals/_env.py`** (imported first). Do NOT fix by
   bumping ragas / downgrading langchain-community — the app is live and pins
   langchain 1.x / langgraph 1.2.9; a version cascade risks the deployed agent.

2. **Use the classic `ragas.metrics` path, NOT `ragas.metrics.collections`.**
   The collections API drives structured output through `instructor`, which sends
   gpt-4o-mini into a degenerate-repetition loop on **NoiseSensitivity**
   (IncompleteOutputException even on a 184-char response, at any max_tokens).
   Classic `ragas.metrics` + `SingleTurnSample.single_turn_ascore()` +
   `LangchainLLMWrapper(ChatOpenAI("gpt-4o-mini", max_tokens=4000))` is stable AND
   is the more widely-recognised API for the cert. `ragas_rag.py` already uses it.

3. **Evaluator judge = gpt-4o-mini** (user-confirmed). Needs `OPENAI_API_KEY`
   (set). Modern `llm_factory` needs a client instance: `llm_factory(model,
   client=AsyncOpenAI(...))` — but we use the classic LangchainLLMWrapper path.

4. **deepseek hangs 30+ min on OpenRouter.** litellm's own timeout does NOT stop a
   hung streaming connection — the app-level `asyncio.wait_for` is the real guard.
   Eval generation uses **glm** (env `RAG_GEN_MODEL`) not deepseek, so runs are
   reproducible. **Keep/drop-deepseek is deferred to the Task 6 bake-off** (add
   latency + timeout-rate columns). Do not drop it reactively — strongest Chinese
   model on paper. (Mirrored in agent memory.)

5. **Structured-output flakiness on OpenRouter models** (glm/qwen/deepseek):
   constrained-int fields (ge=1,le=5) garble to the minimum; nested-object lists
   drift key names; glm sometimes returns prose. Booleans + named scalars are
   reliable. This is why Gen-1 metrics are boolean/extractive and Type C uses the
   deterministic `agg_parse.py` parser, not an LLM extractor.

6. **Dataset is deterministic, not LLM-generated.** `test_dataset.json` is built
   from the reference corpus so Type A cases carry ground-truth `expected_rule_id`
   → enables exact recall@k as a cross-check on RAGAS ContextRecall. Do NOT switch
   to ragas `TestsetGenerator` (no retrieval targets — strictly worse).

7. **Head-to-head is run-unstable on Type C** (10/10-vs-7/10 one run, 6/6 another).
   Honest framing for the write-up: agent = guaranteed-exact oracle; naked LLM =
   run-to-run noisy approximator. The differentiator is reliability/exactness, NOT
   raw capability. Don't over-claim "beats naked LLM."

8. **Agent surface for RAGAS agentic metrics needs the message trace.** `run_agent`
   returns only final text. To build MultiTurnSample you must capture the LangGraph
   message list (HumanMessage / AIMessage[tool_calls] / ToolMessage) using
   `ragas.messages` classes (NOT langchain messages).
