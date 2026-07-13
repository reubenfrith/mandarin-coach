# Eval results — index & verification guide

Every eval surface writes **two files**: a `.md` (human summary) and a `.json`
(`{summary, rows}` — the aggregate PLUS one row per case with the **actual model answer
stored verbatim** and every per-case score). Nothing is a black box: each headline number
is re-derivable from the rows, and every scored answer is inspectable.

## Surfaces

| Surface | Measures | Summary | Raw (per-case) | n |
|---|---|---|---|---|
| **Head-to-head** | Agent vs naked-LLM control: correction accuracy, retrieval recall@3/MRR, personalisation, C_scale aggregation | `head_to_head.md` | `head_to_head.json` → `rows[].{agent,naked}` (incl. `.answer`) | 60 |
| **RAG (RAGAS)** | Retriever→grounding chain: ContextRecall/Relevance, Faithfulness, ResponseGroundedness, NoiseSensitivity, AnswerAccuracy + deterministic recall@3/MRR | `ragas_rag.md` | `ragas_rag.json` → `rows[].{response,ragas,recall_at_k,mrr,retrieved_ids}` | 40 |
| **Agentic (RAGAS)** | Tool-use over the LangGraph trace: ToolCallAccuracy + deterministic required-tool recall / extra-tool rate, AgentGoalAccuracy (completion), off-topic deflection | `ragas_agentic.md` | `ragas_agentic.json` → `rows[].{tool_sequence,tool_call_accuracy,required_recall,extra_tools,agent_goal_accuracy,final_answer}` + `off_topic[]` | 60 (+4 probes) |
| **Extraction** | The hidden post-turn corpus writer (`extract_and_log_error`): had_error precision/recall/F1, category accuracy (specific golds), correction validity — each miss split into omission / malformed-JSON / wrong-value | `extraction.md` | `extraction.json` → `rows[].{outcome,pred_had_error,pred_category,pred_correction,would_log,extraction_errored,category_correct,correction_valid,correction_how}` | 34 pos + 17 neg |
| **C_scale preflight** | Thesis check: can the agent aggregate at scale | `preflight_typec.md` | — | — |

## The audit model (why it's verifiable)

1. **Every scored answer is stored** — `rows[].answer` / `.response` / `.final_answer`. You
   can read exactly what the model produced for any case, not just its score.
2. **Every headline is a plain function of the rows** — the `.md` summaries are computed
   from `rows`; re-run the aggregation yourself and you get the same number (recipes below).
3. **Deterministic cross-checks anchor the LLM-judged metrics** — recall@k by exact rule-id
   match validates RAGAS ContextRecall; required-tool recall validates ToolCallAccuracy;
   `agg_parse` validates C_scale. Where an LLM judge proved unreliable it was demoted and the
   deterministic signal headlined (see `progress/DECISIONS.md #9–#12`).

## Verify a headline number yourself

```bash
# Agentic required-tool recall (headline 0.992) — re-derived from the raw rows
python3 -c "import json; r=json.load(open('evals/results/ragas_agentic.json'))['rows']; print(sum(x['required_recall'] for x in r)/len(r))"

# The single case that dips (B03 — tones case correctly used dictionary_lookup)
python3 -c "import json; [print(x['id'],x['tool_sequence'],x['required_recall']) for x in json.load(open('evals/results/ragas_agentic.json'))['rows'] if x['required_recall']<1]"

# RAG ContextRecall mean (headline 0.90)
python3 -c "import json; xs=[x['ragas']['ContextRecall'] for x in json.load(open('evals/results/ragas_rag.json'))['rows'] if x['ragas'].get('ContextRecall') is not None]; print(sum(xs)/len(xs))"

# Head-to-head C_scale aggregation (agent 10/10 vs naked 7/10)
python3 -c "import json; c=[x for x in json.load(open('evals/results/head_to_head.json'))['rows'] if x['type']=='C_scale']; print('agent',sum(x['agent']['aggregation_correct'] for x in c),'naked',sum(x['naked']['aggregation_correct'] for x in c),'of',len(c))"

# Extraction had_error confusion matrix (precision 1.00) — re-derived from rows
python3 -c "import json; r=json.load(open('evals/results/extraction.json'))['rows']; f=lambda o: sum(x['outcome']==o for x in r); tp,fp,fn=f('TP'),f('FP'),f('FN'); print('TP',tp,'FP',fp,'FN',fn,'TN',f('TN'),'| precision',tp/(tp+fp),'recall',round(tp/(tp+fn),3))"

# The extraction defect (run-variable: glm drops correction on a chunk of logged records)
python3 -c "import json; r=json.load(open('evals/results/extraction.json'))['rows']; L=[x for x in r if x['kind']=='positive' and x['would_log']]; print(sum(1 for x in L if not (x['pred_correction'] or '').strip()),'of',len(L),'logged records have an empty correction (varies per run)')"
```

## Read the actual answer for any case

```bash
# What the agent actually said for agentic case A02
python3 -c "import json; print(next(x['final_answer'] for x in json.load(open('evals/results/ragas_agentic.json'))['rows'] if x['id']=='A02'))"

# Agent vs naked answer for head-to-head case C01
python3 -c "import json; r=next(x for x in json.load(open('evals/results/head_to_head.json'))['rows'] if x['id']=='C01'); print('AGENT:\n',r['agent']['answer'],'\n\nNAKED:\n',r['naked']['answer'])"
```

## Reproduce a whole surface

```bash
uv run python evals/surfaces/eval_harness.py                                  # head-to-head (60)
uv run python evals/surfaces/ragas_rag.py                                     # RAG surface (40)
REQUEST_TIMEOUT=150 EVAL_CONCURRENCY=3 uv run python evals/surfaces/ragas_agentic.py   # agentic (60 + probes)
```

Runs are reproducible: eval generation uses `glm` (deepseek hangs — DECISIONS #4), judges
run at temperature 0, and the dataset is deterministic (`test_dataset.json`, built by
`generate_dataset.py`). LLM-judged metrics still carry small run-to-run noise — the
deterministic cross-checks are the stable anchors.
