# Mandarin Coach — presentation script

Speaker notes for the [pitch deck](../). One section per slide. Timings are a rough
budget (~9–13 min total); the slides carry the visuals, this carries the words.

---

## 0 · Cover — *Correct. Explain. Remember.* (~20s)

> "This is Mandarin Coach. Three words describe the whole product: it **corrects**
> what you say, **explains** the root cause, and — the part nothing else does —
> **remembers** it. It's live, deployed end-to-end, with three surfaces: chat,
> voice, and pronunciation."

The four curves are the four Mandarin tones — that pitch-contour idea comes back in
the demo, because tone is something the app actually measures.

---

## 1 · Why Chinese? — *the hook* (~45s)

**Open with your own reason — make it personal.** This is the cold open; it earns the
audience before you've shown a single feature.

> "Nobody learns Chinese by accident. Everyone starts for a reason — mine is a love
> story. Yours might be a job at a Chinese AI lab, or family, or a move to Shanghai."

Then the universal turn — this is the whole setup for everything after:

> "But whatever the reason, the path is the same. You push past 你好, past the first
> few hundred words… and then you hit the **intermediate plateau**. The place where
> language learning goes to die. Me, and most learners, get stuck right here."

Note: the "me and most learners get stuck here" line quietly introduces the audience,
so slide 3 just sharpens it. Keep this slide short and human — no numbers yet.

---

## 2 · Problem — *Every correction evaporates* (1–2 min)

> "Intermediate learners — roughly HSK 2 to 4 — keep making the same handful of
> mistakes for **months**. Misordered clauses, the wrong measure word, misusing
> 了, 把, 过."

> "The tools all correct you *in the moment*: Duolingo flags a wrong answer, a tutor
> fixes it in session, a language partner rephrases. Then the session ends and the
> correction is **gone**. Nothing keeps a record."

Land the line: **no tool today can say "you've made this exact mistake nine times —
let's drill it."** So learners re-study what they already know while the errors that
actually block fluency go unmeasured.

---

## 3 · Audience — *The intermediate plateau* (1–2 min)

> "Adult English speakers teaching themselves, stuck at the intermediate plateau.
> They can build sentences and hold a slow conversation — but at natural speed a
> native speaker has to strain to follow them, and they can't see *which* recurring
> errors are causing it."

The scope insight worth saying aloud: **those errors are identical in speech and in
writing** — so a text-first tool can track and trend them.

> "They already patch it with Duolingo, Anki, YouTube, the odd iTalki tutor. Every
> one of those shares the same gap: no persistent error log, no adaptation to the
> individual, and nothing guiding them *between* sessions."

The stats strip gives the plateau some weight — hit one or two, don't read all three:

- **2,200 hours** — the FSI's estimate to reach professional proficiency in Mandarin,
  its hardest tier. This is a *long* road, which is why the middle of it is where
  people stall.
- **B1–B2** — the intermediate band is the single most-documented plateau in
  second-language-acquisition research (Richards, *Moving Beyond the Plateau*, 2008).
- **~48%** — roughly half of app learners quit before they even reach intermediate.

Provenance note (for you, not the slide): the 2,200-hour FSI figure is rock-solid;
the plateau-at-B1–B2 is well-established in SLA literature; the ~48% dropout is from
industry / app-learning summaries, so it carries a "~" — treat it as indicative, not
precise, and the on-slide source line says as much.

---

## 4 · Solution — *Three coaches, one corpus* (2 min)

> "The answer is a browser agent with three surfaces that all feed **one** private
> error corpus."

- **Text** — a LangGraph agent with five tools; corrects, grounds the "why" in a
  real grammar rule, and silently logs each mistake.
- **Voice** — free-form spoken Mandarin; an intent router flips to an English
  *coaching* answer the second you ask "why was that wrong?"
- **Pronounce** — compose-and-correct, then say-and-score: a per-syllable tone
  verdict from real pitch analysis (pYIN + DTW), no speech-recognition guesswork.

Then the "why an agent, not just a model" beat:

> "A frontier model already fixes an isolated sentence well — so on one-off
> corrections we *assumed parity*. The build earns its keep on three things a model
> can't do even with your history in its context: **grounded facts** it looks up
> instead of hallucinating, **exact aggregation** over your corpus, and being
> **proactive** — it opens on your weakest area and the value compounds with use."

---

## 5 · Demo — *The correction that remembers* (2–4 min)

Play the screen-recording embedded on the slide and narrate over it (fallback: the
live app at **34-129-227-111.nip.io**). Talk through these beats in order:

- **A — Text-coach correction.** Submit `她把书被他借走了`. Point out the coach catches the
  把/被 conflict, fixes it, explains disposal vs. passive — and files the error.
- **B — The memory payoff.** Ask "how many 把 errors have I made?" It returns an
  **exact count and trend** — computed over the corpus, not estimated. *This is the
  moment the whole pitch lands.*
- **C — Voice.** Speak a Mandarin sentence, get a spoken reply, then ask "why was
  that wrong?" — watch it switch to English coaching mid-conversation.
- **D — Pronounce.** Say `妈`. Show the pitch-contour overlay and the per-syllable
  tone verdict.

If you only have time for one thing: **do A and B.** That's the differentiator.

---

## 6 · Infrastructure — *One VM, one process, one corpus* (1–2 min)

The diagram is three colour-coded flows — Text (red), Voice (gold), Pronounce
(green) — all entering through one FastAPI process and all writing to one corpus.
Trace the three, then land the punchline.

> "Everything runs in a single process on one always-on VM, and auth namespaces
> each learner's corpus. From there the three surfaces split: **Text** runs the
> LangGraph agent — five tools and the hybrid retriever — over the OpenRouter models.
> **Voice** is its own low-latency chain: speech-to-text, an intent router, the
> conversation-or-coach brain, streamed speech back — all on OpenAI. **Pronounce**
> is the odd one out: two passes, and the scoring pass is **pure DSP — pitch analysis
> with no model at all**, for the reason we covered earlier."

> "But follow all three lines down and they converge on the same box: **one shared
> corpus**. That's the whole point — a mistake you make out loud in voice practice
> and a mistake you type in chat land in the same place."

Two rationale lines if asked:

- **Why a VM, not serverless:** ChromaDB is SQLite-backed and needs a real
  filesystem; always-on means no cold starts, and the corpus sits on a persistent
  disk that survives the VM.
- **Why LiteLLM + OpenRouter:** three Chinese-leaderboard models behind one key,
  swappable with zero code change.

---

## 7 · Evals — *Does it actually work?* (1 min)

The closing proof, right before you wrap. Be honest up front: this is a working
prototype, not a business with users, so "success" means an **eval harness** that
proves each piece does what it claims. The slide reads left to right — **what we
measured, what was good, what was honestly weak.** The third column is the one that
buys you credibility; don't skip it.

**What we measured** (one line): corrections against a naked LLM, retrieval, the
memory-writer, tool use, voice routing, and tone scoring — a surface per subsystem.

**What was good** — linger on the first, it's the whole thesis:

- **10/10 vs 7/10** — remembering at scale. A naked LLM given every advantage (same
  model, your records pasted in) still loses, because counting dozens of records is a
  database job, not a language job.
- **97% vs 82%** correct fixes, zero misleading; **1.00** logging precision (text and
  tone); the right tool called **99%** of the time.

**What was honestly weak** — say these plainly, it lands better than pretending:

- On *one-off* corrections the agent is ≈ a plain LLM — the edge is the memory, not
  the individual fix (we measured that parity on purpose).
- Tone scoring hit 1.00 precision, but only on clean **synthetic** audio — real
  learner speech is untested.
- It declines only **2 of 4** off-topic questions — the topic guardrail is thin.
- Retrieval still misses at rank-1 on look-alikes (的 / 得 / 地).

Close on the discipline line: **every judged number is paired with a deterministic
cross-check, and when they disagree, the deterministic one wins.**

---

## 8 · Conclusions — *Lessons learnt, and what's next* (1–2 min)

Frame it as lessons, not a victory lap — it's more honest and more memorable.

**Lessons learnt:**

- **A judge you can't cross-check isn't evidence.** The single biggest methodological
  lesson — every LLM-judged number is paired with a deterministic check, and the
  deterministic one wins.
- **Measure the differentiator, not the easy part.** A naked-LLM control arm showed
  one-off corrections are parity; the value — and the eval that matters — is memory
  at scale.
- **Fix the source, not the reply.** The coach's wrong corrections traced back to
  over-broad rules in the corpus; fixing the *data* fixed every downstream answer.
- **Not everything should be AI.** Tone scoring is pure signal processing precisely
  because speech-to-text hears what you *meant*, not what you *said*.

**What's next** (each tied to something above):

- User file upload — .txt and Anki decks (the one deferred data feature).
- Cross-encoder reranking for the rank-1 look-alike misses.
- Realtime voice, and tone scoring validated on real learner audio (not synthetic).
- A topic-adherence guardrail — closes the "declines only 2 of 4" gap from the evals.

Close on the three words: **"Correct. Explain. Remember." 谢谢。**

---

### Q&A — likely questions

- **"Isn't this just GPT with a prompt?"** → On single corrections, roughly yes, and
  we measured that parity honestly. The value is memory + exact aggregation + grounded
  lookups — the head-to-head 10/10 vs 7/10 is the proof.
- **"How do you trust the auto-logged errors?"** → 1.00 logging precision, plus a
  retry/validation guard that discards incomplete records rather than poison the corpus.
- **"Why DeepSeek?"** → Bake-off: quality tied across three models, DeepSeek had the
  tightest latency (p95 13.4s); GLM is the fallback behind a turn-timeout guard.
- **"What about tone scoring accuracy?"** → It's pure DSP on synthetic-labelled audio
  today — an upper bound; validation on real L2 recordings is the next step.
