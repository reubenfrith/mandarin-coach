# Certification Challenge Submission
**Student:** Reuben Frith  
**Due:** Tuesday, 14 July 2026  
**Project:** Mandarin Learning Coach — Personal Error Intelligence Agent

---

## Task 1: Problem, Audience & Scope

### Problem Statement

Adult self-directed Mandarin learners plateau because no tool tracks their specific error patterns across sessions, so they repeat the same mistakes indefinitely while drilling content they have already mastered.

### Why This Is a Problem

**Who has the problem?**  
Adult English speakers learning Mandarin independently — people using apps like Duolingo or Anki, working with occasional tutors, without the structure of a formal classroom. This learner has real motivation and invests real time, but has no systematic support structure for tracking their individual weaknesses.

**What are they trying to do?**  
Achieve conversational fluency in Mandarin — one of the hardest languages for English speakers, requiring simultaneous mastery of tones, characters, grammar patterns, and cultural register. Progress is inherently slow and error-prone, and the learner depends on feedback to improve.

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

A personal Mandarin coaching agent that accepts user-submitted text, identifies errors by reasoning over a structured personal error corpus and a curated reference knowledge base, returns pattern-level corrections with root cause explanations, logs every mistake to a growing private corpus, and uses LiteLLM and OpenRouter to experimentally compare three models selected from Chinese language benchmarks — DeepSeek V3, Qwen3.5, and GLM-5 — to select the best model for this specific bilingual task with evidence rather than assumption.

---

### Why This Cannot Be Done by ChatGPT or Claude Today

Both ChatGPT and Claude now offer memory features, so this distinction needs to be stated precisely.

**What their memory actually does:**  
ChatGPT and Claude memory stores short text summaries of things you have told them — think of it as a sticky note. It might remember "user is learning Mandarin at HSK 3 level." It cannot answer "how many times have I made a 把 error?", "is my tone accuracy improving over time?", or "which error category is most persistent across my last 50 sentences?" Those questions require structured, queryable, semantically searchable data — not a sticky note.

**The five specific gaps:**

| Capability | ChatGPT / Claude with Memory | This Application |
|---|---|---|
| Error storage | Unstructured text summary | Structured records with category, count, context, timestamp |
| Retrieval | No semantic search — flat recall only | Vector similarity search — finds errors semantically related to the current mistake |
| Pattern detection | Cannot count or trend errors over time | Knows you have made 把 errors 9 times and that frequency is increasing |
| Reference knowledge | Relies on training data only | RAG over HSK corpus, grammar rules, and English-speaker error archetypes |
| Data ownership | Locked to provider's servers | Your corpus, your deployment, fully portable |

**The analogy:**  
ChatGPT memory is a GP who jots a note about you after each visit. This application is a specialist who keeps a structured medical record — searchable, trendable, with pattern analysis across every encounter. Same concept of "memory," completely different capability.

**The key technical reason:**  
Meaningful personalisation requires retrieval over a growing structured corpus, not a language model's flat context window. As your error history grows to hundreds of records, a context window cannot hold or reason across it. ChromaDB with semantic search scales indefinitely; a sticky note does not.

---

### What This Application Does Not Do (v1 Scope)

This version focuses on text-based interaction only. Voice input, pronunciation correction, and tone recognition are post-v1 features. The core value — longitudinal error intelligence — is fully delivered through typed chat.

---

### Model Selection Research

All model choices are based on benchmarks specific to Chinese language tasks, not general popularity. The reasoning and sources are documented here before any code is written.

#### LLM Selection

The core task requires a model that can simultaneously read Chinese text, identify grammatical errors, and explain them clearly in English. This is a bilingual task — strong Chinese comprehension alone is not sufficient. The following benchmarks were used to select candidates:

- **BenchLM Chinese Leaderboard** — ranks models specifically on Chinese language capability across comprehension, reasoning, and generation: [benchlm.ai/blog/posts/best-chinese-llm](https://benchlm.ai/blog/posts/best-chinese-llm)
- **CMMLU** — Comprehensive Chinese benchmark covering 67 topics, 11,500 questions, evaluating knowledge and reasoning in Chinese contexts: [cmmmu-benchmark.github.io](https://cmmmu-benchmark.github.io/)
- **SiliconFlow 2026 Chinese LLM comparison**: [siliconflow.com/articles/en/best-open-source-LLM-for-Mandarin-Chinese](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Mandarin-Chinese)

**Models selected and their evidence:**

| Model | BenchLM Chinese Score | Rationale |
|---|---|---|
| **DeepSeek V3** | 87 (#1) | Top of the Chinese language leaderboard; strong bilingual Chinese+English generation; lowest cost on OpenRouter (~$0.27/M input tokens) making experimentation practical |
| **GLM-5** (Zhipu AI) | 81 (#3) | Chinese-native model from a Chinese AI lab; strong grammar understanding; distinct architecture from DeepSeek providing a genuine independent data point |
| **Qwen3.5-235B** | 79 (#5) | Alibaba; same ecosystem as Qwen3-Embedding-8B — testing whether a unified Qwen LLM + Qwen embedding pipeline outperforms mixed stacks |

*Note: Western models (Claude, GPT-4o) were considered but do not appear in the top 5 of Chinese language benchmarks. They may still perform well on explanation quality in English but are outperformed on Chinese comprehension. Including them would consume evaluation budget without evidence of competitive performance on the primary task.*

All three models are available on OpenRouter. No separate API keys required.

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
| **Qwen3-Embedding-8B** | 70.58 (#1 MTEB multilingual) | Current top of the MTEB multilingual leaderboard; Chinese-native from Alibaba; pairs naturally with Qwen3.5 LLM for a fully Chinese-native pipeline comparison |
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
│         Routes requests to Claude claude-sonnet-4-6               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               LANGCHAIN AGENT ORCHESTRATION                  │
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
│                       RENDER                                 │
│              Deployment (public endpoint)                    │
└─────────────────────────────────────────────────────────────┘
```

---

### Component Decisions

| Component | Choice | Why |
|---|---|---|
| LLM | DeepSeek V3, Qwen3.5-235B, GLM-5 | Selected from Chinese language benchmarks (BenchLM, CMMLU) rather than general popularity — all three are Chinese-native models with strong bilingual Chinese+English capability required for this task (reading errors in Chinese, explaining them in English); DeepSeek V3 leads BenchLM's Chinese leaderboard at score 87, Qwen3.5 at 79, GLM-5 at 81; winner selected by eval score on our specific test set |
| LLM Gateway | LiteLLM + OpenRouter | LiteLLM routes all requests through OpenRouter, providing access to all three models under a single API key with no code changes between experiments; all three models are available on OpenRouter at low cost, well within the available budget |
| Agent Orchestration | LangChain | Mature framework with built-in support for RAG chains, tool use, and both session and long-term memory patterns |
| Tools | 5 tools — see below | The agent selects tools based on intent; having multiple tools is what makes this an agent rather than a chatbot |
| Embedding Model | OpenAI text-embedding-3-small (baseline) → Qwen3-Embedding-8B (target) | OpenAI used as the starting baseline; Qwen3-Embedding-8B is the current #1 on the MTEB multilingual leaderboard and is Chinese-native from Alibaba — the same ecosystem as our Qwen LLM candidate; BGE-M3 from BAAI tested as the best open-source alternative |
| Vector Database | ChromaDB | Collections are namespaced per user (e.g. `reuben_personal_errors`) so each user's error corpus is fully isolated; four collection types: `personal_errors`, `grammar_rules`, `hsk_vocabulary`, `error_patterns` |
| Authentication | Google OAuth via Chainlit | Chainlit's built-in OAuth support authenticates users with their Google account in ~10 lines of code; the authenticated user ID becomes the namespace prefix for all ChromaDB collections, ensuring complete data isolation between users |
| Monitoring | LangSmith | Traces every LLM call, tool invocation, and retrieval step; provides latency and cost visibility across sessions |
| Evaluation Framework | RAGAS + LLM-as-Judge | RAGAS measures retrieval quality (context precision and recall); LLM-as-Judge scores correction accuracy and explanation quality |
| User Interface | Chainlit | Chat interface deployable in minutes; browser-based and responsive on both desktop and mobile; natively supports OAuth, `@cl.on_chat_start` for onboarding, and starter action buttons so users always have a clear first step |
| Deployment | Render | Simple Python app hosting with a free tier; provides a public URL and easy environment variable management |

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
[LangSmith traces every tool call and LLM step]
```

### How the Application Solves the Problem

The user interacts through a simple text chat interface accessible in any browser on laptop or phone. They type a Mandarin sentence, ask a grammar question, or request a drill session. The LangChain agent classifies the intent and routes accordingly.

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

The baseline retrieval pipeline (semantic similarity search with OpenAI embeddings) is the starting point. The following strategies will be tested against the same evaluation dataset in Tasks 5 and 6 to find the best-performing combination for this specific use case.

**Strategy 1: Embedding model comparison — OpenAI vs Qwen3-Embedding vs BGE-M3**

`text-embedding-3-small` is the baseline — a strong general model with English-dominant training. Two Chinese-native alternatives will be tested against it:

- **Qwen3-Embedding-8B** (Alibaba) — current #1 on the MTEB multilingual leaderboard (score 70.58) with specifically strong Chinese and English performance. This is the same Alibaba ecosystem as the Qwen LLM we are testing, creating a potentially powerful all-Qwen pipeline for Chinese language tasks.
- **BGE-M3** (BAAI — Beijing Academy of AI) — the leading open-source multilingual embedding model, 568M parameters, trained on 100+ languages with deep Chinese coverage. Can be run via HuggingFace Inference API at low cost.

All three use the same chunks and ChromaDB collections. Retrieval quality is compared via RAGAS context precision and recall on the same test set.

**Strategy 2: Pure semantic vs hybrid search (BM25 + semantic)**

Semantic search finds conceptually related documents. BM25 keyword search catches exact character matches — when the user writes 把, BM25 finds every document containing 把 directly. For Chinese grammar patterns where specific characters define the error type, exact matching is more important than in English text. Hybrid search combines both signals with a weighted score. LangChain's `EnsembleRetriever` implements this with no additional infrastructure.

**Strategy 3: Metadata pre-filtering vs post-filtering**

Pre-filtering narrows the candidate pool before semantic search (e.g., filter `error_category = grammar` then search within that subset). Post-filtering runs semantic search across all documents then filters the results. Pre-filtering should give better precision; post-filtering gives better recall. The right trade-off depends on corpus size and query type — both will be measured.

**Strategy 4: Reranking with Cohere Rerank**

Retrieve the top 20 candidates cheaply with embedding similarity, then apply Cohere's cross-encoder reranker to reorder them and return the true top 5. Cross-encoders evaluate query-document pairs jointly and are significantly more accurate than bi-encoder similarity scores. Available via OpenRouter at low cost per call.

**Strategy 5: Multi-query retrieval**

Generate 3 paraphrases of the user's query using the LLM, run retrieval for each, and merge the result sets before deduplication. Useful because "why is this sentence wrong?" and "what is the rule for 把-sentences?" retrieve different but complementary documents. LangChain's `MultiQueryRetriever` implements this out of the box.

**Comparison table (to be completed in Task 6):**

| Strategy | Context Precision | Context Recall | Correction Score | Latency (ms) |
|---|---|---|---|---|
| Baseline — semantic only (OpenAI text-embedding-3-small) | | | | |
| Qwen3-Embedding-8B (MTEB #1 multilingual) | | | | |
| BGE-M3 (best open-source Chinese embeddings) | | | | |
| Hybrid search — BM25 + semantic (OpenAI embeddings) | | | | |
| Semantic + Cohere Rerank | | | | |
| Multi-query retrieval | | | | |

The winning strategy will be selected based on correction score (primary) and latency (secondary), and will become the production retrieval pipeline.

---

## Task 4: Prototype

*To be completed*

---

## Task 5: Evaluation Harness

*To be completed*

---

## Task 6: Advanced Retrieval & Improvements

*To be completed*

---

## Task 7: Next Steps

*To be completed*
