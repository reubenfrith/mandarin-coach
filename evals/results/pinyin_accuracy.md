# Pīnyīn-accuracy eval — `tools.pinyin_segments` / `_tone_pinyin`

The ruby a learner reads (`汉字` with pīnyīn underneath, in both coaches) and the `/api/pinyin` string come from pypinyin `Style.TONE` — **citation tones**. Wrong pīnyīn under a hanzi teaches a wrong pronunciation, so we score whether the displayed tone is the one the learner should say. **Fully deterministic** — no model calls, no judge — over a hand-authored gold set.

> **Framing (what is and isn't a defect).** Citation tones are a *defensible* dictionary convention, so we do **not** headline "pypinyin doesn't apply sandhi." We headline **inconsistency**: pypinyin applies the *same* rule to some words and not others (不是→bú but 不去→bù), which is wrong under citation **or** spoken convention. The pure third-tone gap (你好→nǐ hǎo) is reported as a **coverage gap under the spoken-tone product choice** (weak harm), not a defect — that decision is surfaced to you, not pre-made.

**Decision — the tone marks need a rule-based post-pass; pypinyin `Style.TONE` alone is not display-safe.** Two unassailable defect classes, independent of the citation-vs-spoken question:

1. **一/不 sandhi is inconsistent** — where sandhi should change the citation form, pypinyin applies it to only **12/36** (0.33) syllables, scattered *within* each sub-rule (inconsistent: bu_T4, yi_T123, yi_T4). Same rule, different output, decided only by which bigram is lexicalised.
2. **Grammatical 地/得 get the wrong reading** — the adverbial 地 and the V得C complement 得 are the neutral syllable `de`, but pypinyin prints `dì`/`dé` in **9/10** cases. Not sandhi — the wrong lexical reading.

pypinyin's own `ToneSandhiMixin` is a **partial** remedy (recovers 22/36 of the 一/不 cases and 1/10 of the neutral-particle cases — see the per-rule tables), so it is not a drop-in fix. **Recommendation:** add a small rule-based sandhi/neutral-tone post-pass over the per-hanzi marks in `pinyin_segments`, and make citation-vs-spoken for pure T3 an explicit product choice (currently citation by default, 0.00 coverage of the spoken form).

Sanity floor: the **control** bucket (lexical polyphones pypinyin resolves — 银行, 长江, 目的, 觉得) scores **1.00** (12/12). The test is not rigged against pypinyin — it passes exactly where pypinyin is right.

Dataset: **102** cases (93 scored). Ruby marks match the `/api/pinyin` marks on every case (✓). See `results/README.md` to re-derive any number.

## 1. 一/不 sandhi — consistency (the headline)

`applied` = pypinyin already prints the sandhi form. The story is the **spread inside a single sub-rule**: a rule engine would be 0/N or N/N, never scattered.

| Sub-rule | applied | rate | inconsistent? | mixin recovers |
|---|---|---|---|---|
| 不 + 4th tone → bú | 5/14 | 0.36 | **yes** | 13/14 |
| 一 + 4th tone → yí | 3/12 | 0.25 | **yes** | 3/12 |
| 一 + 1/2/3 → yì | 4/10 | 0.40 | **yes** | 6/10 |
| 不 + 1/2/3 → bù (no sandhi; control) | 8/8 | 1.00 | n/a (control) | 8/8 |

The `bu_T123` row is a **fairness control**: when no sandhi applies, citation IS correct and pypinyin scores full marks — the eval only faults it where the tone genuinely changes.

## 2. Grammatical neutral particles 地 / 得 (unassailable defect)

| Sub-rule | correct | rate | mixin recovers |
|---|---|---|---|
| 地 adverbial → de | 0/5 | 0.00 | 0/5 |
| 得 (V得C complement) → de | 1/5 | 0.20 | 1/5 |

Note 得 is *also* internally inconsistent — `听得懂`→`de` (right) while `看得见`→`dé` (wrong), same V得C grammar. Wrong renderings:

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

- **3+ stacked third tones** (我很好, 买手表, 请你给我, 很勇敢): realisation is prosody/grouping-dependent and genuinely contested — scoring it would measure our opinion, not a defect.
- **儿化** (花儿, 玩儿, 一点儿, 这儿, 那儿): 花儿 → huār is one spoken syllable, but `pinyin_segments` is one-pīnyīn-per-hanzi by contract, so erhua is **unexpressible** in the ruby — a structural model limitation, not a pypinyin miss.
