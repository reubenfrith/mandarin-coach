# Pīnyīn-accuracy — findings & decisions

Decision record for the `pinyin_accuracy` surface (`surfaces/pronunciation/pinyin_eval.py`).
The headline `.md`/`.json` live in `results/pinyin_accuracy.{md,json}`; this note is the
narrative: why the surface exists, the framing trap it had to avoid, what it found, and the
product change it argues for.

## Why the pīnyīn ruby needed its own surface

Every learner-facing character in the app carries pīnyīn: the ruby (`汉字` with the reading
underneath) in the text and voice coaches, and the `/api/pinyin` string. All of it comes from
two functions in `tools.py` — `pinyin_segments` and `_tone_pinyin` — which both call pypinyin
with `Style.TONE`, i.e. **citation tones**. Nothing checked whether the tone printed under a
hanzi is the tone the learner should actually say. That is a direct correctness surface: wrong
pīnyīn under a character teaches a wrong pronunciation, and it's the *reference* the learner
trusts.

`tools.py` itself flags the gap — `annotate_tones` carries the comment *"tone sandhi is not
applied here (a Phase-2 refinement)."* This surface quantifies that Phase-2 gap, deterministically.

## The framing trap (and how the buckets avoid it)

The naïve version of this eval — "pypinyin doesn't apply tone sandhi, therefore it's broken" —
is an **overclaim**, and the same kind the other surfaces were built to avoid. Citation tones
are a *defensible* pedagogical convention: dictionaries mark 你好 as `nǐ hǎo` and teach the
third-tone sandhi rule separately. An eval that scores citation output as "wrong" is grading
its author's product opinion, not a defect.

So the headline is **not** citation-vs-spoken. It is **inconsistency**: pypinyin's tone output
is a lexicalised lookup, not a rule engine, so it applies the *same* rule to some words and not
others. That is wrong under *either* convention and needs no philosophical defense. The gold set
is bucketed so the unassailable defects are scored and the defensible product choice is only
*surfaced*:

| Bucket | Class | Scored? |
|---|---|---|
| `yi_bu_sandhi` | **Defect** — consistency of 一/不 sandhi | yes (headline) |
| `neutral_particle` (地/得) | **Defect** — wrong lexical reading, not sandhi | yes |
| `t3_bisyllabic` | **Coverage gap** under the spoken-tone choice (weak harm) | yes, but framed as a decision |
| `redup` | Secondary (soft gold; some dicts keep full tone) | yes, de-emphasised |
| `control` | Sanity floor (lexical polyphones pypinyin gets right) | yes, must be ~100% |
| `t3_multi`, `erhua` | Contested / structurally unexpressible | **no** — carried for honesty |

Gold was authored from **ground-truth probes of the real functions**, not from memory, and the
datagen prints a gold-vs-pypinyin diff so a mis-typed tone mark is caught before it becomes a
"finding" (for every scored case the two differ only on the syllable the rule targets).

## What it found

**1. 一/不 sandhi is inconsistent — the headline.** Where sandhi should change the citation
form, pypinyin applies it to only **12/36 (0.33)** syllables, and — this is the point — the
misses are *scattered within each sub-rule*, not clean:

| Sub-rule | applied | note |
|---|---|---|
| 不 + 4th tone → bú | 5/14 | 不是→bú but 不去→bù, 不算→bù |
| 一 + 4th tone → yí | 3/12 | 一个→yí but 一样→yī, 一下→yī |
| 一 + 1/2/3 → yì | 4/10 | 一起→yì but 一天→yī, 一些→yī |
| 不 + 1/2/3 → bù (no sandhi) | 8/8 | fairness control — citation IS right here, pypinyin scores full |

A rule engine would be 0/N or N/N; scattered means it's a curated bigram list. The `bu_T123`
control matters: the eval faults pypinyin *only* where the tone genuinely changes, and gives it
full marks where citation is correct.

**2. Grammatical 地/得 get the wrong reading — unassailable.** The adverbial 地 (高兴地) and the
V得C complement 得 (看得见) are read as the neutral syllable `de`; pypinyin prints `dì`/`dé` in
**9/10** cases. This is *not* sandhi — it's the wrong lexical reading for the grammatical role,
wrong under every convention. And 得 is *itself* inconsistent: `听得懂`→`de` (right) while
`看得见`→`dé` (wrong), identical grammar. (The `control` bucket confirms pypinyin *can* read the
same characters correctly in lexical contexts — 目的→`mù dì`, 觉得→`jué de` — which is exactly
why the particle misreads are a defect, not a limitation.)

**3. Bisyllabic third-tone sandhi — a coverage gap, not a defect.** Spoken T3+T3→T2+T3 (你好→ní
hǎo) is shown as citation on **all 18/18**. Harm is **weak**: this is the defensible-convention
case. Reported as a product decision — *should the ruby show what's written (citation) or what's
said (spoken)?* — not scored as broken.

**4. Reduplication (secondary).** Neutral 2nd syllable (谢谢→xièxie) kept at full tone on 8/9.
Held secondary because some dictionaries do mark the full tone.

**Control = 12/12.** The lexical-polyphone floor (银行 yín háng, 长江 cháng jiāng, 校长 xiào
zhǎng, 重要/重复 the zhòng/chóng split) is perfect. The eval passes exactly where pypinyin is
right, so the defect numbers above are not an artefact of a test rigged against pypinyin.

## We tried the obvious fix: pypinyin's own `ToneSandhiMixin`

pypinyin 0.55 ships a `contrib.tone_sandhi.ToneSandhiMixin`. Wiring it in is the first thing a
reader will ask about, so the eval scores it too. It is a **partial** remedy, and lopsidedly so:

- 一/不 sandhi: recovers **22/36** — but concentrated in 不+T4 (13/14); it recovers **0 extra**
  for 一+T4 (still 3/12, identical to baseline). So it does *not* generalise across the very
  rule it targets.
- Neutral particles 地/得: recovers **0/10** — the mixin doesn't touch them at all.
- Bisyllabic T3: recovers **7/18** — partial, and (per the earlier probe) it only fires on
  a small curated set of dictionary words (你好, 可以), not by rule (很好, 老虎, 小狗 unchanged).

So the mixin is not a drop-in fix — it closes under half the sandhi gap and none of the
neutral-particle gap.

## Decision

**The tone marks need a small rule-based post-pass over the per-hanzi output of
`pinyin_segments`; pypinyin `Style.TONE` alone (with or without the mixin) is not
display-safe.** A deterministic pass can fix the two unassailable classes cleanly:

- **一/不 sandhi** is fully rule-governed given the *following* syllable's tone (which the
  segmenter already has per character) → apply it uniformly instead of relying on lexicalised
  coverage.
- **Grammatical 地/得** → `de` when acting as the adverbial/complement particle.

And **citation-vs-spoken for pure third-tone sandhi should be an explicit product choice** — it
is currently citation by default (0/18 spoken coverage), which is defensible but was never a
decision. If the product wants the ruby to model *speech*, third-tone sandhi joins the post-pass;
if it wants to model the *written* citation reading, it stays and the sandhi rule is taught
separately. The eval does not pre-decide this — it surfaces it.

Nothing here is wired into production yet: this surface **measures and localises** the Phase-2
gap `tools.py` already acknowledged, and gives the post-pass a before/after target (一/不 12/36 →
36/36, 地/得 1/10 → 10/10, with T3 gated on the product decision).

## Honest scope

- Gold is hand-authored over common words; it establishes the *existence and shape* of the
  inconsistency, not a corpus-wide error rate. The 一/不 and 地/得 rules are unambiguous, so
  their golds are not opinions; the T3 and reduplication golds encode a convention choice, which
  is exactly why they're framed as gap/secondary rather than defect.
- `pinyin_segments` and `_tone_pinyin` share the same `Style.TONE` marks — the eval asserts they
  agree on every case (they do) and scores the shared output once, rather than inventing a
  distinction between the two surfaces.
- **儿化** (花儿→huār) is a genuine ruby-*model* limitation, not a pypinyin miss: one spoken
  syllable can't be shown under one of two hanzi in a one-pīnyīn-per-hanzi ruby. Excluded from
  scoring and stated plainly, so it isn't mistaken for a defect the post-pass could fix.
