# Corpus harm — EMPIRICAL confirmation (does the coach actually misfire?)

Fed each candidate rule's proposed CORRECT sentence to the real coach (**deepseek**, 2x each); a rule is CONFIRMED harmful iff the coach marked that correct sentence WRONG in >=1 run (detector = gpt-4o). Behaviour, not opinion — this converges the over-flagged candidate list (69) to what the coach actually gets wrong.

## Confirmed harmful: 13/69

| rule | correct sentence | coach misfired | fix |
|---|---|---|---|
| `gr_youdianr_yidianr` 有点儿 (yǒudiǎnr) vs 一点儿 (yìdiǎnr) | 这个有点儿便宜。 | 2/2: 你的句子语法上没有错误，但用词有点儿不自然。 | 有点儿 + 形容词多表示轻微抱怨/不理想（有点儿贵）。当“便宜”被视为不理想时，也可以说“有点儿便宜”。形容词 + 一点儿用于比较，表示“再/更……一点儿”（便宜一点儿）。不要把“一点儿”放在形容词前（不用：一点儿贵）。 |
| `gr_jiu_cai` 就 (jiù) vs 才 (cái) | 他九点才来了。 | 2/2: **Corrected sentence:** 他九点才来。 | Revise the note to: “With 才, don’t put 了 right after the verb in simple past statements (他九点才来). Sentence-final 了 is OK  |
| `gr_le_negation_drop` 没 negates a completed action and drops 了 | 他没来了。 | 2/2: 你的句子 **“他没来了”** 有一个很常见的语法错误。 | Say: “To negate a completed action, use 没(有) + V and do not use the perfective 了 right after the verb: 我没去 (not 我没去‘了’ f |
| `gr_zhiyao_jiu` 只要……就…… (as long as) | 只要你是学生，门票才五十块。 | 2/2: 你的句子意思很清楚，但有一个常见的语法搭配错误。 | Common mistake: After 只要, link the result with 就 (只要…就…). Don’t use 才 to mean “only then” (that pattern is 只有…才…). Note: |
| `gr_yi_jiu` 一……就…… (as soon as) | 你一到家给我打电话。 | 2/2: **错误：** 缺少 **就** (jiù) | Revise the note to: “不要用‘一……然后……’。一般用‘一……就……’。口语里，尤其在要求/提醒时，可以省略‘就’（如：你一到家给我打电话），但用‘就’更保险：你一到家就给我打电话。” |
| `gr_wulun_dou` 无论/不管……都…… (no matter) | 不管天气怎么样，我去。 | 2/2: 有一个小问题让它听起来不太自然。 | Edit to: “无论/不管 + … usually takes 都/也 in the main clause. Use 都/也 to sound clear and natural (especially in writing), bu |
| `gr_cong_dao` 从……到…… (from ... to) | 我九点到五点上班。 | 2/2: 你的句子意思很清晰，但缺少一个关键的词。 | Change the note to: “Don’t put the time range after the verb (e.g., 我工作九点到五点 is unnatural). Note: A 到 B without 从 is als |
| `gr_duo_approx` Number + 多 approximation | 一百块多。 | 2/2: 你的句子 **一百块多** 需要调整一下语序。 | Teach both orders: 多 can go after the number or after the measure word: 三十多岁 / 三十岁多；一百多块 / 一百块多。Don’t put 多 before the n |
| `gr_le_change` 了 (le) as change of state (sentence-final) | 我饿。 | 1/2: Your sentence **我饿** is understandable, but it sounds a bit off to a native spea | Add: “Sentence-final 了 highlights a new/changed situation; it’s not required if you’re simply stating a current fact.” U |
| `gr_hui_neng_keyi` 会 / 能 / 可以 (huì/néng/kěyǐ) modals | 我能说三种语言。 | 1/2: 你的句子基本正确，但有一个**很细微却很关键**的地方可以改进。 | Change the “Common mistake” to: “For learned skills, 会 is more natural; 能 is also used and not wrong. Use 可以 (not 会) for |
| `gr_yinwei_suoyi` 因为……所以…… (yīnwèi...suǒyǐ) cause and result | 因为下雨，我没去。 | 1/2: 语法上不被判错，但不够地道，有“英语直译”的味道 | Explanation: 因为…所以… is a common and natural pairing, but in everyday Chinese 所以 is often optional after 因为; you can also |
| `gr_suiran_danshi` 虽然……但是…… (suīrán...dànshì) although | 虽然很累，我很开心。 | 1/2: Your sentence is very close, but it has a classic **"虽然...但是..."** issue. | Revise explanation: “虽然 (although) often pairs with 但是/可是 (but), but 但是/可是 is optional when the contrast is clear. Both  |
| `gr_gei_coverb` 给 (gěi) + recipient + verb (for / to) | 我打电话给你。 | 1/2: 听起来像是英语直译 | Teach both common orders and note verbs that don’t use 给: 给 + recipient + 动词, and also 动词 + 给 + recipient are both commo |

## Not confirmed (56) — coach affirmed the sentence in all 2 runs

`gr_ba_disposal`, `gr_bei_passive`, `gr_shi_de`, `gr_measure_words`, `gr_zai_progressive`, `gr_de_complement`, `gr_de_di_de`, `gr_time_before_place`, `gr_duration_complement`, `gr_liang_er`, `gr_resultative`, `gr_directional`, `gr_haishi_huozhe`, `gr_double_le`, `gr_zhe_durative`, `gr_yao_le_imminent`, `gr_ma_question`, `gr_ba_suggestion`, `gr_hui_de_certainty`, `gr_xiang_yao_want`, `gr_yinggai_should`, `gr_dei_must`, `gr_ji_duoshao`, `gr_meiyou_comparison`, `gr_yuelaiyue`, `gr_yue_yue`, `gr_bi_degree_diff`, `gr_ruguo_jiu`, `gr_zhiyou_cai`, `gr_chule_yiwai`, `gr_xian_ranhou`, `gr_bushi_ershi`, `gr_deshihou`, `gr_yiqian_yihou`, `gr_dao_resultative`, `gr_jian_perception`, `gr_gei_resultative`, `gr_qilai_inchoative`, `gr_xiaqu_continue`, `gr_li_distance`, `gr_weile_purpose`, `gr_yong_instrument`, `gr_zai_location_verb`, `gr_shi_identity`, `gr_zai_location`, `gr_di_ordinal`, `gr_mei_every`, `gr_xie_some`, `gr_money_spoken`, `gr_adj_predicate_hen`, `gr_dou_all`, `gr_zai_you_again`, `gr_zhi_only`, `gr_tai_le`, `gr_verb_reduplication`, `gr_lai_qu_purpose`

## Caveats

- Coach runs at temperature; 2 samples/rule is a first cut. A rule marked 'not confirmed' may still misfire sometimes (false negatives possible); a 'confirmed' one genuinely misfired at least once (real). Raise `samples` to tighten.
- Assumes gpt-5's proposed sentence is actually correct — spot-check the confirmed list before editing `data/grammar_rules.json`.
