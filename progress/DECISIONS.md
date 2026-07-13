# Key decisions & gotchas (read before resuming Task 5)

1. **RAGAS import is broken out-of-the-box.** ragas 0.4.3 hard-imports
   `langchain_community.chat_models.vertexai` which lc-community 0.4.2 deleted.
   Fix is a **module shim in `evals/lib/_env.py`** (imported first). Do NOT fix by
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
   reliable. This is why Gen-1 metrics are boolean/extractive and C_scale uses the
   deterministic `agg_parse.py` parser, not an LLM extractor.

6. **Dataset is deterministic, not LLM-generated.** `test_dataset.json` is built
   from the reference corpus so A_stateless cases carry ground-truth `expected_rule_id`
   → enables exact recall@k as a cross-check on RAGAS ContextRecall. Do NOT switch
   to ragas `TestsetGenerator` (no retrieval targets — strictly worse).

7. **Head-to-head is run-unstable on C_scale** (10/10-vs-7/10 one run, 6/6 another).
   Honest framing for the write-up: agent = guaranteed-exact oracle; naked LLM =
   run-to-run noisy approximator. The differentiator is reliability/exactness, NOT
   raw capability. Don't over-claim "beats naked LLM."

8. **Agent surface for RAGAS agentic metrics needs the message trace.** DONE via
   `app/agent.py::invoke_with_trace` — a single-graph, timeout-bounded invoke returning
   the raw langchain message list. It does NOT use `run_agent` (whose fallback silently
   swaps models, corrupting provenance). The app never imports ragas; the langchain→
   `ragas.messages` conversion lives in `evals/surfaces/ragas_agentic.py::to_ragas_messages`.

9. **`ToolCallAccuracy` is an exact tool-SET match, not recall.** `strict_order` defaults
   **True** (`sequence_aligned = pred_names == ref_names`, multiplies the whole score); we
   set `strict_order=False` for order-free multiset match, but it still scores 0 for ANY
   missing OR extra tool. The agent adds sanctioned drills/dictionary lookups, so its TCA
   is low (B=0.10) — reported beside a deterministic **required-tool recall** (0.992) +
   **extra-tool rate**. Also: strip tool args to `{}` on BOTH pred and ref — default arg
   comparison is `ExactMatch`, and our free-text query args have no ground truth (`_get_arg
   _score` returns 1.0 only when both sides are empty).

10. **`AgentGoalAccuracyWithReference` is UNUSABLE — use `WithoutReference`.** Its
    compare-outcome prompt rates semantically identical outcomes ("total is 60" vs "the
    total number of logged errors is 60") as "different" → ~0 everywhere, on BOTH
    gpt-4o-mini AND gpt-4o (not a judge-strength issue). `WithoutReference` infers the goal
    from the conversation and is reliable. It measures **task COMPLETION, not correctness**
    (a wrong "45" when truth is 60 still scores 1.0), so `agg_parse` stays the sole
    correctness authority on C_scale. This surface runs the agent ALONE (an oracle on Type
    C), so completion≈correctness≈1.0 here — the completion-vs-correctness GAP lives in the
    head-to-head naked arm, NOT this file.

11. **Agentic reasoning judges use gpt-4o, not gpt-4o-mini.** DEVIATION from #3 (scoped to
    this surface). gpt-4o-mini's `AgentGoalAccuracy` goal-verdict coin-flips on complete
    multi-part answers (verified [1,1,0,0,1] on a real trace); gpt-4o is stable
    ([1,1,1,1,1]). Env `RAGAS_AGENTIC_EVALUATOR` (default gpt-4o). AGA still has ~20%
    residual false-negatives even on gpt-4o (C_scale completion reads 0.80 vs deterministic
    1.00 — the shortfall is judge noise). ToolCallAccuracy needs no LLM (ExactMatch).

12. **`TopicAdherenceScore` demoted — too unstable to headline.** Even gpt-4o oscillates
    0.0↔0.67 on a clearly on-topic error-count question (hypersensitive to reference-topic
    wording + run noise). Raw RAGAS number kept in JSON only. Headline adherence = a **focused
    gpt-4o binary judge** (FULFILLED vs DECLINED) over 4 off-topic probes. NOTE: an early
    deterministic proxy (`has_chinese`/redirect + no web_search) was WRONG — the coach fulfils
    off-domain requests AND sprinkles Mandarin on top, so a Chinese-content check reads every
    answer as a "redirect" (falsely reported 3/4 deflected; the real number is ~2/4). **Finding:
    topic adherence is WEAK** — the agent readily fulfils a recipe / sports-fact request with a
    Mandarin twist rather than steering back; it declines the coding request. A real guardrail
    gap (worth flagging), and behaviour is run-variable so the 4-probe number is directional.

13. **Structured-extraction surface scores the LOGGING predicate, not the raw bool — and the
    headline finding is field OMISSION, not misclassification.** `extract_and_log_error` is the
    hidden post-turn call that writes the learner's corpus; a wrong record silently poisons the
    B_small/C_scale memory the other two surfaces depend on. Design choices: (a) added a side-effect-free
    eval sibling `extract_error_record` (no `memory` write, `_has_chinese` guard applied eval-side
    so guard-skips are scored deterministically, model overridable to glm); (b) precision/recall
    computed on the EFFECTIVE `would_log` predicate (`has_chinese AND had_error AND original`), the
    thing that actually writes to the corpus; (c) category scored only on the 20 SPECIFIC-category
    golds — the 20 `grammar` golds are the catch-all ("use grammar if unsure"), underspecified, so
    reported separately; (d) correction validity is deterministic exact-match first, focused LLM
    judge (bare-sentence prompt, NOT llm_judge's coaching-answer judge) only on the residue; (e)
    negatives carry a REAL generated coach reply (empty/grammar-discussing replies prime false
    positives — a correct-sentence negative with a blank reply is a harness bug, not a finding).
    **Result:** precision **1.00** (0 false positives — the guardrail against corpus poisoning is
    perfect), recall **~0.95–0.97** (run-variable; the recurring miss A32 is a debatable one-clause
    sentence).
    **The real finding is glm structured-output UNRELIABILITY, and it is NOT a capability limit —
    the earlier "can't do multi-field extraction / drop deepseek" framing was WRONG.** Two
    run-variable facets: (i) *field omission* — on ~12–18/33 logged records (varies per run) glm
    returns `had_error`+`original` but drops `correction`+`category`+`explanation` TOGETHER; (ii)
    *malformed JSON* — it intermittently emits `null` for the string fields, raising a parse error
    that production's try/except turns into a silent no-log. Proof it's flakiness not capability:
    (a) the correction is present in the coach reply the extractor reads; (b) the SAME inputs return
    a complete, correct record on a retry (A09/A18 dropped fields in one run, populated on another);
    (c) when non-empty, correction is ~0.95 valid and category has ≤2 genuine mismatches;
    (d) it reproduces on both `json_mode` and `function_calling`; (e) **it persists at temperature 0
    — glm returned different outputs for the SAME input at temp 0 (A18: 1/3 complete over 3 calls),
    so this is provider-side non-determinism, not sampling temperature** (tested because temp is the
    obvious variability lever; `get_llm` defaults 0.2). **So the fix is a retry-on-incomplete /
    field-validation guard around the extraction call — NOT a model swap and NOT just lowering
    temperature.** Whether deepseek (prod default; hangs, untested here) shares the flaw is unknown;
    the guard is needed regardless. Two eval-fidelity choices this forced: extraction failures are scored the way
    production behaves (fail-safe → not logged), never dropped; and 6 corpus inputs carrying English
    meaning-annotations (e.g. "（meaning: I have tried…）") were EXCLUDED as invalid — the "error"
    only exists relative to leaked intent a learner never types (stripping would relabel a
    grammatical sentence as an error), leaving 34 clean positives.
