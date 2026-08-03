# Pīnyīn-accuracy eval — `tools.pinyin_segments` / `_tone_pinyin`

The ruby a learner reads (`汉字` with pīnyīn underneath, in both coaches) and the `/api/pinyin` string come from pypinyin `Style.TONE` — **citation tones**. Wrong pīnyīn under a hanzi teaches a wrong pronunciation, so we score whether the displayed tone is the one the learner should say. **Fully deterministic** — no model calls, no judge — over a hand-authored gold set. This surface both **diagnosed** the gap and now **guards a shipped fix** (the 不-sandhi post-pass in `tools.py`), before → after below.

> **Framing (what is and isn't a defect).** Citation tones are a *defensible* dictionary convention, so we do **not** headline "pypinyin doesn't apply sandhi." The diagnosis headlined **inconsistency**: pypinyin applies the *same* rule to some words and not others (不是→bú but 不去→bù), wrong under citation **or** spoken convention. The pure third-tone gap (你好→nǐ hǎo) is a **coverage gap under the spoken-tone product choice** (weak harm), not a defect — surfaced as a decision, not pre-made.

**Outcome — shipped the one rule that's safe to apply positionally; the other two need POS we don't have.** The diagnosis found 一/不 sandhi applied to only **12/36** (0.33) syllables, scattered *within* each sub-rule — a defect under any convention. But only **不-sandhi** is rule-governed by the following syllable's tone alone:

- **✅ Shipped — 不 → bú before a 4th tone.** `bu_T4` goes **5/14 → 14/14** with **1** regression on the 15-case guard (`sandhi_no_apply`). Fires only where pypinyin emits a full-tone `bù`, so it skips the V不C potential-complements it already handles (看不见→bú).
- **⛔ Not auto-fixed — 一 sandhi.** Context-dependent (cardinal 一个→yí vs ordinal 一月/第一→yī): a following-tone rule would misfire on ordinals, and pypinyin is *already* wrong on some (一月→yí yuè). Needs POS. Left as citation (yi_T4 3/12, yi_T123 4/10).
- **⛔ Not auto-fixed — grammatical 地/得.** Adverbial 地 / V得C 得 are `de`, but they're indistinguishable at the character level from lexical 地方/得到 (which pypinyin gets right). A blanket rule would regress those. Needs POS. (1/10 correct.)
- **decision, not a defect — pure T3** (你好→nǐ hǎo): citation by default, 0.00 spoken coverage. Ship spoken-tone T3 only if the product wants the ruby to model speech over the written citation reading.

pypinyin's own `ToneSandhiMixin` was the obvious alternative — rejected as a partial, lopsided remedy (recovers 22/36 of 一/不 but **0** of the neutral particles, and doesn't generalise even across 一+T4). The targeted 不 rule is smaller and fully understood.

Sanity floor: the **control** bucket (lexical polyphones — 银行, 长江, 目的, 觉得) scores **1.00** (12/12). The test isn't rigged against pypinyin — it passes exactly where pypinyin is right.

Dataset: **117** cases (93 scored + 15 regression-guard). Ruby marks match the `/api/pinyin` marks on every case (✓). See `results/README.md` to re-derive any number.

## 1. 一/不 sandhi — diagnosis (before) and the shipped 不 fix (after)

`before` = bare pypinyin; `after` = production now (with the 不-sandhi post-pass). The diagnosis was the **spread inside a single sub-rule** — a rule engine would be 0/N or N/N, never scattered. The fix makes 不+T4 uniform; 一 is deliberately left to pypinyin.

| Sub-rule | before | after | was inconsistent? | mixin |
|---|---|---|---|---|
| 不 + 4th tone → bú  ✅ fixed | 5/14 | 14/14 | **yes** | 13/14 |
| 一 + 4th tone → yí  ⛔ needs POS | 3/12 | 3/12 | **yes** | 3/12 |
| 一 + 1/2/3 → yì  ⛔ needs POS | 4/10 | 4/10 | **yes** | 6/10 |
| 不 + 1/2/3 → bù (no sandhi; control) | 8/8 | 8/8 | n/a (control) | 8/8 |

`bu_T123` is a **fairness control**: when no sandhi applies, citation IS correct and pypinyin scores full marks — the eval only faults it where the tone genuinely changes.

## 1b. Regression guard — the 不 fix changed nothing it shouldn't

The `sandhi_no_apply` bucket (15 cases) is where a naïve rule would break correct output: 一 ordinals (一月/第一/一号), 不 in V不C/V不V (看不见/差不多/对不对), and lexical 地/得 (阵地/目的地/值得). The shipped 不 rule must leave every one **unchanged** — and it changes **1**:
- `说不定`: `shuō bù dìng` → `shuō bú dìng` (ideal `shuō bu dìng`). A V不C fixed expression where pypinyin emits full `bù`; the rule applies general sandhi. **Lateral, not a regression** — neither `bù` nor `bú` is the neutral-standard `bu`, so no *correct* value was broken.

## 2. Grammatical neutral particles 地 / 得 — diagnosed, NOT auto-fixed (needs POS)

The adverbial 地 and V得C 得 are the neutral `de`; pypinyin prints `dì`/`dé`. This is a real defect, but **not** shippable as a character rule: 高兴**地**(de) is indistinguishable from 阵**地**(dì) / 目的**地**(dì) without knowing the grammatical role. Left to pypinyin.

| Sub-rule | correct | rate | mixin |
|---|---|---|---|
| 地 adverbial → de | 0/5 | 0.00 | 0/5 |
| 得 (V得C complement) → de | 1/5 | 0.20 | 1/5 |

Note 得 is *also* internally inconsistent — `听得懂`→`de` (right) while `看得见`→`dé` (wrong), same V得C grammar. Wrong renderings (still present — not targeted by the 不 fix):

- `高兴地` → pypinyin `gāo xìng dì`, should be `gāo xìng de`
- `慢慢地` → pypinyin `màn màn dì`, should be `màn màn de`
- `认真地` → pypinyin `rèn zhēn dì`, should be `rèn zhēn de`
- `开心地` → pypinyin `kāi xīn dì`, should be `kāi xīn de`
- `轻轻地` → pypinyin `qīng qīng dì`, should be `qīng qīng de`
- `看得见` → pypinyin `kàn dé jiàn`, should be `kàn de jiàn`
- `跑得快` → pypinyin `pǎo dé kuài`, should be `pǎo de kuài`
- `说得好` → pypinyin `shuō dé hǎo`, should be `shuō de hǎo`
- `走得慢` → pypinyin `zǒu dé màn`, should be `zǒu de màn`

## 3. Third-tone sandhi, bisyllabic (coverage gap — a product choice, not a defect)

Spoken T3+T3 → T2+T3 (你好 → ní hǎo). pypinyin shows citation on **18/18** — coverage of the spoken form is **0.00**. Harm is **weak**: marking citation tones and teaching the sandhi rule separately is a legitimate convention. This is surfaced as a decision — *do we want the ruby to show what's written (citation) or what's said (spoken)?* — not scored as broken. (mixin recovers 7/18.)

## 4. Reduplication (secondary — soft gold)

Neutral 2nd syllable (谢谢 → xièxie): pypinyin keeps full tone on **8/9**. Kept **secondary** — some dictionaries do mark the full tone, so this is a weaker claim than 地/得.

## 5. Carried but not scored (honesty)

- **sandhi_no_apply** (15 cases): the regression guard in §1b — scored only for whether the post-pass leaves them unchanged, not for pypinyin's absolute correctness (some, like 一月→yí yuè, are pre-existing pypinyin 一 errors that reinforce why 一 isn't auto-fixed).
- **3+ stacked third tones** (我很好, 买手表, 请你给我, 很勇敢): realisation is prosody/grouping-dependent and genuinely contested — scoring it would measure our opinion, not a defect.
- **儿化** (花儿, 玩儿, 一点儿, 这儿, 那儿): 花儿 → huār is one spoken syllable, but `pinyin_segments` is one-pīnyīn-per-hanzi by contract, so erhua is **unexpressible** in the ruby — a structural model limitation, not a pypinyin miss.
