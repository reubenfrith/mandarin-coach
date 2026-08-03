# Teaching-quality eval — SLICE (judge feasibility)

13 cases (9 real coach replies + 4 authored controls); judge = **gpt-4o** (independent of the deepseek coach, temp 0). A **feasibility slice**: can an LLM judge even operationalize a teaching-quality rubric, or does it default to "everything teaches" / get fooled by verbosity? What it does NOT establish is whether the judge tracks an *independent* human — see the ⚠️ below and run the blind-label round for that.

> ⚠️ **The κ below is CIRCULAR — read it as rubric self-consistency, not validation.** The same author wrote both the human labels *and* the judge's system prompt, from one rubric, in one sitting; the prompt pre-answers every control. So κ measures "does the judge obey the instructions I wrote," not "does the judge's judgment match an independent human's." A high κ here is expected and cheap. The independent number comes from `--emit-blind` → you label blind → `--score-human`.

## 1. What genuinely survives the circularity

These retire a real *"maybe the model can't do this at all"* risk, because they don't depend on the judge agreeing with a standard the judge authored:

- **Floor caught: 3/3** — the judge does not default to "everything teaches" (fix-only / Chinese-only / padded-empty all flagged `explains_why=False`).
- **Length-bias probe: resisted** — a long, warm, rule-free reply scored `explains_why=False` while its one-line twin that states the rule scored `True`. Verbosity/sycophancy (a named LLM-judge failure mode) did not fool it on this pair.

## 2. Rubric self-consistency (CIRCULAR — not validation) — judge vs. author labels

| Dimension | Cohen's κ | Agreement | Judge vs author (as truth) | Disagreements |
|---|---|---|---|---|
| `explains_why` | **+1.00** (almost perfect) | 100% (13/13) | fp 0 · fn 0 (tp 10, tn 3) | — |
| `explanation_in_english` | **+1.00** (almost perfect) | 100% (13/13) | fp 0 · fn 0 (tp 7, tn 6) | — |

_These numbers are self-referential (see ⚠️). `fp` = judge over-credited teaching the author didn't; `fn` = judge missed teaching the author credited. Zero disagreements ≠ a reliable judge — it means the rubric is internally consistent._

## 3. The independent test (not yet run) — blind-label round

The only way to retire the real risk is a standard the judge did **not** author: a human labels the real replies blind (no judge output shown), then κ is computed judge-vs-that-human, plus human-vs-author κ as the ceiling the judge is chasing. Run:

```
uv run python evals/surfaces/text_coach/teaching_quality_eval.py --emit-blind    # writes a blank sheet
#  … fill in results/teaching_blind_labels.json (true/false per dim) …
uv run python evals/surfaces/text_coach/teaching_quality_eval.py --score-human results/teaching_blind_labels.json
```

## Per-case

| id | role | author why/en | judge why/en | agree | judge reason |
|---|---|---|---|---|---|
| A01 | real | ✓/✓ | ✓/✓ | ✅ | The reply clearly explains the rule of the 把 construction, why the learner's sentence is i |
| A02 | real | ✓/✗ | ✓/✗ | ✅ | The reply explains the rule about not mixing 把 and 被 in a single sentence, but the explana |
| A05 | real | ✓/✓ | ✓/✓ | ✅ | The reply clearly explains the difference between 了 and 过, providing the underlying rule a |
| A07 | real | ✓/✗ | ✓/✗ | ✅ | The reply explains the rule about using measure words between numbers and nouns, but the e |
| A08 | real | ✓/✗ | ✓/✗ | ✅ | The reply explains the rule about stative verbs not taking '在' for ongoing actions, but th |
| A10 | real | ✓/✓ | ✓/✓ | ✅ | The coach clearly explains the rule for using 的 and 地, specifying their grammatical functi |
| A11 | real | ✓/✓ | ✓/✓ | ✅ | The reply clearly explains the rule about not using 很 in 比 comparisons and provides exampl |
| A14 | real | ✓/✗ | ✓/✗ | ✅ | The reply explains the rule about when to use '两' versus '二', but the explanation is subst |
| A06 | real | ✓/✗ | ✓/✗ | ✅ | The reply explains the rule about using 是……的 for completed actions to emphasize means, but |
| C1_fix_only | control | ✗/✓ | ✗/✓ | ✅ | The reply provides the correct sentence but does not explain the rule that the 把 construct |
| C2a_padded_empty | control | ✗/✓ | ✗/✓ | ✅ | The reply does not explain the underlying rule about why '很' is incorrect in a 比 compariso |
| C2b_terse_why | control | ✓/✓ | ✓/✓ | ✅ | The reply explains the rule that '比' already implies 'more', so '很' is unnecessary, and it |
| C3_cn_fix_only | control | ✗/✗ | ✗/✗ | ✅ | The reply only provides the corrected sentence without explaining the rule or principle, a |

## Caveats (read before quoting κ)

- **The κ is CIRCULAR — it is not validation.** One author wrote the labels AND the judge prompt from one rubric; the prompt pre-answers the controls. So κ measures rubric self-consistency, not whether the judge matches an *independent* human. This is not merely "easy cases" — even hard cases would inflate, because the standard isn't independent of the instrument. The `--emit-blind` round fixes exactly this.
- **`explanation_in_english=False` on the all-Chinese replies encodes a contestable premise** — a learner who writes full Chinese sentences may read Chinese explanations fine. This is precisely the kind of judgement a second (blind) labeller might overturn; don't treat it as settled.
- **n=13, single author labeller.** κ here is directional. A real surface needs ≥2 labellers (human–human κ = the ceiling the judge is chasing) and ~40+ real cases.
- **The real coach is consistently strong on `explains_why`** (all 8 real replies explain the why), so that dimension's variance comes almost entirely from the controls. `explanation_in_english` has real variance among the real replies and is the more informative dimension here.
- **`grounded` is deferred.** The full surface would add a (deterministic-ish) check that the rule the coach cites actually matches the retrieved corpus rule — omitted from the slice to avoid the retrieval plumbing.
- **Judge is gpt-4o (OpenAI).** Same-provider self-preference isn't a risk here (the coach is deepseek), but a second judge model would still be worth adding to measure judge–judge stability.
