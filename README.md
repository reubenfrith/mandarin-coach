# Certification Challenge Submission
**Student:** Reuben Frith  
**Due:** Thursday, 16 July 2026, 7 pm ET  
**Submission:** Google Form — https://forms.gle/xtM9F38nfRKcdjH97  
**Project:** Mandarin Learning Coach — Personal Error Intelligence Agent

---

## Task 1: Problem, Audience & Scope

### Problem Statement

Lower-intermediate self-directed Mandarin learners (roughly HSK 2–4) keep repeating the same specific grammar and word-choice mistakes month after month, and those persistent errors are exactly what force native speakers to slow down, repeat, and rephrase in order to understand them. They can already hold a slow conversation and know the vocabulary and rules in theory, but the same handful of errors resurface unnoticed whether they are typing or speaking, so their progress toward being easily understood stalls.

### Why This Is a Problem

**Who has the problem?**  
Adult English speakers past the beginner stage — roughly HSK 2–4 — learning Mandarin independently with apps like Duolingo or HelloChinese, Anki decks, and occasional iTalki tutors, without the structure of a formal classroom. This learner is over the first hump: they can build sentences, read with effort, and sustain a slow, cooperative conversation. The moment that exposes the problem is talking with a native speaker at natural speed — the learner hesitates, misorders clauses, reaches for the wrong measure word, misuses aspect markers like 了 and 过, and the native has to visibly work to follow them. The learner feels the strain but cannot see which specific, recurring errors are causing it. They have real motivation and invest real time, but no systematic support for isolating and fixing their individual weaknesses.

**What are they trying to do?**  
Break out of the intermediate plateau and reach the point where a native speaker no longer has to strain to understand them — genuine conversational fluency. Mandarin is one of the hardest languages for English speakers, requiring simultaneous mastery of tones, characters, grammar patterns, and cultural register. Critically, the errors that make them hard to understand out loud are the same grammar and word-choice errors they make in writing — which is exactly where a tool can catch, track, and trend them. Progress is slow and error-prone, and the learner depends on targeted feedback, not more generic curriculum, to improve.

**How do they handle it today?**  
Learners cobble together a toolbox: Duolingo or HelloChinese for vocabulary drills, Anki for flashcard review, occasional iTalki tutor sessions for conversation practice, YouTube for grammar explanations, and Google Translate for ad hoc lookups. When they make a mistake, a tutor corrects them in the moment or an app flags a wrong answer. The correction is ephemeral — it lives in the session and is never systematically captured.

**Why isn't that good enough?**  
Every tool treats the learner as an average user progressing through a fixed curriculum. None build a model of the individual learner's specific error patterns. A tutor who meets you once a week has no longitudinal view of your mistakes across hundreds of practice sentences. Duolingo's algorithm optimises for engagement, not for targeting your persistent weaknesses. The result: learners spend time reinforcing things they already know while the errors that will actually hold back their fluency go unaddressed. There is no tool today that can say "you have made this exact mistake nine times — let us fix it now."

---

### Current Workflow Diagram

How a self-directed Mandarin learner handles their study today:

```
[Learner] 
    │
    ▼
Open study tool (Duolingo / textbook / YouTube)
    │
    ▼
Follow generic curriculum ──────────────────────► [Pain point: not adapted to individual]
    │
    ▼
Attempt to write or speak a sentence
    │
    ▼
Error occurs
    │
    ├──► App flags wrong answer (Duolingo)
    ├──► Tutor corrects in session (iTalki) ─────► [Pain point: infrequent, expensive]
    └──► Native speaker corrects (HelloTalk)
    │
    ▼
Learner notes correction ───────────────────────► [Pain point: notebook or mental note only]
    │
    ▼
Session ends
    │
    ▼
Errors NOT captured anywhere persistent ─────────► [Pain point: lost between sessions]
    │
    ▼
Next session: same curriculum continues
    │
    ▼
Same errors recur ───────────────────────────────► [Pain point: no feedback loop]
```

**Tools the learner interacts with today:**
- Duolingo / HelloChinese (mobile, generic curriculum)
- Anki (flashcard review, generic or self-made decks)
- iTalki (tutor marketplace, infrequent sessions)
- YouTube (grammar explanations, passive consumption)
- Google Translate (ad hoc word lookup)
- Physical notebook (manual, inconsistent error logging)

**Where the workflow breaks down:**
1. No persistent error log across any tool
2. Generic curriculum not adapted to the individual's weaknesses
3. Corrections are ephemeral — lost between sessions
4. No visibility into which errors are most frequent or recurring
5. The gap between tutor sessions is entirely unguided

---

### Evaluation Q&A Pairs

Input/output pairs used to evaluate application performance:

| # | User Input | Expected Output |
|---|---|---|
| 1 | `我昨天去了商店买了一些苹果。` | No errors. Agent confirms correct usage of 了 and suggests a related drill. |
| 2 | `她把书被他借走了。` | Agent identifies 把/被 conflict. Explains disposal vs. passive. Logs error. Offers targeted drill. |
| 3 | `我很喜欢吃的食物是饺子。` | Agent flags awkward structure. Suggests `我最喜欢吃的食物是饺子`. Explains why. |
| 4 | `请帮我找一个关于天气的单词` | Agent calls dictionary API. Returns weather vocabulary with pinyin and example sentences. |
| 5 | `Drill me on my weak points` | Agent retrieves top 3 error categories from memory. Generates targeted exercises for each. |
| 6 | `Why do I keep getting 把 wrong?` | Agent retrieves error history. Surfaces how many times and in what context. Explains rule. |
| 7 | `我明天将去北京` | Grammatically correct but agent notes 将 is formal/written register. Suggests 要 for natural speech. |
| 8 | `What's the difference between 看 and 看看?` | Grammar explanation with examples. No dictionary API call needed. |
| 9 | `Drill me on tones` | Agent retrieves tone-related errors from memory. Generates tone discrimination exercises. |
| 10 | `我没有去过中国但是我想去。` | No errors. Agent confirms and offers cultural context or vocabulary expansion. |

---

## Task 2: Proposed Solution

### Solution Statement

A personal Mandarin coaching agent that accepts user-submitted text, identifies errors by reasoning over a structured personal error corpus and a curated reference knowledge base, returns pattern-level corrections with root cause explanations, logs every mistake to a growing private corpus, and uses LiteLLM and OpenRouter to experimentally compare three models selected from Chinese language benchmarks — DeepSeek V4, GLM-5.2, and Qwen3.5-397B — to select the best model for this specific bilingual task with evidence rather than assumption.

---

### How This Beats a Naked LLM

This is the central claim of the project, so it is stated precisely and — critically — it is **measured head-to-head in Task 5 rather than asserted.**

**First, an honest concession.** A naked frontier LLM (Claude or GPT, even with its built-in memory) is already excellent at correcting a single Mandarin sentence and explaining the error in English. On isolated, stateless corrections this system is at *parity* with the base model, because it is the base model plus scaffolding. The differentiation is therefore **not** "better grammar explanations." Staking the argument there would lose the head-to-head — a strong LLM knows Mandarin grammar cold.

**The baseline is the strongest fair version, not a strawman.** The obvious attack on any "we beat a naked LLM" claim is: *"You crippled the baseline — paste the history into context and it does fine."* So the control arm is the same model, a best-effort prompt, and for memory cases the user's **raw error records handed directly into its context.** Beating an amnesiac model proves nothing; the win only counts against a model that has been given everything.

Against that fair baseline, the advantage is three things a naked LLM structurally cannot do:

**1. Factual grounding — no hallucinated pinyin, tone marks, or HSK levels.**  
LLMs routinely emit a wrong tone mark, a plausible-but-wrong pinyin, or an incorrect HSK level. These are objective facts with a ground truth. The agent looks them up via the CC-CEDICT and HSK word-list tools instead of guessing. This is cleanly testable and shows up **even on the "stateless parity" cases** — turning near-parity into a visible, factual win.

**2. Deterministic aggregation and trending over a growing corpus.**  
This is the core moat, and it only reveals itself **at scale.** Ask a naked LLM "how many 把 errors have I made and is it getting worse?" with five records in context and it answers fine. Give it sixty records across mixed categories and it miscounts, mis-orders the trend, or overflows its context budget — because counting and trending across a large structured record is a *database operation*, not a language operation. ChromaDB does it exactly, cheaply, and indefinitely. This is the difference between a sticky note and a queryable medical record — a GP who jots a note after each visit versus a specialist keeping a structured, trendable record across every encounter.

**3. Proactive, compounding coaching rather than reactive answering.**  
A naked LLM waits to be asked. This agent opens a session by surfacing the user's most persistent error category, offers a drill built from that specific pattern, and logs each new error back to the corpus so the next session starts sharper. The value **compounds**: the more the plateau learner uses it, the more precisely it targets the exact invisible errors that make natives strain to understand them.

**The gaps at a glance:**

| Capability | Naked LLM (even with memory, records in context) | This Application |
|---|---|---|
| Factual lookup | Hallucinates pinyin, tone marks, HSK level | Grounded via CC-CEDICT + HSK tools |
| Error storage | Unstructured text summary | Structured records: category, count, context, timestamp |
| Retrieval | Flat recall over what fits in context | Vector similarity search across the full corpus |
| Aggregation at scale | Miscounts / mis-trends / overflows past ~dozens of records | Exact counts and trends, unbounded |
| Reference knowledge | Training data only | RAG over HSK corpus, grammar rules, L1-specific error archetypes |
| Data ownership | Locked to provider's servers | Your corpus, your deployment, fully portable |

**Why the personalisation metric is not circular.** A fair objection is "you invented a metric only your system can pass." It is not arbitrary: the plateau learner's *entire* problem — established in the audience section — is that their persistent, recurring errors are invisible to them. Measuring whether a response explicitly identifies and targets those recurring errors *is* measuring whether the tool solves the stated problem. The metric is the operationalisation of the persona, not a bar built to flatter the system.

---

### What This Application Does Not Do (v1 Scope)

This version focuses on text-based interaction only. Voice input, pronunciation correction, and tone recognition are post-v1 features. This is a deliberate design choice, not a gap: the errors that make an intermediate learner hard to understand in live conversation — wrong aspect marker, broken 把-structure, awkward word order, wrong measure word — are the same grammar and word-choice errors they make in text. Text is where the learner has time to reflect and where the tool can track and trend the pattern over time. The core value — longitudinal error intelligence — is fully delivered through typed chat while directly targeting the spoken-fluency plateau.

---

### Model Selection Research

All model choices are based on benchmarks specific to Chinese language tasks, not general popularity. The reasoning and sources are documented here before any code is written.

#### LLM Selection

The core task requires a model that can simultaneously read Chinese text, identify grammatical errors, and explain them clearly in English. This is a bilingual task — strong Chinese comprehension alone is not sufficient. The following benchmarks were used to select candidates:

- **BenchLM Chinese Leaderboard** — ranks models specifically on Chinese language capability across comprehension, reasoning, and generation: [benchlm.ai/blog/posts/best-chinese-llm](https://benchlm.ai/blog/posts/best-chinese-llm)
- **CMMLU** — Comprehensive Chinese benchmark covering 67 topics, 11,500 questions, evaluating knowledge and reasoning in Chinese contexts: [cmmmu-benchmark.github.io](https://cmmmu-benchmark.github.io/)
- **SiliconFlow 2026 Chinese LLM comparison**: [siliconflow.com/articles/en/best-open-source-LLM-for-Mandarin-Chinese](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Mandarin-Chinese)

**Models selected and their evidence:**

All three candidates were verified against the **BenchLM Chinese leaderboard (July 2026)** and confirmed **available on OpenRouter (July 2026)** — versions and scores are current as of this build, not carried over from an older snapshot.

| Model | Standing (2026) | OpenRouter | Rationale |
|---|---|---|---|
| **DeepSeek V4** | #1 on BenchLM Chinese leaderboard (87) | ✓ — V4 Flash ~$0.14/M input | Top of the Chinese leaderboard; strong bilingual Chinese+English generation; lowest cost of the three, making repeated eval runs practical |
| **GLM-5.2** (Zhipu AI) | #1 open-weight on the Artificial Analysis Intelligence Index, ahead of DeepSeek V4 Pro and Kimi K2.6 | ✓ — ~$0.45/$3.31 per M | Chinese-native from a distinct lab; different architecture from DeepSeek gives a genuine independent data point |
| **Qwen3.5-397B-A17B** | Top-tier Chinese leaderboard (≈79 band) | ✓ | Alibaba; same ecosystem as the Qwen3-Embedding-8B candidate — tests whether a unified all-Qwen LLM + embedding pipeline beats a mixed stack |

*Note on roster: **Kimi K2.6** (Moonshot, ~$0.66/$3.41 on OpenRouter) is a strong current contender but is excluded to keep the bake-off at three and to preserve the all-Qwen pipeline comparison. **Western models** (Claude, GPT-4o) were considered but do not lead Chinese-language benchmarks; they may explain well in English but are outperformed on Chinese comprehension, so including them would spend eval budget without evidence of competitive performance on the primary task.*

All three models are available on OpenRouter under a single API key. No separate provider keys required.

---

#### Embedding Model Selection

The embedding model determines retrieval quality — how well the agent finds relevant grammar rules and past errors when the user submits a sentence. The following sources were used:

- **MTEB Multilingual Leaderboard 2026**: [codesota.com/benchmarks/mteb](https://www.codesota.com/benchmarks/mteb)
- **BentoML embedding model guide 2026**: [bentoml.com/blog/a-guide-to-open-source-embedding-models](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)
- **Mixpeek embedding benchmark 2026**: [mixpeek.com/curated-lists/best-embedding-models](https://mixpeek.com/curated-lists/best-embedding-models)

**Models selected and their evidence:**

| Model | MTEB Multilingual Score | Rationale |
|---|---|---|
| **OpenAI text-embedding-3-small** | Baseline | Widely used, well-documented, easy to integrate — serves as the baseline to beat |
| **Qwen3-Embedding-8B** | 70.58 (#1 MTEB multilingual, as of mid-2025) | Top of the MTEB multilingual leaderboard; Chinese-native from Alibaba; pairs naturally with Qwen3.5 LLM for a fully Chinese-native pipeline comparison |
| **BGE-M3** (BAAI) | Top open-source | Best open-source multilingual embedding model from Beijing Academy of AI; 568M parameters; specifically strong on Chinese; available via HuggingFace Inference API |

*Note: Cohere embed-multilingual-v3 was the prior default recommendation but has been superseded by Qwen3-Embedding-8B on current benchmarks and is not included.*

---

### Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                  │
│                   (Browser / Phone)                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     CHAINLIT UI                              │
│              Chat interface (browser-based)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              GOOGLE OAUTH (via Chainlit)                     │
│   Authenticates user — user ID namespaces ChromaDB          │
│   collections so each user's error corpus is isolated        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    LITELLM GATEWAY                           │
│  Routes via OpenRouter to the selected Chinese-native LLM   │
│      (DeepSeek V4 / GLM-5.2 / Qwen3.5-397B)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               LANGGRAPH AGENT ORCHESTRATION                  │
│     Manages conversation flow, tool calls, memory           │
│                                                             │
│  ┌─────────────────┐          ┌──────────────────────────┐  │
│  │  Session Memory │          │    Long-Term Memory      │  │
│  │ (conversation   │          │  (personal error corpus  │  │
│  │  buffer)        │          │   persists across        │  │
│  └─────────────────┘          │   sessions)              │  │
│                               └──────────────────────────┘  │
└──────┬──────────────────────────────────┬───────────────────┘
       │                                  │
       ▼                                  ▼
┌──────────────────────────────────────────────────────┐
│                    AGENT TOOLS                        │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐                  │
│  │  CC-CEDICT  │  │    TAVILY    │  External APIs   │
│  │  Dictionary │  │  Web Search  │                  │
│  │             │  │              │                  │
│  │ Word lookup │  │ Real-world   │                  │
│  │ pinyin, HSK │  │ Chinese text │                  │
│  │ level       │  │ + context    │                  │
│  └─────────────┘  └──────────────┘                  │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │    Error     │  │   Grammar    │  │   Drill   │  │
│  │   Pattern    │  │    Rule      │  │ Generator │  │
│  │  Analyser   │  │   Fetcher    │  │           │  │
│  │             │  │              │  │ Targeted  │  │
│  │ Frequency,  │  │ Full rule +  │  │ exercises │  │
│  │ trends,     │  │ examples     │  │ from error│  │
│  │ insights    │  │ from corpus  │  │ category  │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬─────┘  │
└─────────┼────────────────┼────────────────┼─────────┘
          │                │                │
          └────────────────┴────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │     CHROMADB       │
                  │   Vector Database  │
                  │                    │
                  │  personal_errors   │
                  │  grammar_rules     │
                  │  hsk_vocabulary    │
                  │  error_patterns    │
                  └────────────────────┘
                                          │
                                          ▼
                                 ┌────────────────────┐
                                 │  OPENAI EMBEDDINGS │
                                 │  text-embedding-   │
                                 │  3-small           │
                                 └────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     LANGSMITH                                │
│         Monitoring — traces every agent call                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              GCP COMPUTE ENGINE (Docker + Caddy)             │
│     Deployment — always-on VM, public HTTPS endpoint         │
└─────────────────────────────────────────────────────────────┘
```

---

### Component Decisions

| Component | Choice | Why |
|---|---|---|
| LLM | DeepSeek V4, GLM-5.2, Qwen3.5-397B | Selected from Chinese language benchmarks (BenchLM, CMMLU) rather than general popularity, and verified current + OpenRouter-available as of July 2026 — all three are Chinese-native models with the bilingual Chinese+English capability this task needs (reading errors in Chinese, explaining them in English); DeepSeek V4 leads BenchLM's Chinese leaderboard (87), GLM-5.2 is the #1 open-weight model on the Artificial Analysis index, and Qwen3.5-397B pairs with the Qwen embedding for an all-Qwen pipeline test; winner selected by eval score on our specific test set |
| LLM Gateway | LiteLLM + OpenRouter | LiteLLM routes all requests through OpenRouter, providing access to all three models under a single API key with no code changes between experiments; all three models are available on OpenRouter at low cost, well within the available budget |
| Agent Orchestration | LangGraph (`create_agent`) + LangChain | LangGraph runs the tool-calling agent as a graph with a MemorySaver checkpointer for per-conversation memory (keyed by thread_id) and produces one grouped LangSmith trace per turn; LangChain provides the underlying model (`ChatLiteLLM`), `@tool` definitions, and structured output |
| Tools | 5 tools — see below | The agent selects tools based on intent; having multiple tools is what makes this an agent rather than a chatbot |
| Embedding Model | OpenAI text-embedding-3-small (baseline) → Qwen3-Embedding-8B (target) | OpenAI used as the starting baseline; Qwen3-Embedding-8B is the current #1 on the MTEB multilingual leaderboard and is Chinese-native from Alibaba — the same ecosystem as our Qwen LLM candidate; BGE-M3 from BAAI tested as the best open-source alternative |
| Vector Database | ChromaDB | Collections are namespaced per user (e.g. `reuben_personal_errors`) so each user's error corpus is fully isolated; four collection types: `personal_errors`, `grammar_rules`, `hsk_vocabulary`, `error_patterns` |
| Authentication | Google OAuth via Chainlit | Chainlit's built-in OAuth support authenticates users with their Google account in ~10 lines of code; the authenticated user ID becomes the namespace prefix for all ChromaDB collections, ensuring complete data isolation between users |
| Monitoring | LangSmith | Traces every LLM call, tool invocation, and retrieval step; provides latency and cost visibility across sessions |
| Evaluation Framework | RAGAS + LLM-as-Judge | RAGAS measures retrieval quality (context precision and recall); LLM-as-Judge scores correction accuracy and explanation quality |
| User Interface | Chainlit | Chat interface deployable in minutes; browser-based and responsive on both desktop and mobile; natively supports OAuth, `@cl.on_chat_start` for onboarding, and starter action buttons so users always have a clear first step |
| Deployment | GCP Compute Engine (Docker + Caddy) | Always-on VM (no cold starts) in Melbourne region for low latency; Docker Compose runs the app behind Caddy for automatic HTTPS; a persistent Docker volume keeps the ChromaDB corpus across restarts. See `DEPLOY.md`. |

### Agent Tools

The agent has five tools and decides which to call based on the user's intent and the content of their input. This decision-making is what distinguishes an agent from a simple chatbot.

| Tool | Type | Trigger | Returns |
|---|---|---|---|
| **CC-CEDICT Dictionary Lookup** | External API | Agent encounters an unfamiliar or misspelled word in the user's input | Definition, pinyin, HSK level, example sentences |
| **Tavily Web Search** | External API | Agent needs real-world usage examples, cultural context, or current Chinese text beyond the static corpus | Live Chinese text examples, cultural notes, contemporary usage |
| **Error Pattern Analyser** | Internal (ChromaDB query) | User asks "what am I getting wrong?", "show my progress", or "drill me on weak points" | Ranked error categories by frequency, trend data, improving vs. persisting patterns |
| **Grammar Rule Fetcher** | Internal (ChromaDB query) | Agent identifies an error type and needs the full rule to explain it accurately | Complete grammar rule, common mistakes for that pattern, correct usage examples |
| **Drill Generator** | Internal (LLM call) | User requests practice, or agent offers a drill after a correction | 3–5 targeted exercises with answers, built from the specific error category just encountered |

---

### Agent Workflow Diagram

```
[User opens app in browser]
          │
          ▼
[Google OAuth login — Chainlit]
  User ID extracted → namespaces
  all ChromaDB collections for
  this user (e.g. reuben_*)
          │
          ▼
    ┌─────────────────────────────────────┐
    │  First-time user or returning?     │
    └──────┬──────────────────┬──────────┘
           │                  │
           ▼                  ▼
   FIRST-TIME USER      RETURNING USER
           │                  │
           ▼                  ▼
  Agent sends welcome   Agent sends session
  + asks 2 questions:   summary:
                        "Welcome back. Since
  Q1: HSK level?        your last session you
  [HSK 1-2][HSK 3-4]   made 3 new errors.
  [HSK 5-6][Beginner]   Most persistent:
                        aspect markers.
  Q2: Biggest struggle? Want a drill?"
  [Tones][Grammar]
  [Vocabulary][Unsure]
           │
           ▼
  Answers stored in
  user profile.
  Error corpus seeded
  with level-appropriate
  patterns.
  3 starter prompts
  shown as buttons:
  → "Check this sentence"
  → "Drill me on tones"
  → "What is 了 vs 过?"
           │
           └──────────────────┐
                              │
                              ▼
[User types input or clicks a starter prompt]
          │
          ▼
[LangChain Agent receives input + user ID]
          │
          ▼
    ┌─────────────────────────────────────┐
    │   ROUTER: What type of request?    │
    └──────┬──────────┬───────────┬──────┘
           │          │           │
           ▼          ▼           ▼
     Correction   Drill /      Grammar /
      Request     Insights     Question
           │          │           │
           ▼          │           ▼
  ┌──────────────────┐│  ┌─────────────────────┐
  │ TOOL: Grammar    ││  │ TOOL: Grammar Rule  │
  │ Rule Fetcher     ││  │ Fetcher             │
  │ Retrieves rule   ││  │ Retrieves rule for  │
  │ for error type   ││  │ question topic      │
  └───────┬──────────┘│  └──────────┬──────────┘
          │           │             │
          ▼           │             ▼
  ┌──────────────────┐│  ┌─────────────────────┐
  │ TOOL: Error      ││  │ TOOL: Tavily Search │
  │ Pattern Analyser ││  │ (if corpus examples │
  │ Retrieves similar││  │ insufficient)       │
  │ past mistakes    ││  │ Fetches real-world  │
  └───────┬──────────┘│  │ usage examples      │
          │           │  └──────────┬──────────┘
          ▼           │             │
  ┌──────────────────┐│             ▼
  │ LLM analyses     ││  ┌─────────────────────┐
  │ sentence using   ││  │ Generate explanation│
  │ retrieved rule   ││  │ with examples       │
  │ + error history  ││  └─────────────────────┘
  └───────┬──────────┘│
          │           ▼
          ▼    ┌──────────────────────┐
  ┌────────────┐│ TOOL: Error Pattern │
  │ Unknown   ││ Analyser            │
  │ word?     ││ Top errors by freq  │
  └─────┬─────┘│ Trend: improving vs │
        │      │ persisting          │
        ▼      └──────────┬──────────┘
  ┌────────────┐          │
  │ TOOL:      │          ▼
  │ CC-CEDICT  │ ┌────────────────────┐
  │ Dictionary │ │ TOOL: Drill        │
  │ Lookup     │ │ Generator          │
  │ definition │ │ 3-5 exercises from │
  │ + pinyin   │ │ top error category │
  └─────┬──────┘ └──────────┬─────────┘
        │                   │
        ▼                   │
  ┌──────────────────┐      │
  │ Generate:        │      │
  │ - Correction     │◄─────┘
  │ - Root cause     │
  │   explanation    │
  │ - Mini drill     │
  │ - Pattern note   │
  │   if recurring   │
  └───────┬──────────┘
          │
          ▼
  ┌──────────────────┐
  │ TOOL: Error      │
  │ Pattern Analyser │
  │ Logs new error   │
  │ to ChromaDB      │
  │ (type, count,    │
  │ context)         │
  └───────┬──────────┘
          │
          ▼
[Response returned to user in Chainlit]
          │
          ▼
[HUMAN REVIEW STEP]
  User reads correction and
  explanation inline.
  Two optional actions shown:
  → "Log this error" (confirm)
  → "Dismiss" (discard — if
     the agent was wrong)
  Default: auto-log after 5s
  so friction is low for most
  corrections.
          │
          ▼
[LangSmith traces every tool call and LLM step]
```

### How the Application Solves the Problem

The user interacts through a simple text chat interface accessible in any browser on laptop or phone. They type a Mandarin sentence, ask a grammar question, or request a drill session. The LangGraph agent classifies the intent and routes accordingly.

**Onboarding and session initiation** are handled by Chainlit's `@cl.on_chat_start` hook. On first login, the agent detects an empty error corpus and runs a short two-question onboarding: the user selects their HSK level and their biggest area of difficulty. These answers are stored in their user profile and used to seed the error corpus with level-appropriate patterns, so the app delivers value from the very first session rather than waiting weeks for the personal corpus to build. Three clickable starter prompts are displayed — "Check this sentence," "Drill me on tones," "What is the difference between 了 and 过?" — so the user always has a clear next action. For returning users the session opens with a personalised summary of their last session's errors and a prompt to continue where they left off. A blank chat window is never shown.

The agent has five tools and selects between them based on the user's intent and the content of their input — this decision-making is what makes it an agent rather than a chatbot. For a correction request, the agent calls the Grammar Rule Fetcher to retrieve the relevant rule from the corpus, then the Error Pattern Analyser to pull semantically similar past mistakes from the user's personal error log. Both results inform how the LLM reasons about the sentence: not just identifying what is wrong, but diagnosing why — root cause, not symptom. Where Duolingo says "incorrect," this agent says "this is your fourth 把-structure error; the underlying issue is applying a disposal marker to an intransitive verb — here is the rule and a targeted drill." If an unknown word is encountered, the agent calls the CC-CEDICT Dictionary tool for its definition, pinyin, HSK level, and example sentences. When corpus examples are insufficient for a grammar question, the agent calls Tavily Web Search to retrieve contemporary real-world Chinese text. Every correction concludes with the agent logging the new error back to ChromaDB via the Error Pattern Analyser — incrementing the count, updating the category, and keeping the personal error profile current.

The fifth tool — the Drill Generator — activates either on user request or when the agent offers follow-up practice after a correction. It generates 3–5 exercises directly targeting the error category just encountered, using the retrieved grammar rule as its source of truth. The Error Pattern Analyser also powers a dedicated insights mode: the user asks "what am I getting wrong?" and the agent returns a ranked summary of their error categories, trend direction (improving or persisting), and a recommendation on where to focus next. This is the feature no existing tool provides — not a streak counter, but a genuine longitudinal diagnostic of the user's learning trajectory.

---

## Task 3: Data Strategy

### Data Sources

The application draws on four data sources loaded into ChromaDB, plus two external APIs called at runtime.

#### ChromaDB Collections

| Collection | Source | Content | Size |
|---|---|---|---|
| `{user_id}_personal_errors` | Generated by the app | Every error the user makes: original input, correction, error category, explanation, timestamp, session count | Grows per user over time |
| `grammar_rules` | Curated from Chinese Grammar Wiki and standard Mandarin textbooks | ~150 grammar rules, each with: rule name, explanation, common English-speaker mistakes, correct and incorrect examples | ~150 documents |
| `hsk_vocabulary` | HSK 1–6 official word lists (publicly available as CSV) | ~5,000 word entries: Chinese character, pinyin, English meaning, HSK level, part of speech, example sentence | ~5,000 documents |
| `error_patterns` | Curated from linguistics research on English-speaker Mandarin errors; supplemented with synthetic data generated by Claude | ~80 error archetypes: error type, why English speakers make this mistake, correct usage, examples | ~80 documents |

#### User-Uploaded Personal Data

The `{user_id}_personal_errors` collection also accepts **direct file uploads** from the user via the Chainlit interface. This is the primary mechanism for satisfying the "own personal data, uploaded to your application" requirement. Two formats are supported in v1:

| Format | Description |
|---|---|
| **Plain text (.txt)** | Freeform notes — tutor corrections, things the user has noticed about their own mistakes, vocabulary observations. Each line is treated as one record. |
| **Anki export (.txt/.tsv)** | Tab-separated Anki deck export (front, back, tags). Each card becomes one record with the Chinese and English fields indexed separately. |

Uploaded content is parsed, chunked per record, embedded, and stored in the user's `{user_id}_personal_errors` collection exactly like app-generated error records — retrieval is available immediately after upload.

The Chainlit `@cl.action_callback` handles the upload flow. Files are processed server-side and can be deleted by the user from their profile at any time.

#### External APIs

| API | Role | When Called |
|---|---|---|
| **CC-CEDICT** | Chinese-English dictionary with pinyin, definitions, and example sentences | Agent calls this when it encounters a word in the user's input that needs definition or clarification |
| **Tavily Web Search** | Live search for real-world Chinese text, contemporary usage examples, and cultural context | Agent calls this when the static corpus does not contain sufficient examples for a grammar question, or when the user asks about current usage |

---

### Chunking Strategy

**Default strategy: one document per semantic unit — no splitting.**

Unlike chunking a long document such as a PDF or research paper, all four data sources in this application are already naturally discrete records. Each HSK word is a self-contained entry. Each grammar rule is a complete explanation. Each error pattern is a standalone archetype. Each personal error is a single logged event.

Splitting these records with a sliding window or fixed token size would actively harm retrieval — a grammar rule split mid-explanation loses the context needed to answer the user's question correctly. Keeping each record as a single chunk means every retrieval returns a complete, usable unit of knowledge.

**Chunk sizes by collection:**

| Collection | Typical chunk size | Rationale |
|---|---|---|
| `personal_errors` | ~100 tokens | Small structured record — complete as-is |
| `grammar_rules` | ~300–500 tokens | Full rule explanation fits within one chunk; longer rules are the exception |
| `hsk_vocabulary` | ~80 tokens | Word entry with pinyin, definition, and example sentence |
| `error_patterns` | ~200–300 tokens | Archetype with examples — self-contained |

For any grammar rule that exceeds 500 tokens, a single split at a natural paragraph boundary is applied with no overlap — overlap is unnecessary here because each paragraph of a grammar rule is topically cohesive, unlike prose where overlap preserves narrative context.

**Metadata filtering before semantic search:**

Each chunk carries structured metadata that allows the agent to pre-filter ChromaDB before running the semantic similarity search. This narrows the candidate set and improves retrieval precision:

- `personal_errors`: always filtered by `user_id` — users never see each other's data
- `grammar_rules`: optionally filtered by `difficulty_level` based on the user's declared HSK level
- `hsk_vocabulary`: optionally filtered by `hsk_level` to surface vocabulary appropriate to the user's stage
- `error_patterns`: optionally filtered by `error_category` (tones / grammar / vocabulary / characters) when the agent has already classified the error type

**Why this approach and not fixed-size chunking?**

Fixed-size chunking (e.g., 256 tokens with 50-token overlap) is appropriate when the source material is unstructured prose — books, articles, support documents — where semantic units do not have clear boundaries. Our data is structured by design. Forcing it through a fixed-size splitter would break grammar rule explanations mid-sentence and create meaningless partial word entries. The natural unit is always the right unit here.

---

### How the Data Sources Interact During a Session

When a user submits a sentence for correction, the agent runs retrieval across multiple collections simultaneously and combines the results before calling the LLM:

```
User input: "她把书被他借走了"
          │
          ├──► Query grammar_rules → retrieves 把-sentence rule
          │                          + passive 被 construction rule
          │
          ├──► Query {user_id}_personal_errors → retrieves
          │    past 把/被 errors by this user (if any)
          │
          ├──► Query error_patterns → retrieves English-speaker
          │    archetype: "mixing disposal and passive markers"
          │
          └──► All three passed to LLM as context
               LLM corrects with root cause explanation
               informed by rule + user history + archetype
                    │
                    ▼
               If word unknown → CC-CEDICT called
               If examples insufficient → Tavily called
                    │
                    ▼
               New error logged back to {user_id}_personal_errors
```

The personal error collection and the reference collections work together: the reference data (grammar rules, error patterns) makes the app immediately useful on day one, while the personal error corpus builds over time to make corrections increasingly specific to the individual user.

---

### Retrieval Strategies Under Evaluation

Every choice below was made against published 2026 retrieval research, not by intuition. The experiment is deliberately structured as **two independent axes over one baseline**, rather than a sprawling five-way comparison, because the axes measure different things and mixing them produces uninterpretable results.

**The baseline pipeline** is semantic similarity search with OpenAI `text-embedding-3-small`, **with metadata pre-filtering always on** (filter by `user_id`, and by `error_category` / `hsk_level` when the agent has classified the query, before the vector search runs). Pre-filtering is treated as baseline hygiene, not a competing strategy — it is a *complement* to semantic search that narrows the candidate pool, so testing it as a rival arm would be a category error. It is applied in every configuration below.

#### Axis 1 — Embedding model (3-way)

The embedding model determines whether the right grammar rule or past error is found at all. Chinese-native models are tested against a strong English-dominant baseline, selected from the MTEB multilingual leaderboard and 2026 open-source embedding guides (sourced in the *Embedding Model Selection* section above).

- **OpenAI `text-embedding-3-small`** — baseline; strong general model, English-dominant training.
- **Qwen3-Embedding-8B** (Alibaba) — #1 on the MTEB multilingual leaderboard (70.58, as of mid-2025); pairs with the Qwen LLM candidate for an all-Qwen Chinese-native pipeline.
- **BGE-M3** (BAAI) — leading open-source multilingual model, 568M params, deep Chinese coverage; runnable via HuggingFace Inference API.

#### Axis 2 — Retrieval technique (3-way)

Reduced from five candidates to three via the research below. Two were removed for principled reasons: **metadata filtering** moved to the always-on baseline (above); a fifth slot was never a distinct technique once embeddings and filtering became their own axes.

**Technique 1 — Hybrid search (BM25 + dense, Reciprocal Rank Fusion).**  
Across 2026 RAG benchmarks, hybrid retrieval consistently beats both sparse-only and dense-only — often by double-digit nDCG/MAP margins — and **more than halves hallucination and rejection rates** in RAG settings ([digitalapplied 2026](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026), [denser.ai 2026](https://denser.ai/blog/hybrid-search-for-rag/)). This is the single best-supported technique for our case specifically: a Chinese grammatical particle (把 / 了 / 过) is an exact-match signal that defines the error type, and BM25 catches it where dense search underweights it. Fusion uses RRF (rank-only) to avoid the score-incompatibility problem of naive weighting. *Implementation note: Chinese BM25 requires CJK tokenization (jieba) — the research is explicit that East Asian languages need CJK-aware tokenizers or lexical matching silently fails.* Built via LangChain's `EnsembleRetriever`.

**Technique 2 — Cross-encoder reranking (BGE-reranker-v2-m3).**  
Retrieve top-20 by embedding similarity, then rerank to the true top-5 with a cross-encoder that scores (query, document) pairs jointly — reliably lifting nDCG@10 over pure vector search ([futureagi 2026](https://futureagi.com/blog/best-rerankers-for-rag-2026/)). **Model choice is BGE-reranker-v2-m3, not Cohere**: 2026 comparisons put its accuracy on par with Cohere Rerank v3.5 while it is Apache-2.0, self-hostable at zero API cost, and strong on Chinese across 100+ languages ([localaimaster 2026](https://localaimaster.com/blog/reranking-cross-encoders-guide)). It also keeps the stack thematically consistent with the Qwen/BGE Chinese-native components rather than adding a Western API dependency.

**Technique 3 — Multi-query retrieval.**  
Generate 3 LLM paraphrases of the query, retrieve for each, merge and dedupe. Justified for our case because query intent varies — "why is this sentence wrong?" and "what is the 把-sentence rule?" retrieve complementary documents. This is the recall-oriented arm and carries the highest latency (3× retrieval + one paraphrase LLM call), so it is measured explicitly on the latency/recall trade-off. Built via LangChain's `MultiQueryRetriever`.

**Comparison table (to be completed in Task 6). Each axis is measured against the same baseline so the winner of each is independently interpretable:**

| Configuration | Context Precision | Context Recall | Correction Score | Latency (ms) |
|---|---|---|---|---|
| **Baseline** — OpenAI embeddings, dense + metadata pre-filter | | | | |
| *Axis 1:* Qwen3-Embedding-8B (MTEB #1 multilingual) | | | | |
| *Axis 1:* BGE-M3 (best open-source Chinese embeddings) | | | | |
| *Axis 2:* Hybrid — BM25 + dense, RRF | | | | |
| *Axis 2:* Cross-encoder rerank — BGE-reranker-v2-m3 | | | | |
| *Axis 2:* Multi-query retrieval | | | | |

The winning embedding and the winning retrieval technique are selected on correction score (primary) and latency (secondary), then combined into the production pipeline. Task 6's "advanced retriever" deliverable is the Axis 2 winner; the "one other change" deliverable is the Axis 1 embedding swap — both backed by this same eval harness.

---

## Task 4: Prototype

*To be completed*

---

## Task 5: Evaluation Harness

### Evaluation Design (pre-build, to be executed after Task 4)

The evaluation dataset must test the capability that actually differentiates this application: **memory-informed personalisation**. A test set of single-turn input → correction pairs only measures stateless correction quality — which any LLM already does without RAG. That is not what this application is selling.

**The whole harness is designed as a head-to-head.** Every case is run through two systems: the full agent, and a *naked-LLM control arm*. The control arm is the strongest fair baseline, not a strawman — the same LLM, a best-effort prompt, and for memory cases the user's raw error records handed directly into its context. The claim in Task 2 ("How This Beats a Naked LLM") is only credible if it survives this comparison, so the eval is built to give the naked LLM every advantage and still show where it structurally fails.

**Three test case types:**

**A_stateless — Stateless correction (40 pairs)**  
A Mandarin sentence with a known error is submitted with no prior error history. The agent should identify the error, retrieve the relevant grammar rule, and return a correct explanation. These test retrieval quality and LLM reasoning. *Expected result: near-parity with the naked LLM on correction accuracy — this is the honest concession — but the agent wins on factual grounding (see below).*

**B_small — Memory-informed correction at small scale (10 sequences, N≈5 seeded errors)**  
Each sequence pre-seeds the user's `personal_errors` collection with 3–5 historical error records of the same category, then submits a new sentence with the same error type. The expected output must explicitly reference the user's history (e.g., "this is your fourth 把 error") and/or personalise the drill. *Expected result: the naked LLM with records in context also passes here — five items is trivial to count. This is deliberately included to prove the harness is fair, not rigged.*

**C_scale — Memory-informed correction at scale (10 sequences, N≈50–100 seeded errors)**  
Identical structure to B_small, but the corpus is seeded with 50–100 mixed-category error records before the query, which asks for a count or trend ("how many 把 errors, and is it getting worse?"). *Expected result: this is where the thesis is proven or falsified. Deterministic aggregation over ChromaDB returns exact counts and trends; the naked LLM — even with all records in context — miscounts, mis-orders the trend, or overflows its budget. If the naked LLM passes C_scale too, the differentiation is thinner than claimed and the prose is toned down accordingly.*

| Test type | # Cases | What it tests | Naked-LLM expectation |
|---|---|---|---|
| A_stateless — Stateless correction | 40 | Rule retrieval, correction accuracy, factual grounding | Parity on correction; loses on grounding |
| B_small — Memory-informed, small scale | 10 | Personalisation with N≈5 history | Parity (fair-baseline sanity check) |
| C_scale — Memory-informed, at scale | 10 | Aggregation/trending over N≈50–100 | Fails — the core differentiator |
| **Total** | **60** | | |

**Metrics:**

| Metric | Tool | Applies to | Why |
|---|---|---|---|
| Context Precision | RAGAS | A_stateless | Was the retrieved grammar rule relevant? |
| Context Recall | RAGAS | A_stateless | Was the right rule retrieved at all? |
| Correction Accuracy | LLM-as-Judge | A, B, C | Is the correction linguistically correct? (expected parity) |
| **Factual-Grounding Accuracy** | Exact match vs CC-CEDICT / HSK ground truth | A, B, C | Are pinyin, tone marks, and HSK level correct? (agent should win) |
| Personalisation Score | LLM-as-Judge | B, C | Does the response explicitly use the error history? |
| **Aggregation Accuracy** | Exact match vs known seeded counts | C only | Is the reported count/trend numerically correct? (the decisive metric) |

Every metric is reported for **both** the agent and the naked-LLM control arm, side by side. The differentiation argument is whatever that table shows — and the strength of the prose in Task 2 will be set by the actual C_scale result, not chosen in advance.

---

### Results — what was actually built, and what it showed

The plan above was executed, but with one deliberate change of direction that you requested during the build: the single six-metric table was rebuilt on the **standard RAGAS suite** rather than fully bespoke scorers. That rebuild grew the harness from one blended table into **four separate evaluation surfaces**. The reason for keeping them separate is important: each surface exercises a *different subsystem* of the application (retrieval, tool-use, generation, and the hidden corpus-writer), and a single blended score would hide *which* subsystem a good or bad number actually belongs to. When a number moves, we need to know whether retrieval, the agent loop, the generator, or the extractor moved it — so they are measured independently.

Every surface writes two artifacts: a human-readable `.md` summary and a `.json` file shaped as `{summary, rows}`, where `rows` contains **one entry per case with the model's verbatim answer stored alongside every score**. Nothing is a black box — every headline number below is a plain function of the raw rows and can be re-derived in a single command. The index and copy-paste verification recipes live in [`evals/results/README.md`](evals/results/README.md).

| Surface | Subsystem it isolates | Files | Cases |
|---|---|---|---|
| Head-to-head | The whole agent vs the naked-LLM control arm | `results/head_to_head.{md,json}` | 60 |
| RAGAS RAG | The retriever → grounding chain | `results/ragas_rag.{md,json}` | 40 |
| RAGAS agentic | Tool-use over the full LangGraph trace | `results/ragas_agentic.{md,json}` | 60 |
| Structured extraction | The hidden post-turn corpus-writer | `results/extraction.{md,json}` | 34 + 17 |

Two provider realities shaped every run and should be stated up front, because they explain several choices below. First, **DeepSeek (the intended default generation model) intermittently hangs for 30+ minutes on OpenRouter**, so all *reproducible* eval generation is run on **GLM** instead; the keep-or-drop decision on DeepSeek is deferred to Task 6, where latency and timeout-rate are measured directly. Second, **constrained-integer "1–5" score fields come back garbled to their minimum on these OpenRouter models**, so every metric is a boolean or an exact extract-then-check rather than a 1–5 judge rating — a judge that reliably answers "yes/no" is worth more than one that unreliably answers "3 or 4".

#### Surface 1 — Head-to-head: does the agent actually beat a naked LLM?

This is the surface that tests the central claim of the project. Every case runs through the full agent and through a naked-LLM control arm given every fair advantage (the same model, a best-effort prompt, and for memory cases the user's raw error records handed straight into its context).

| Metric | Agent | Naked LLM | What it means |
|---|---|---|---|
| A_stateless — correct fix | **36/37** | 32/39 | On the sentences each arm's judge could score, the agent corrected 97% vs the naked LLM's 82% |
| A_stateless — materially misleading claim | **0** | 1 | The agent made no actively wrong grammar claims; the naked LLM made one |
| A_stateless — retrieval recall@3 / MRR | **1.0 / 1.0** | n/a | Every case with a ground-truth rule retrieved the right rule in the top 3 |
| A_stateless — factual grounding (pinyin/HSK correct) | 12/16 (0.75) | 24/30 (0.80) | Near-parity; the agent volunteered *fewer* grounding claims |
| B_small — correct fix (small-scale memory) | 9/10 | 10/10 | Parity, as designed — five history items are trivial to handle |
| B_small — references the user's history | **7/10** | 4/10 | The agent personalises more often |
| B_small — cites a specific count | 0/10 | 0/10 | Neither cites exact numbers at small scale |
| **C_scale — aggregation at scale (the differentiator)** | **10/10** | 7/10 | The agent counts and trends exactly; the naked LLM miscounts |

Reading the table with the reasons behind each row:

- **The denominators in A_stateless differ (37 vs 39) on purpose, not by accident.** A handful of judge calls returned no parseable verdict for one arm's answer; rather than silently scoring an unjudged answer as "wrong" (which would penalise an arm for a *judge* failure), those cases are excluded from that arm's denominator. Three agent answers and one naked answer were dropped this way. This keeps the correction-accuracy rate honest at the cost of unequal denominators, which is the correct trade.

- **The agent won on correction accuracy, which was more than the plan predicted.** The design honestly expected parity here, because stateless correction is something any capable LLM can do. The agent came out ahead (97% vs 82%) because it retrieves the actual grammar rule before answering, so its corrections are anchored in a source rather than generated from the model's memory — and, tellingly, it produced zero materially misleading claims while the naked arm produced one.

- **Factual grounding did *not* become the agent's win, and the honest reason is worth stating.** The design predicted the agent would win on grounding because it can call `dictionary_lookup`. In practice the agent volunteered far fewer explicit pinyin/HSK claims (16 vs 30) and scored slightly lower on them (0.75 vs 0.80). The likely cause is behavioural: the agent leans on its retrieved rule and its structured correction and simply *asserts fewer* checkable pinyin/HSK facts, whereas the naked LLM volunteers more of them and happens to get about 80% right. The conclusion is therefore corrected by the data: grounding is near-parity, and it is **not** where the differentiation lives. That honesty matters more than defending the original prediction.

- **C_scale is where the thesis holds.** The agent scored a perfect 10/10 on at-scale aggregation against the naked LLM's 7/10. The reason the agent is exact is structural rather than lucky: it computes counts and trends deterministically over ChromaDB, so it behaves as an oracle on this task, while the naked LLM — even with every record in context — has to *count in its head* and drifts. One caveat is reported rather than hidden: the naked arm's C_scale score is run-variable (a re-run has produced 6/6), because it depends on the model's counting noise on that run. The stable, defensible claim is the *structural* one: the agent is an exact aggregator by construction and the naked LLM is not, so the agent's 10/10 is repeatable in a way the naked arm's score never is.

#### Surface 2 — RAGAS RAG metrics: is retrieval and grounding sound?

This surface runs the six standard RAGAS RAG metrics over the retriever→grounding chain for the 40 A_stateless cases (LLM judge = gpt-4o-mini, generation = GLM).

| RAGAS metric | Score | Interpretation |
|---|---|---|
| Context Recall | 0.90 | Did retrieval surface the information needed to answer? |
| Context Relevance | 0.84 | How much of what was retrieved was on-point? |
| Faithfulness | 0.84 | Are the answer's claims supported by the retrieved context? |
| Response Groundedness | 0.98 | Is the response anchored in the retrieved context rather than free-floating? |
| Noise Sensitivity | 0.23 | How often irrelevant retrieved chunks corrupt the answer (lower is better) |
| Answer Accuracy | 0.83 | Overall answer correctness per the judge |
| **Deterministic recall@3 / MRR** | **1.0 / 1.0** | Exact rule-id match against the retriever's output |

The single most important thing this surface shows is the **gap between RAGAS's LLM-approximated Context Recall (0.90) and the deterministic recall@3 (1.0)**, and the reason for the gap is the whole methodological point. RAGAS's Context Recall is computed by an LLM judging whether retrieved text "covers" the reference, which is an approximation and undercounts when the wording differs. Our A_stateless cases, by contrast, carry a ground-truth `expected_rule_id`, so we can check retrieval by **exact id match** — which is not an approximation at all. Retrieval genuinely returned the correct rule in the top 3 on 100% of cases; the 0.90 is the judge being conservative, not the retriever missing. This is why the deterministic number is treated as the authority and the RAGAS number as a cross-check, not the other way round — and it is exactly the retriever-level signal Task 6 will vary when it sweeps embedding models.

#### Surface 3 — RAGAS agentic metrics: is the tool-use correct?

This surface runs the standard RAGAS agentic metrics over the full LangGraph tool-call trace for all 60 cases. The two multi-turn reasoning judges use **gpt-4o** (a deliberate deviation explained in "What went wrong" below).

| Metric | A | B | C | Overall | Why it reads this way |
|---|---|---|---|---|---|
| Tool Call Accuracy (exact-set) | 0.55 | 0.10 | 1.00 | 0.55 | An *exact tool-set* match — it scores 0 if the agent calls any tool beyond the reference set |
| **Required-tool recall (deterministic)** | 1.00 | 0.95 | 1.00 | **0.992** | Did the agent call the tools it genuinely needed? |
| Extra-tool rate | 0.45 | 0.90 | 0.00 | — | How often it calls *additional* sanctioned tools (e.g. offering a drill) |
| Agent Goal Accuracy (completion) | 0.80 | 0.80 | 0.80 | 0.80 | Did it complete the user's goal? |

The headline here is that **the low Tool Call Accuracy is a measurement artifact, not an agent failure, and the deterministic required-tool recall of 0.992 is the number that actually matters.** RAGAS's `ToolCallAccuracy` is an exact-set comparison: if the reference says "call A and B" and the agent calls "A, B, and a drill generator", the agent scores **zero** for that case despite doing everything right and more. The agent is *designed* to proactively offer drills, so it frequently calls extra (sanctioned) tools, which tanks the exact-set metric — hence the very high extra-tool rate on Types A and B. The honest signal is therefore the deterministic **required-tool recall**, which asks only "did it call the tools it needed?" and comes out at 0.992. The single dip (B_small at 0.95) is one tones case where the agent reached for `dictionary_lookup` instead of `grammar_rule_fetcher` — a linguistically reasonable choice, not an error.

Two further points, each with its reason:

- **Agent Goal Accuracy measures completion, not correctness, so its 0.80 on C_scale is judge noise rather than a real gap.** On C_scale the agent's deterministic aggregation correctness is 1.00, but the goal-accuracy judge scored completion at 0.80. Because the deterministic correctness is provably perfect on those same cases, the 0.20 shortfall is the judge under-crediting complete answers, not the agent getting anything wrong. This is why `agg_parse` (the deterministic parser) remains the correctness authority on C_scale and the judge is read only as a completion signal.

- **Topic adherence is weak, and this is reported as a genuine finding rather than smoothed over.** Only 2 of 4 off-domain probes were declined; the agent will fulfil a recipe or sports-fact request as long as it can add a Mandarin twist, and on one probe it even reached for web search. This is a real guardrail gap worth flagging for a future iteration. (RAGAS's own `TopicAdherenceScore` was too unstable to headline — it oscillated between 0.0 and 0.67 on a clearly on-topic question even on gpt-4o — so adherence is reported via a focused binary judge over the four probes, with the raw RAGAS number kept in the JSON for completeness.)

#### Surface 4 — Structured extraction: is the hidden corpus-writer trustworthy?

The application silently runs `extract_and_log_error` after every turn to mine the learner's mistake into a structured record and append it to their error corpus. No user ever sees its output, but a wrong record poisons the very B_small/C_scale memory the other surfaces depend on — so this surface is what *justifies trusting the other three*. It is scored on the effective logging predicate the production code actually uses (`has_chinese AND had_error AND original`), across 34 positive cases and 17 negatives.

| Metric | Result | Why |
|---|---|---|
| had_error precision | **1.00** | Not a single clean sentence, question, or English message was ever logged as an error — a false positive is the dangerous case, because it silently corrupts the corpus |
| had_error recall / F1 | 0.97 / 0.985 | The one recurring miss is a debatable single-clause sentence |
| Category accuracy (specific golds) | 0.50 | Low — but almost entirely due to *empty* fields, not wrong ones (see below) |
| Correction validity (logged) | 0.64 | Same story: the gap is empty corrections, not invalid ones |
| Correction validity *when non-empty* | **0.95** | When the model does emit a correction, it is nearly always valid |

The precision result is the reassuring one: the guardrail against corpus poisoning is perfect. The interesting result — and the one that took real investigation to get right — is **why** category accuracy and correction validity look low. The cause is **not** that GLM produces *wrong* categories or corrections; it is that GLM's structured output is **unreliable**, intermittently returning `had_error=True` with the `correction`, `category`, and `explanation` fields all left *empty* together (and occasionally emitting malformed JSON with `null` string fields). When it does fill those fields, they are almost always right (correction 0.95 valid; only two genuine category mismatches in the whole set).

This conclusion was hardened by ruling out the alternatives rather than asserting it, because the first draft of the finding was wrong and the correction matters:

- **It is not a capability limit.** The correct fix is literally present in the coach reply the extractor reads, and for the very same inputs the model returns a complete, correct record on a later call — so it *can* produce the fields; it just doesn't do so reliably.
- **It is not the structured-output method.** The drop reproduces on both the `json_mode` and `function_calling` extraction paths.
- **It is not sampling temperature.** It persists at temperature 0 — GLM returned different outputs for the *same input* at temp 0 — which means this is provider-side non-determinism, not a temperature the app can tune away.

The actionable conclusion, therefore, is that the fix is a **retry-on-incomplete / field-validation guard around the extraction call** — not a model swap and not merely lowering temperature. This is a concrete input to the Task 6 model decision. (One data-quality note handled here rather than hidden: six reference-corpus inputs carried English editorial parentheticals such as "（meaning: I have tried…）". These were *excluded* rather than stripped, because the "error" in them only exists relative to an intended meaning a learner would never actually type — stripping the annotation would relabel a perfectly grammatical sentence as a mistake and unfairly penalise the extractor.)

### What went wrong along the way, and how each was handled

The value of an eval harness is partly in the traps it survives, so these are recorded rather than hidden. Each was found empirically during the build and each conclusion carries its reason.

- **1–5 judge scores were unusable, so all metrics became boolean or extractive.** Constrained-integer score fields came back pinned to their minimum on the OpenRouter models, whereas boolean and named-scalar fields are reliable. A judge that answers "yes/no" dependably is more informative than one that answers "3" unreliably, so every metric is a boolean or an exact extract-then-check.
- **DeepSeek hangs, so GLM is used for reproducible generation.** DeepSeek intermittently stalls for 30+ minutes on OpenRouter, which makes repeatable runs impossible; GLM generates reliably. The keep-or-drop decision is deferred to Task 6 where latency and timeout-rate are measured head-to-head rather than guessed.
- **`AgentGoalAccuracyWithReference` is unusable, so the `WithoutReference` variant is used.** Its compare-outcome prompt rated semantically identical outcomes ("total is 60" vs "the total number of logged errors is 60") as *different*, scoring ~0 everywhere on both gpt-4o-mini and gpt-4o — so it is a prompt defect, not a judge-strength issue. The `WithoutReference` variant is reliable, but it measures **completion, not correctness**, which is why the deterministic parser remains the correctness authority on C_scale.
- **The agentic reasoning judges use gpt-4o, a deliberate deviation from the gpt-4o-mini used elsewhere.** gpt-4o-mini's goal verdict coin-flipped on complete multi-part answers (verified as [1,1,0,0,1] on a real trace); gpt-4o was stable. The deviation is scoped to the two multi-turn reasoning judges only and is overridable via `RAGAS_AGENTIC_EVALUATOR`.
- **An early deterministic deflection check was wrong and was replaced after reading the actual answers.** A first attempt inferred "off-topic deflection" from the presence of Chinese plus a redirect, but the coach *fulfils* off-domain requests while sprinkling Mandarin on top, so that heuristic read every answer as a redirect and falsely reported 3/4 deflected. Reading the real answers showed the true number is ~2/4, which is the corrected (and less flattering) finding now reported.
- **The extraction finding itself was initially over-stated and then corrected.** The first draft asserted a GLM capability limit and recommended dropping DeepSeek; investigating the cause (dumping the omitted `explanation` field, retrying the same inputs, testing `function_calling`, testing temperature 0) showed it is run-variable provider non-determinism, so the recommendation became a retry/validation guard instead. This is the harness catching its own premature conclusion, which is the behaviour you want from an eval process.

### Why these results can be trusted

The single design principle running through every surface is that **each LLM-judged metric is paired with a deterministic cross-check that can be recomputed independently, and where the two disagree the deterministic number is the authority.** This is what turns "an LLM said it's good" into a defensible measurement.

- RAGAS Context Recall (0.90, LLM-approximated) is anchored by exact rule-id recall@3 (1.0, deterministic).
- RAGAS Tool Call Accuracy (0.55, exact-set) is anchored by required-tool recall (0.992, deterministic).
- Agent Goal Accuracy on C_scale (0.80, judge completion) is anchored by `agg_parse` aggregation correctness (1.00, deterministic).
- Correction validity in the extraction surface (LLM judge) is anchored by exact-match against the gold correction first, with the judge used only on the residue.

On top of that, the whole comparison is a head-to-head against a fair — not strawman — baseline, every raw answer is stored for inspection, and each headline number is a plain function of the stored rows with a copy-paste recipe to reproduce it in [`evals/results/README.md`](evals/results/README.md). Where an LLM judge proved unfit, it was demoted in favour of the deterministic signal and the demotion was documented, because showing that a metric was assessed and found unfit is itself part of an honest methodology.

### What this sets up for Task 6

The evaluation did its job of surfacing the decisions Task 6 now has to make with evidence rather than intuition:

- **Retrieval is already perfect on exact rule-id recall (1.0)**, so the Task 6 embedding sweep must be judged on the harder cases and on latency, not on whether it can find an obvious rule — the baseline is already at the ceiling on the easy metric.
- **The keep-or-drop DeepSeek decision now has real inputs**: DeepSeek's hangs (a reliability cost) on one side, and GLM's structured-output non-determinism in the extraction surface (a correctness cost that a guard can mitigate) on the other. Task 6's bake-off adds the missing latency and timeout-rate columns to settle it.
- **The extraction surface produced a concrete, cheap product fix** — a retry-on-incomplete guard around `extract_and_log_error` — that should land before the bake-off so the model comparison is measured on a corpus-writer that fails safe.

---

## Task 6: Advanced Retrieval & Improvements

*To be completed*

---

## Task 7: Next Steps

*To be completed*
