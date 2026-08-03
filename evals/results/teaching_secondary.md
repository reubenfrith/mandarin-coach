# Teaching-quality — misleading SECONDARY content

9 real coach replies; judge = **gpt-4o** (independent, temp 0). Checks the axis no other surface sees: factual errors in the reply's SUPPORTING content (hints, drill answers, example tables, measure-word choices, exception lists) — the headline correction is out of scope. **Gold = an expert's independent blind labels** (4/9 replies carry a secondary error), so this measures whether the judge catches what a human caught — it is NOT self-referential.

## Can the judge find the expert's errors?

- **Recall: 3/4** known secondary errors caught — **missed A02**.
- **Precision: 60%** (3 true / 5 flagged; false alarms on A01, A14).
- Agreement 67%, Cohen's κ **+0.34** vs the expert.

> Recall is the headline: a secondary error is spoken to the learner as fact, so a **miss** is the dangerous outcome. But read each flag's *content* below — a flag that trips for the wrong reason isn't really a catch.

## Per-case — judge vs expert (does it flag for the RIGHT reason?)

| id | grammar | gold | judge | verdict |
|---|---|---|---|---|
| A01 | 把 (bǎ) disposal construction | clean | error | ⚠️ false alarm |
| A02 | 被 (bèi) passive construction | error | clean | ❌ MISSED |
| A05 | 过 (guò) experiential aspect | clean | clean | ✅ clean |
| A07 | Measure words (量词) | error | error | ✅ caught |
| A08 | 在/正在 (zài/zhèngzài) progressive aspect | error | error | ✅ caught |
| A10 | 的 / 得 / 地 (de) distinction | clean | clean | ✅ clean |
| A11 | 比 (bǐ) comparison | clean | clean | ✅ clean |
| A14 | 两 (liǎng) vs 二 (èr) | clean | error | ⚠️ false alarm |
| A06 | 是……的 (shì...de) emphasis construction | error | error | ✅ caught |

## Detail — what each side flagged

### A01 — 把 (bǎ) disposal construction
- **Judge:** The drill answer for '他把门打______了。 (opened)' is given as '开', but it should be '开开' or '开了'. In standard Mandarin, '开' alone is not typically used as a resultative complement in this context.

### A02 — 被 (bèi) passive construction
- **Expert:** The correction is right and both rewrites are good, but the stated rule is overstated: "一个句子只能选择其中一种结构" is not true. The 被…把… pattern is grammatical — 他被人把钱偷走了、我被他把眼镜打破了 — with 被 preceding 把 and the subject as the affected party. Fine as a beginner heuristic, wrong as an absolute law.
- **Judge:** (did not flag)

### A07 — Measure words (量词)
- **Expert:** The rule and the 三本书 correction are right, but the hint is wrong: it says cats and people both take 个. Cats take 只 — 两只猫. 个 is correct for 人 and 苹果.
- **Judge:** The claim '猫和人都用 **个**' is incorrect. The measure word for '猫' (cat) is '只', not '个'.
- **Judge:** The prompt '两 ___ 猫 (cat)' should use '只' as the measure word for '猫', not '个'.

### A08 — 在/正在 (zài/zhèngzài) progressive aspect
- **Expert:** 我知道答案 is the right fix and the 看/吃 contrast is good, but the summary list is wrong to include 想. 想 in its "think about / miss" sense is an activity verb and takes 在 freely: 我在想这件事、我在想办法、我在想你. Only the "hold the opinion that" sense resists it. 知道、喜欢、爱、认识 are fine on that list.
- **Judge:** The claim "想（think）" is a stative verb and cannot be used with '在' is incorrect. '想' can be used with '在' when it means 'thinking about' or 'considering', as in '我在想这个问题。'

### A14 — 两 (liǎng) vs 二 (èr)
- **Judge:** The claim '现在是 __ 点。' should use '两' is incorrect. It should be '二' because time uses '二' for hours, e.g., '现在是二点。'

### A06 — 是……的 (shì...de) emphasis construction
- **Expert:** he 是……的 half is correct: 你是怎么来的 for asking means, with 了 excluded, and both drill answers are right. But the summary table marks 你怎么来了这里 as for 'why did you come here.' That sentence is awkward — 了 doesn't sit comfortably between the verb and a place object. Natural options are 你怎么来这里了? or 你怎么会来这里？, and 你为什么来这里？(also listed) is fine.
- **Judge:** The claim "'Why did you come here?' | 你怎么来了这里？ / 你为什么来这里？" is incorrect. The sentence '你怎么来了这里？' is not a standard way to ask 'Why did you come here?' in Mandarin. The correct form should be '你为什么来了这里？' or '你为什么来这里？' without '了'.
- **Judge:** The claim "问已完成动作的 方式/手段 → 用 是……的 结构，不用 了。" is overstated. While 是……的 is commonly used for emphasis on means or manner, using 了 is not incorrect and can be used in some contexts to indicate completion or change of state.

## Caveats

- **n=9, one expert labeller.** Recall/precision are over a handful of known errors — directional, not a stable rate. The point is feasibility: *can* the judge see this class at all?
- **This is open-ended grammar correctness**, the hardest thing to ask of a judge. A miss doesn't mean the axis is hopeless — a stronger/reasoning judge model or corpus-grounded checks are the next lever. Report the miss honestly rather than hiding it.
- **The gold is derived** from the expert's `explains_why=False` labels (they failed those replies on a wrong supporting claim); the note is their verbatim rationale.
