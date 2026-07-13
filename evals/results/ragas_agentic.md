# Agentic-metric surface — the agent's tool-use

RAGAS agentic metrics over the LangGraph message trace. Agent-under-test: **glm** · ToolCallAccuracy judge: deterministic ExactMatch · reasoning judges (AgentGoalAccuracy): **gpt-4o** (gpt-4o-mini's goal verdict coin-flips on multi-part answers — see file header).

## ToolCallAccuracy + deterministic tool-selection cross-check
> ToolCallAccuracy is RAGAS's **exact tool-set match** (order-free; no missing, no extra). Our agent proactively offers a sanctioned drill/dictionary lookup, which counts against it — so read it beside the deterministic **required-tool recall** (did it call every tool the task needs) and **extra-tool rate** (how often it adds a sanctioned extra).

| Type | n | ToolCallAccuracy | Required-tool recall | Extra-tool rate | AgentGoalAccuracy (completion) |
|---|---|---|---|---|---|
| A_stateless | 40 | 0.550 | 1.000 | 0.450 | 0.800 |
| B_small | 10 | 0.100 | 0.950 | 0.900 | 0.800 |
| C_scale | 10 | 1.000 | 1.000 | 0.000 | 0.800 |
| **all** | — | 0.550 | 0.992 | — | 0.800 |

> **Reading AgentGoalAccuracy (completion):** the ~0.80 is a judge-noise FLOOR, not a 20% task-failure rate. Even on gpt-4o the WithoutReference goal-verdict marks a minority of genuinely complete answers as incomplete; real incompletion is near-zero (the head-to-head lands 36/37 A_stateless corrections). Treat completion as a 'doesn't go off the rails' sanity check, not a discriminator — the tool metrics carry this surface.

## Task completion vs factual correctness (C_scale)
> AgentGoalAccuracy (WithoutReference) measures whether the agent **completed** the task — inferred a total was asked for and reported one — NOT whether the number was right; a confidently-wrong answer still scores 1.0. This surface runs the agent ALONE, and the agent is an exact oracle on C_scale (see DECISIONS #7), so deterministic correctness is 1.00. AGA sits below that purely as judge error: on the cases where AGA=0, `agg_parse` confirms the correct number WAS in the response, so the task was provably completed and the 0 is necessarily a false negative — not real incompletion. There is **no completion-vs-correctness gap in this file**; that gap (naked LLM reports a wrong number confidently) lives in the head-to-head naked arm — see `head_to_head.md`.

| Metric | Value |
|---|---|
| AgentGoalAccuracy — task completion (C_scale) | 0.800 |
| Deterministic aggregation correctness (C_scale) | 1.000 |

## Topic adherence — off-topic deflection
> RAGAS `TopicAdherenceScore` proved too unstable on this domain to report as a headline (even gpt-4o oscillates 0.0↔0.67 on a clearly on-topic question — the raw number is kept in the JSON). Adherence is instead a focused gpt-4o binary judge (FULFILLED vs DECLINED) over 4 off-topic probes. **Finding: adherence is weak** — the coach readily FULFILS off-domain requests (e.g. a recipe, a sports fact) while adding a Mandarin twist, rather than steering back to coaching; it declines the coding request and, when a web_search returns nothing usable, fails to deliver (weather). A real weak spot worth a guardrail, not a metric artefact. (Small 4-probe sample, agent behaviour is run-to-run variable — read as directional.)

| Metric | Value |
|---|---|
| Off-topic probes deflected (declined) | 2/4 |
| Off-topic probes that triggered web_search | 1/4 |
| RAGAS TopicAdherence off-topic mean (unstable — record only) | 0.517 |