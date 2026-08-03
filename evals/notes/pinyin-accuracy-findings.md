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

## Decision — what shipped, and why only that

The first draft of this note promised a post-pass taking "一/不 12/36 → 36/36, 地/得 1/10 → 10/10."
Working through the implementation **disproved that target**: two of the three classes can't be
fixed by a character-level rule without regressing real strings. So the shipped change is
narrower and precise, and the eval now guards it (a `sandhi_no_apply` regression bucket, §1b).

**✅ Shipped — 不 tone sandhi (不 → bú before a 4th tone).** This is the one rule fully governed by
the *following* syllable's citation tone, which the segmenter already has. Implemented in
`tools._apply_bu_sandhi`, shared by both `_tone_pinyin` and `pinyin_segments` so the ruby and the
`/api/pinyin` string can't diverge (`seg_agrees` stays true). It fires **only where pypinyin
emits a full-tone `bù`** — which automatically skips the V不C potential-complements it already
renders `bú`/neutral (看不见, 差不多, 买不到), the cases that would need grammar to handle. Result:
`bu_T4` **5/14 → 14/14**, and on the 15-case regression guard it changes exactly **one** string —
`说不定` (`shuō bù dìng` → `shuō bú dìng`), a fixed expression where pypinyin's own `bù` isn't the
neutral standard either, so no *correct* value is broken (lateral, documented in §1b).

**⛔ Deliberately NOT auto-fixed — 一 sandhi.** Not rule-governed by the neighbouring tone: 一 is
cardinal (一个 → yí) in some contexts and ordinal/final (一月, 一楼, 第一, 星期一 → yī) in others,
and only the cardinal takes sandhi. A following-tone rule would wrongly change the ordinals, and
pypinyin is *already* wrong on some (一月 → yí yuè). Correct handling needs POS/context, so 一 is
left to pypinyin (yi_T4 3/12, yi_T123 4/10 — still citation-inconsistent, documented not fixed).

**⛔ Deliberately NOT auto-fixed — grammatical 地/得.** Real defect (1/10), but the adverbial 地 /
V得C 得 (`de`) are **indistinguishable at the character level** from lexical 地方/阵地/得到 (which
pypinyin gets *right*). A blanket 地/得 → de would regress those. Needs POS. Left to pypinyin.

**Decision, not a defect — pure third-tone sandhi.** Citation by default (0/18 spoken coverage).
If the product wants the ruby to model *speech* (你好 → ní hǎo), T3 sandhi joins the post-pass; if
it wants the *written* citation reading, it stays and the rule is taught separately. The eval
surfaces this, unchanged, rather than pre-deciding it.

Net: a small, safe, fully-understood fix for the highest-frequency class (不 negation), with the
eval left as a permanent before/after + regression guard. The remaining classes are localised and
their fix scoped to "needs a POS-aware pass," not hand-waved as "apply the rule."

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
