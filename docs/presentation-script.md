# Mandarin Coach — presentation script

Speaker notes for the [pitch deck](../). One section per slide. Timings are a rough
budget (~9–13 min total); the slides carry the visuals, this carries the words.

---

## 0 · Cover — *Correct. Explain. Remember.* (~20s)

> Ni hao wo de mingzi Reuben - hi my name is Reuben and this is mandarin coach. A coach that corrects what you say, explains the root cause, and remembers it.

---

## 1 · Why Chinese? — *the hook* (~45s)

> But why learn chinese - nobody learns it by accident.
> Mine is a love story - my wife is chinese and I want to chat with her family and enjoy yummy food and her culture. 
> But yours might be going to china for a holiday or joining a chinese AI research lab.
> Whatever the reason, the path is the same.
> You push past 你好, past the first
> few hundred words… and then you hit the **intermediate plateau**. 

---

## 2 · The plateau — *the problem* (1–2 min)

> The intermediate plateau is the place where language learning goes to die.  learners get stuck right here — it is a well-documented stall in language learning — we keep making the same handful of mistakes. Misordered clauses, the wrong measure word, misusing tenses.

> There are already a lot of language learning apps out there but they all correct you *in the moment* none of them say "you've made this exact mistake 9 times lets practice it"
> Duolingo flags a wrong answer, a tutor fixes it in session, a language partner rephrases. Then the session ends and the correction is **gone**.
> Mandarin's a hard language where it takes roughly 2200 hours to reach professional proficiency, so the quicker someone can move through the intermediate level the better.

---

## 4 · Solution — *Three coaches, one corpus* (2 min)

> Incomes mandarin coach to save the day it is a browser agent with three surfaces that all feed **one** private error corpus.

- **Text** — an agent with five tools; it corrects, grounds the "why" in a
  real grammar rule and expected vocabulary, and logs each mistake.
- **Voice** — which allows for free-form spoken Mandarin as well as a coaching answer to help you learn as you go;
- **Pronounce** — practices your tones and gives a per-syllable tone
  verdict from real pitch analysis (pYIN + DTW), no speech-recognition guesswork.

---

## 5 · Demo — *The correction that remembers* (2–4 min)

Lets jump into mandarin coach,

Text-coach correction: 
wo you liang ge mao - 我有两个猫 is this correct ?
wo qu zou tian - 我去昨天 is this correct ? 

Voice-coach correction:
Wo xiang he kafei - 我想喝咖啡 
How to say this more politely ?

Pronounce:
Wo xiang he kafei - 我想喝咖啡

---

## 6 · Infrastructure (1–2 min)

The diagram is three colour-coded flows — Text (red), Voice (gold), Pronounce
(green) — all entering through one FastAPI process and all writing to one corpus.
Trace the three, then land the punchline.

> Text
> "The text coach is a LangGraph agent with five tools and a hybrid retriever. It
> runs over OpenRouter models - it has a primary model of Deep Seek v4 flash, the CC-CEDICT dictionary, a grammar-rule corpus,
> and a web-search tool. It extracts each error and logs it to your corpus."
> For this I focused on using models that are strong on Chinese, and I wanted to be able to swap them out with zero code change. So I used LiteLLM + OpenRouter, which lets me use three different Chinese-leaderboard models behind one key. I have deepseek-v4-flash as the primary with glm as a fallback behind a turn-timeout guard. 

> Voice
> "The voice coach is a free-form spoken conversation partner that speaks Mandarin as well as a coaching brain that switches to English when you ask a learning question. It runs on OpenAI's models and has a low-latency chain: speech-to-text, an intent router, the conversation-or-coach brain, and streamed speech back." This uses openai's models for the voice coach because they are strong on Chinese and have a low-latency chain: speech-to-text, an intent router, the conversation-or-coach brain, and streamed speech back.

> Pronounce
>  "The pronunciation coach is a two-pass tone coach: It analyses the raw audio of your voice directly — measuring how your pitch moves across each syllable and comparing that curve to the correct tone shape — to give a per-syllable tone verdict and a curve overlay. There's no AI model involved at all." This is because text to speech models are trained to hear what you *meant* to say, not what you actually *said* - they are designed to be forgiving, so I wanted a pure signal processing approach to tone scoring.

---

## 7 · Evals — *Does it actually work?* (1 min)

Evals helps us say is it working and back it up with numbers. 

One of the core questions is - "Is this actually better than just using a naked LLM like ChatGPT?" 
With one-off corrections and questions the naked-LLM control and Mandarin Coach were similar, however the differentiation happens when we start having longer conversations at scale and want to track our mistakes. Mandarin Coach earns its keep on three things a model
can't do even with your history in its context: **grounded facts** it looks up
instead of hallucinating, **exact aggregation** over your corpus, and being
**proactive** — it opens on your weakest area and the value compounds with use. Our agent is grounded in facts and has a memory that allows us to track mistakes over time.

Some other things we measured were the retrieval, the memory-writer, tool use, voice routing — most surfaces had some kind of metric to ensure good performance.

Additionally where we had LLMs judging for correctness we paired that with a deterministic cross-check, and when they disagreed, the deterministic one won. This is because a judge you can't cross-check isn't evidence.

---

## 8 · Conclusions — *Lessons learnt, and what's next* (1–2 min)

Frame it as lessons, not a victory lap — it's more honest and more memorable.

**Lessons learnt:**

- **tools are the differentiator.** The LLM is a commodity; the value is in the tools, the memory, and the grounded lookups.
- **Build in fallbacks** Relying on a single model is a risk; we built in a fallback behind a turn-timeout guard.
- **Not everything should be AI.** Tone scoring is pure signal processing precisely
  because speech-to-text hears what you *meant*, not what you *said*.

**What's next** (each tied to something above):

- User file upload — .txt and Anki decks (the one deferred data feature).
- Realtime voice, and tone scoring validated on real learner audio.
- A topic-adherence guardrail — closes the "declines only 2 of 4" gap from the evals.

That's Mandarin Coach: Thanks for your time - xiexie 谢谢。

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
