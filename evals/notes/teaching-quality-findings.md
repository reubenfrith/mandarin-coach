# Teaching-quality surface — findings (SLICE)

**What / why.** Every existing judge in the suite grades whether the coach is *right*
(`identifies_error` / `correct_fix` / `misleading` / voice `meets_expectation`). None grade
whether the reply *teaches* — the axis a learner actually feels. This slice probes whether that
axis is even *measurable* by an LLM judge before investing in a full surface. Two booleans:
`explains_why` (does it state the underlying rule, not just the fix?) and
`explanation_in_english` (is the explanation prose in the English-speaker's L1?).

**Set.** 13 cases: 9 real coach replies lifted verbatim from `results/head_to_head.json`
(A_stateless arm) + 4 hand-authored controls (fix-only floor · padded-empty length-probe ·
terse-with-rule · Chinese-fix-only). Judge = **gpt-4o** (independent of the deepseek coach).

## The honest result

The headline is **not** a coach score, and **not** the κ. Two things genuinely survive:

1. **Floor caught 3/3** — the judge does not default to "everything teaches"; fix-only,
   Chinese-only, and padded-but-empty replies were all flagged `explains_why=False`.
2. **Length-bias probe resisted** — a long, warm, rule-free reply scored `False` while its
   one-line twin that states the rule scored `True`. Verbosity/sycophancy (a named LLM-judge
   failure mode) did not fool it on this pair.

That retires the real *"maybe the model can't operationalize this axis at all"* risk. It is a
defensible feasibility result.

## What is NOT established (the trap we avoided)

κ vs the author's labels came out **+1.00 on both dims — and that number is CIRCULAR.** One
author wrote both the human labels *and* the judge's system prompt, from one rubric, in one
sitting; the prompt pre-answers every control. So κ measures *rubric self-consistency* ("does
the judge obey the instructions I wrote"), **not** whether the judge tracks an *independent*
human. A high κ here is expected and cheap, and is reported as such in the surface `.md`. This
is not merely "the cases are easy" — even hard cases would inflate, because the standard is not
independent of the instrument.

The `explanation_in_english=False` labels on the all-Chinese replies also encode a *contestable*
premise (a learner who writes full Chinese sentences may read Chinese fine) — exactly where a
second labeller could diverge.

## Decision

**Feasibility PASSES → the axis is worth building out**, but the reliability claim is **pending
the independent test**, which the slice ships but does not run:

- `--emit-blind` writes a blank sheet (real replies only, no author labels / no judge output).
- A second person (the user) labels blind.
- `--score-human` computes **judge-vs-blind-human κ** (the real number) plus **author-vs-human κ**
  (the ceiling the judge is chasing).

## Independent round — 2026-08-03

**First attempt failed instructively.** The first-time labeller graded the *learner's sentences*
(are they correct?) not the *coach's replies*, so there was nothing to score without fabricating
labels (declined). Fix: the blind sheet was rewritten with a "grade the COACH'S REPLY, not the
learner's sentence" banner + a 3-case worked example. Lesson retained: the labelling task is not
self-explanatory; the full surface needs this detail plus a labeller warm-up.

**Second attempt completed** (`results/teaching_quality_blind.json`, n=9 real replies):

| Dimension | judge vs blind-human κ | author vs blind-human κ |
|---|---|---|
| `explanation_in_english` | **+1.00** (100%) | +1.00 (100%) |
| `explains_why` | **0.00** (56%) | **0.00** (56%) |

Two non-circular findings, neither of which is "the judge works":

**1. `explains_why` is an under-defined construct — that is why κ collapsed, NOT judge
unreliability.** The tell: *author-vs-human κ is also 0*. Two humans disagree as much as the
judge does, so the dimension isn't pinned. Root cause: the judge prompt says "assume the
correction is correct; do not re-grade correctness," so judge + author read `explains_why` as
*"is a rule stated at all"* → all 9 pass. The blind human read it as *"is the why taught
**correctly**"* → False wherever a reply carries a wrong secondary claim. Both defensible; the
definition simply wasn't fixed. **Action for the full surface: split the axis into
`states_a_rule` (presence) and `misleading_secondary` (correctness of hints/drills/side-claims),
and drop the blanket "assume correct" instruction** — a learner reads the whole reply, not just
the headline fix.

**2. The blind human surfaced a real product defect no other surface catches.** All four
`explains_why=False` cases fail on a factual error in the coach's *supporting* content, not the
main correction:
- **A07** — hint claims cats take 个; they take 只 (两只猫).
- **A08** — lists 想 as unable to take 在; 想 ("think about / miss") takes 在 (我在想你).
- **A02** — asserts "一个句子只能选择其中一种结构"; the 被…把… co-occurrence exists (他被人把钱偷走了).
- **A06** — the summary table mislabels 你怎么来了这里.

**4 secondary errors in 9 replies.** `head_to_head` only judges the headline correction;
nothing in the suite inspects the hints/drills/side-claims the learner also reads. This is the
strongest argument for the surface: the coach's *auxiliary* teaching content has an error rate
worth measuring, and an expert human found it in ~5 minutes. A `misleading_secondary` dimension
(judge, verifiable against the corpus / a stronger model) is the highest-value next build.

## `misleading_secondary` built + evaluated 2026-08-03 (`results/teaching_secondary.{md,json}`)

Added `judge_secondary_errors` (gpt-4o), scored against the expert's blind labels as gold (gold
positive = the 4 replies the human failed on a wrong supporting claim). Result:

- **Recall 3/4** · **Precision 60%** (2 false alarms) · Cohen's κ **+0.34** (fair) vs the expert.

Per case, and it is the *content* of each flag that matters, not the boolean:

| id | expert | judge | right reason? |
|---|---|---|---|
| A07 (只 vs 个) | error | caught | ✅ exact — "猫 takes 只 not 个" |
| A08 (想 + 在) | error | caught | ✅ exact — "想 CAN take 在 (thinking about)" |
| A06 (table mislabel) | error | caught | ✅ same target (你怎么来了这里 / 了 placement) |
| A02 (被…把… overstated) | error | **MISSED** | the subtlest, most advanced point — human beat the judge |
| A01 | clean | **false alarm** | judge WRONG: claims 他把门打**开**了 needs 开开/开了; 打开 is the correct resultative |
| A14 | clean | **false alarm** | judge WRONG: claims two o'clock is 二点; it is 两点 (a *basic* error the coach + human got right) |

**The finding — the judge is a useful TRIAGE flagger, not a trustworthy ARBITER.** It found the
two well-known errors cleanly, but (a) missed the hardest true error (被…把… co-occurrence), and
(b) invented two errors of its own — one of them elementary (两点). The scary failure mode for an
autonomous correctness judge is not over-flagging trivia; it is *being wrong about the language*,
which it was, twice. So the shape of a real surface is:

- Use the judge to **surface candidates**, never to auto-decide. Recall-oriented (a spoken-aloud
  secondary error is the dangerous miss), with a human adjudicating the flags.
- To lift precision + catch the subtle misses, the next levers are a **stronger/reasoning judge
  model** and **corpus-grounding** the checkable claims (measure-word tables, aspect rules) rather
  than free-form judgement. A same-provider caveat also applies (gpt-4o judging; worth a
  cross-provider second opinion).
- **Product takeaway independent of the eval:** the coach emits real secondary errors (~4/9 here)
  in hints/drills/tables. Worth a prompt fix (e.g. "do not assert measure words or exception
  lists you are not certain of") regardless of how the surface matures.

## Prompt guard shipped + verified (directionally) 2026-08-03

Extended the coach's existing "do not guess pinyin/HSK" guard to measure words / "can-cannot"
exception lists / drill answers, in `AGENT_SYSTEM_PROMPT` and `VOICE_COACH_SYSTEM_PROMPT`. Then
re-generated the 4 affected replies **3× each** with the guard live (deepseek, clean provenance),
re-judged + eyeballed each for the specific known error:

| case | original error | with guard (3 samples) |
|---|---|---|
| A07 | 猫 takes 个 | **fixed 3/3** — all give 只 (table + drill answers) |
| A08 | 想 barred from 在 | **fixed 3/3** — 想 omitted, or correctly qualified ("when meaning want") |
| A02 | "把/被 never both" overstated | **not fixed 3/3** — still absolute (but a defensible beginner heuristic; out of the guard's scope) |
| A06 | table mislabels 你怎么来了这里 | **partial** — mislabel gone, but 了-placement still fumbled in ~1/3 |

**Honest limits of this verification:** it is NOT a clean A/B. The coach runs at temperature, so
each regenerated reply is entirely different *content* from the original — "the guard helped"
cannot be cleanly separated from "resampling produced different text," and n=3/case is
underpowered for a rate. Directional, not proof. A proper A/B (old prompt vs new, ≥5
samples/case, focused detector) followed — and **overturned the directional read**, see below.

## A/B with a control arm — 2026-08-03 — the directional claim above does NOT survive

Ran both arms: OLD prompt (pre-guard) vs NEW prompt (guard), 5 samples/case, same deepseek coach,
scored by a FOCUSED per-case detector (one yes/no about the specific known error — the open-ended
secondary judge was too noisy). Error-present rate (after correcting 2 detector false positives by
reading the replies):

| case | old (no guard) | new (guard) |
|---|---|---|
| A07 (猫→个) | 0/5 | 0/5 |
| A08 (想 barred from 在) | 0/5 | 1/5 |
| A02 (把/被 "never both") | 4/5 | 4/5 |
| A06 (了-placement) | 4/5 | 1/4 |
| **all** | ~8/20 | ~6/19 |

**The single-arm "fixed 3/3" was resampling noise, not the guard — retracted.** The control arm
shows the OLD prompt already gets A07 right 5/5 and A08 right ~5/5 on resampling: the original
head_to_head errors were **low-frequency (~1-in-5) samples, not systematic failures**, so
regenerating "cleared" them regardless of the guard. This is exactly the confound the earlier note
flagged; the A/B confirms it bites.

**Verdict on the guard:** no demonstrable effect at n=5. A02 unchanged (both overstate — and that
"error" is a defensible beginner heuristic anyway); A07/A08 unchanged (both already low-rate); only
A06 is suggestive (4/5→1/4) but has the smallest n, one timed-out run, and its status as an error
is itself contestable (你怎么来了这里 may be acceptable colloquial Mandarin). The dominant source of
variation is temperature, not the prompt. The guard is kept as cheap, harmless prompt hygiene that
*may* help at the margin, but the evidence does not show it measurably does — to detect an effect
this small you'd need much larger n.

**Methodology note (on-theme):** the focused detector beat the open-ended judge but still made ~2
false positives / 39 (a drill blank read as a claim; a correctly-qualified 想（认为）read as the
error) — even a narrowed LLM scorer needs a human read of the flags.

## For the full surface (deferred)

- Run the blind round with ≥2 labellers; report human–human κ as the ceiling.
- ~40+ **real** coach replies (not authored controls), including genuinely borderline ones.
- Add a **`grounded`** dimension: check the rule the coach cites against the *retrieved* corpus
  rule (deterministic-ish, RAGAS-faithfulness style) — omitted here to skip retrieval plumbing.
- Drive a **before/after**: two coach prompts, report the teaching-quality delta, gated on κ so
  the delta is believable. (This "is the surface *useful*" half was cut from the slice, which
  only answers "is the judge *feasible*".)
