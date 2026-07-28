# Voice Coach — plan

Turn the **voice partner** (free-form spoken chat) into a **voice coach** that also
answers clarifying / learning questions ("why was that wrong?", "explain that rule",
"give me another example") — by routing each spoken turn to the brain that fits it.

## Decisions (locked)

- **Routing:** auto-classify each turn **+ a manual override** so an ambiguous turn can be
  forced into coaching mode.
- **Memory scope:** the voice session keeps **its own** conversation context (separate from
  the text coach). The per-user error **corpus** is still shared, so longitudinal learning
  carries across both surfaces — only the turn-by-turn chat log is separate.
- **Coach answer style:** **speak short, show full.** TTS a concise spoken line; render the
  full explanation (rule, examples, drills) as on-screen text.
- **Bias:** precision-first toward CONVERSE — misrouting chat→coach (an English lecture when
  you wanted to talk) is more jarring than the reverse, and the Mandarin partner already
  does light inline correction, so a misrouted mild question degrades gracefully. Mirrors
  the repo's existing precision-first philosophy (`LOG_MARGIN`, the extraction guard).

## Both brains already exist — this wires a router between them

| | Conversation brain | Coach brain |
|---|---|---|
| Path today | `voice_api._reply` | `agent.run_agent` |
| Persona | warm partner, **speaks Mandarin**, light inline recasts | analytic, **explains in English** |
| Tools | none | grammar-rule RAG, error-pattern (corpus), dictionary, drills, web |
| Memory today | `_voice_history` dict (last 12) | LangGraph checkpointer by `thread_id` |

The two personas have *opposite* language and verbosity behaviour, which is exactly why two
brains beats one blurry prompt.

## The crux is memory, not routing

"Why was that wrong?" only works if the coach brain can see the recast the **partner** just
made. Today those live in two separate memories, so the handoff is blind. Fix:

- **`_voice_history` becomes the single canonical spoken log.** Both paths read/write it.
- The coach turn gets the recent history **injected as the message list** (seed the graph
  with `[…recent turns…, new question]` and a throwaway thread_id) rather than relying on
  the LangGraph checkpointer — keeps voice context out of the text coach and vice-versa.
- The coach's answer is written **back** into `_voice_history` (summarised, mode-tagged) so
  conversation resumes seamlessly after a learning detour, and a long English explanation
  doesn't drift the *next* converse turn into English.
- The "correction" being asked about is almost always the **last assistant turn** (already
  in history). No corpus handoff needed for that; the corpus is for longitudinal patterns.

## Two prerequisites (must land first)

1. **STT is hardcoded `language="zh"`** (`voice_api._transcribe`). An English clarifying
   question gets mangled into Chinese phonetics — which sabotages both the classifier and
   the coach, *and* English input is the strongest signal that a turn is a learning
   question. Relax to auto-detect (config `VOICE_STT_LANGUAGE`, default auto).
   **Correction to the original plan:** the STT model is `gpt-4o-mini-transcribe`, which
   supports only `json`/`text` response formats — **not** `verbose_json` — so there is no
   model-returned `language` field. The routing signal therefore comes from the
   **transcript's script** (Han vs Latin) in Phase 2, which is model-agnostic and a stronger
   "is this an English meta-question" signal than a language code anyway. **DONE** — see
   Phase 0 status below.
2. **The coach brain is bounded at `AGENT_TURN_TIMEOUT=180s` and chains tool calls** — fine
   for text, unacceptable while someone holds the mic. The voice-coach path needs its own
   tighter budget: shorter timeout, a tool-call ceiling, and/or a faster model.
   **Update:** the voice pipeline is now all-OpenAI on `gpt-4o-mini` (see below), a fast
   non-reasoning model — measured STT+chat ~2.3s vs ~7.5s for the old glm chat call alone.
   So the voice-coach brain (Phase 1) runs on `gpt-4o-mini` too; that + a tool-call ceiling
   is the latency budget, no reasoning-model timeout to fight.

**Voice provider consolidation (done alongside Phase 0):** all three voice legs — STT, chat,
TTS — now run direct on OpenAI (`gpt-4o-mini-transcribe` / `gpt-4o-mini` / `gpt-4o-mini-tts`).
The OpenRouter proxy hop and the reasoning chat model were the latency problem. The TEXT
coach still uses the OpenRouter reasoning models + tools. `_openrouter_client` was removed
from `voice_api`.

## Cheap routing (no classifier call on the common path)

- **Pure-Chinese transcript + detected zh → CONVERSE** with no LLM classifier call (the
  common case, zero added latency).
- Otherwise invoke a structured-output classifier (reuse the `_extract_record` pattern —
  `with_structured_output(TurnIntent)` on a fast model), biased toward CONVERSE.
- **Manual override** short-circuits both: a `mode` form field (`auto|converse|coach`); when
  not `auto`, skip classification entirely.

## Coach answer format — "speak short, show full" with zero extra calls

Instruct the voice coach to answer as: **first line = a one-sentence spoken TL;DR**, rest =
the detailed explanation (examples/drills). Then `spoken_text` = first line (→ TTS),
`assistant_text` = whole answer (→ shown, with ruby on any Chinese examples). No structured
output, no second call, no structured-output-vs-tools conflict.

## Implementation phases

**Phase 0 — STT prerequisite** ✅ DONE
- `config.py`: `VOICE_STT_LANGUAGE` (default None = auto-detect). ✅
- `voice_api._transcribe`: added a `language` param (hint sent only when set); returns the
  transcript string (no `verbose_json`/detected-language — unsupported by the model). ✅
- `voice_turn` auto-detects (`VOICE_STT_LANGUAGE`); Pass-1 pronunciation drafts stay pinned
  to `zh`. ✅
- **Verified** via a real TTS→STT round-trip (no speech samples in the repo): auto-detect is
  byte-identical to forced-zh on Mandarin (`我昨天去商店买东西了。`) and transcribes
  `"Why is that sentence wrong?"` as English. All 5 tests still pass.
- **Still needs a human check:** noisy real-mic *English* input — clean TTS audio can't
  reproduce the zh-bias mangling the fix targets. Test in-browser before trusting the router.

**Phase 1 — shared history + bounded coach path** ✅ DONE
- `_voice_history` is now the canonical, **mode-tagged** spoken log (`{role, content, mode}`),
  shared by both brains via `_history_messages` / `_remember`. `_reply` refactored onto it. ✅
- `agent.build_voice_coach(user_id)` — a STATELESS `create_agent` graph (no checkpointer;
  voice injects its own history) on the coach tools + `VOICE_COACH_SYSTEM_PROMPT`
  (spoken-first-line convention). `_build_graph` grew an optional `checkpointer` param. ✅
- `agent.run_voice_coach(graph, history_messages, question)` — injects the message list,
  bounded by `VOICE_COACH_TIMEOUT=45s` + `recursion_limit=8`, returns `(spoken, full)` via
  `_split_spoken`; on error speaks a short apology. ✅
- `voice_api._coach_reply` ties it together: runs the brain over shared history, writes back
  only the SHORT spoken line (mode=coach) so a long English answer can't bloat/derail chat. ✅
- Tests (`tests/test_voice_coach.py`, 15 checks) — the crux is proven: a coaching question
  sees the prior conversation and the correction in it.
- **Verified end-to-end on real `gpt-4o-mini`:** identified the 的 from injected history,
  honored the spoken-first-line format. Latency: **~2.1s with no tool call, ~6.6s when
  `grammar_rule_fetcher` fires** (real corpus loaded). Both within the 45s bound; the ~6.6s
  is the realistic figure for a grounded coaching answer. Note: gpt-4o-mini's grammar
  precision is imperfect (a 地/的 slip in one example) — a model-quality caveat, not wiring.
- NOT yet wired into `/api/voice/turn` — that's Phase 2 (the router decides when to call it).

**Carry into Phase 2 (from an advisor review):**
- **English-drift is unverified** — the stub test proves the next chat turn *sees* the coach
  detour, but only an in-browser turn can confirm the partner still replies in *Mandarin*
  after an English coaching aside. This is the one real risk of the write-back-short-line
  design; don't mark it done on the stub.
- **Thread the learner's level into the coach** — `_coach_for` builds `build_voice_coach(uid)`
  with no `profile_note`, so unlike the conversation partner it won't pitch to HSK level yet.

**Phase 2 — the router** ✅ DONE
- `TurnIntent` model + `INTENT_CLASSIFIER_PROMPT` + `agent.classify_turn_intent` (fast model,
  structured output, defaults to converse on any error). ✅
- `voice_api._route_intent(user_id, text, mode)` — manual override wins; a zero-latency
  SCRIPT heuristic routes the clear cases (English→coach, Mandarin→converse); only a mixed
  turn costs the classifier call. Biased to converse throughout. ✅
- `/api/voice/turn`: accepts `mode`; branches on intent; logs **only on CONVERSE** turns;
  response gains `intent`, `spoken_text`, full `assistant_text`. ✅
- HSK note now threaded into the coach (`_coach_for` → `build_voice_coach(uid, _profile_note)`). ✅
- Tests (`tests/test_voice_router.py`, 21 checks): heuristic routing + classifier-only-on-mixed
  + endpoint branch (coach speaks TL;DR / shows full / logs nothing; converse logs; override
  wins; empty→null intent).

**Phase 3 — frontend** ✅ DONE (`app.js`, `index.html`, `style.css`)
- 3-way **mode toggle** on the voice pane: Auto (default) / Chat / Coach, sent as `mode`. ✅
- Coach replies styled distinctly (accent left-border, "coach · explanation" label, normal
  line-height for English prose, ruby only on the Chinese examples); the short spoken TTS
  auto-plays; the full text is shown. ✅
- Intro copy updated to tell the learner they can ask questions in English.
- (Power-user Shift+Space and the tab rename remain optional/deferred — cosmetic.)

**Phase 4 — measure** (mirrors the repo's eval-surface discipline)
- A small labeled transcript→intent set → a router **precision** eval surface under
  `evals/surfaces/`, precision-first on CONVERSE. Calibrate the classifier bias / heuristic.
- Wiring tests (`tests/test_voice_router.py`): stub the classifier + both brains; assert
  manual override wins, pure-Chinese skips the classifier, coach path injects history and
  writes a summarised turn back, CONVERSE-only logging.

## Files touched

- `app/config.py` — `VOICE_STT_LANGUAGE`, voice-coach timeout/ceiling knobs.
- `app/voice_api.py` — STT auto-detect, router, branch, response shape.
- `app/agent.py` — `build_voice_coach`, `run_voice_coach`, `TurnIntent`.
- `app/prompts.py` — `VOICE_COACH_SYSTEM_PROMPT`, `INTENT_CLASSIFIER_PROMPT`.
- `app/web_ui/{app.js,index.html,style.css}` — mode toggle, coach styling.
- `tests/test_voice_router.py` (new); `evals/surfaces/voice_intent_eval.py` (new).

## Open / deferred

- Spoken/detail split is a **format convention** in v1; upgrade to structured `{spoken, detail}`
  only if the first-line convention proves unreliable.
- Auto-detect mis-detection risk on very short/noisy clips — fall back to a zh hint if the
  eval shows Mandarin degradation.
- Tab rename + coach-bubble visual polish are cosmetic; keep out of the critical path.
