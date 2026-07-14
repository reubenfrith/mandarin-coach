# Loom Video — Script & Recording Workflow

Target runtime: **9:00** (hard cap 10:00 — leave buffer for trimming slop).
Rubric: *"A 10-minute (OR LESS) loom video of a live demo of your application that also describes the use case."* — so the demo is the centrepiece; evals and architecture support it.

---

## Part A — Prep (do all of this BEFORE hitting record)

### A1. Warm the demo account (~15 min, do it an hour before)

The best moments of the demo — "drill me on my weak points", "how many 把 errors have I made?" — need a corpus with real history. A fresh account has nothing to show.

1. Log in to https://34-129-227-111.nip.io as your main demo user (e.g. `reuben`).
2. Submit these wrong sentences over a few turns (2–3 把 errors, plus a couple of other categories, so 把 is clearly the "most persistent" category):
   - `我把作业忘了带。` (把 error #1)
   - `他把门被关上了。` (把/被 error #2)
   - `我把这本书很喜欢。` (把 error #3)
   - `我昨天去了北京了了。` (aspect/了 error)
   - `我有三个书。` (measure word error)
3. Confirm each turn shows the "📝 logged to your error corpus" step.
4. Log out. **This doubles as the end-to-end smoke test of the deployment.**

### A2. Create the fresh account name (don't log in yet)

Pick an unused username (e.g. `demo`) — first login happens **on camera** to show onboarding. Verify beforehand it doesn't exist yet.

### A3. Pre-open browser tabs, in this order (you'll move left → right)

1. **App, logged out** — https://34-129-227-111.nip.io
2. **GitHub README, scrolled to the Infrastructure Diagram** (Task 2)
3. **GitHub `evals/results/head_to_head.md`** — the agent-vs-naked-LLM table
4. **GitHub README, scrolled to the Task 6 retrieval-sweep table** (§6.1)
5. **This script / paste-buffer doc** (see A4) — keep on a second monitor or off-screen

### A4. Paste-buffer doc (never type Chinese live)

Keep these in a plain-text doc, ready to copy one at a time:

```
她把书被他借走了。
我很喜欢吃的食物是饺子。
Why do I keep getting 把 wrong? How many times have I made that mistake?
Drill me on my weak points
```

### A5. Loom setup

- Screen + camera bubble (small, bottom-right), mic checked.
- Record the **browser window**, not the full desktop (hides the paste doc).
- Close notification apps. Hide bookmarks bar.
- **Latency plan:** a normal turn is 5–15 s. Narrate over the wait (see cues in the script — the wait is when you explain the tool calls). If a turn ever stalls past ~30 s, keep talking; the app falls back to GLM automatically — and that guard is itself a talking point. If something truly breaks, stop, fix, re-record — don't ship a broken take.
- Do **one full dry run** with a stopwatch before recording for real. If the dry run exceeds 9:00, cut section 5 (the drill) first — the counts answer in section 4 is the differentiator, the drill is garnish.

---

## Part B — The script

Times are cumulative targets. [SCREEN] = what's visible. Spoken lines are a guide — say it naturally, don't read.

### 1. The problem & the user — 0:00 → 0:50
[SCREEN] Tab 1: app login page.

> "Hi, I'm Reuben, and this is Mandarin Coach — a personal error-intelligence agent for self-directed Mandarin learners.
>
> Here's the problem. Intermediate learners — roughly HSK 2 to 4 — keep repeating the same handful of grammar mistakes month after month: 把-structures, aspect particles, measure words. These are exactly the errors that force native speakers to slow down and rephrase. Every tool they use today — Duolingo, Anki, a weekly tutor — corrects mistakes *in the moment* and then forgets them. Nobody keeps the longitudinal record. So nobody can say: *you've made this exact mistake nine times — let's fix it.*
>
> That's what this application does: it corrects you, explains the root cause, and — the part no existing tool does — logs every error into a private, growing corpus it can query, count, and trend."

### 2. First-time experience — 0:50 → 1:50
[SCREEN] Tab 1. Log in as the **fresh** `demo` account, on camera.

> "It runs in any browser, phone or laptop. Logging in for the first time…"

*(While onboarding loads)* Point at the HSK-level question and starter buttons.

> "New users get a one-question onboarding — your HSK level — and three starter prompts, so there's never a blank chat window. The username also namespaces the vector database, so every user's error corpus is fully isolated."

Don't interact further as `demo`. Log out.

### 3. The core loop: correction + logging — 1:50 → 3:40
[SCREEN] Tab 1. Log in as the **warm** account.

> "Now the account I've been using — and notice the difference: it greets me with a summary of *my* recent errors and offers to pick up where I left off."

Paste: `她把书被他借走了。`

*(Narrate during the ~10 s wait — this is scripted dead air):*

> "While it thinks: this sentence mixes 把, the disposal marker, with 被, the passive marker — a classic English-speaker error. Under the hood a LangGraph agent is deciding which of its five tools to call. Here it retrieves the actual grammar rule from a 315-document corpus using a hybrid BM25-plus-dense retriever, and pulls my own past 把 errors from my personal corpus."

When the answer renders, point at: the correction, the root-cause explanation, and **the "logged to your error corpus" step**.

> "Correction, the *why* — grounded in a retrieved rule, not the model's memory — and this last line is the whole product: the error was just written to my corpus as a structured record. Every mistake I make compounds into a profile of my weaknesses."

### 4. The differentiator: memory at scale — 3:40 → 5:10
[SCREEN] Tab 1.

Paste: `Why do I keep getting 把 wrong? How many times have I made that mistake?`

*(During the wait):*

> "This is the question no naked LLM can answer reliably, because it isn't a language question — it's a database question. The agent runs a deterministic count over ChromaDB rather than counting in its head."

When the answer renders, point at the exact count and trend.

> "Exact count, the contexts I made it in, and whether it's improving or persisting. In our evals, on corpora of 50 to 100 errors, the agent got this right ten out of ten times; a naked LLM with the same records pasted into its context miscounted."

### 5. Targeted practice — 5:10 → 6:10
[SCREEN] Tab 1.

Paste: `Drill me on my weak points`

*(During the wait):*

> "And it closes the loop: drills generated from *my* top error categories, using the retrieved grammar rule as the source of truth — not a generic exercise bank."

Show the exercises briefly. Move on — don't answer them.

### 6. Architecture in 45 seconds — 6:10 → 6:55
[SCREEN] Tab 2: infrastructure diagram.

> "The stack, quickly: Chainlit UI with password auth; a LangGraph tool-calling agent; LiteLLM routing through OpenRouter to Chinese-native models — DeepSeek V4 default with an automatic GLM fallback if it hangs; five tools including CC-CEDICT dictionary lookup and Tavily search; ChromaDB for both the reference corpora and each user's private error collection; LangSmith tracing every turn; deployed with Docker and Caddy on a GCP VM."

### 7. Evals: the evidence — 6:55 → 8:30
[SCREEN] Tab 3: head-to-head results table.

> "The claim 'this beats a naked LLM' is measured, not asserted. Sixty cases, every one run through both the full agent and a fair control — the same model, best-effort prompt, and for memory cases the user's raw error records pasted straight into its context.
>
> Three headlines. Stateless correction: the agent won 97 to 82 percent, because it retrieves the real rule before answering. At-scale aggregation — the core thesis — agent ten out of ten, naked LLM seven, and the agent's score is structural: it's an exact database aggregation, not counting in its head. And the hidden corpus-writer that logs errors after every turn: logging precision 1.00 — not a single clean sentence ever polluted the corpus.
>
> Every LLM-judged metric is paired with a deterministic cross-check, and where they disagree, the deterministic number wins."

[SCREEN] Tab 4: retrieval-sweep table.

> "For the improvement round I first had to fix my own eval — the original retrieval test was circular, queries copied from the rule documents themselves. On an honest, non-circular query set the baseline dropped to 49 percent recall-at-1, and a hybrid BM25-plus-dense retriever lifted that to 56 with MRR up from .63 to .70 — because Chinese grammar particles are exact-match signals dense embeddings underweight. That hybrid retriever is what's running in production, and the eval also drove a retry guard on the corpus-writer and a three-model bake-off that settled the default model on latency data."

### 8. Close — 8:30 → 9:00
[SCREEN] Tab 1 (the app).

> "Next steps: user file upload for Anki decks, cross-encoder reranking on the near-neighbour rules, and a topic-adherence guardrail the evals flagged. The repo has the full write-up — every number in it is reproducible from committed result files. Thanks for watching."

---

## Part C — After recording

1. Trim dead air in Loom (long waits you didn't narrate over, fumbles).
2. Confirm final length **< 10:00**.
3. Title: `Mandarin Coach — AI Makerspace Certification Demo (Reuben Frith)`.
4. Set link permissions to **anyone with the link can view**.
5. Add the Loom URL to the top of `README.md` (under the Submission line), commit, push.
6. Paste the URL into the submission Google Form.

## Timing summary

| Section | Ends at | Cut-first priority if over time |
|---|---|---|
| 1 Problem & user | 0:50 | keep |
| 2 Onboarding | 1:50 | trim to 30 s (2nd cut) |
| 3 Correction + logging | 3:40 | keep |
| 4 Counts at scale | 5:10 | keep — the differentiator |
| 5 Drill | 6:10 | **cut first** |
| 6 Architecture | 6:55 | keep, can compress |
| 7 Evals | 8:30 | compress to headlines (3rd cut) |
| 8 Close | 9:00 | keep |
