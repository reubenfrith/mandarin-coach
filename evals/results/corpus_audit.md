# Corpus-quality audit — reference grammar rules

98 rules audited by **gpt-5** (frontier judge, temp 0). Flags `explanation` / `common_mistake` claims that are factually wrong or materially OVER-BROAD in standard Mandarin — the class that seeds SYSTEMATIC coach errors (a corpus error propagates to every reply grounded on the rule). **First-pass triage for a human to adjudicate, not an oracle** — keep/reject each flag.

## Flagged: 71/98  ·  major 45  ·  minor 26

_major = would teach an advanced learner something false; minor = pedantic edge case._

| rule | severity | the problem (judge — verify) |
|---|---|---|
| `gr_adj_predicate_hen` Adjective predicate takes 很, not 是 | major | “An adjective predicate needs a degree adverb (usually a bland 很) and NO 是: 他很高.” — This is too absolute. Bare adjectives are fine in several common contexts (e.g., negation: 他不高;  |
| `gr_ba_suggestion` 吧 (ba) suggestion / supposition | major | "incorrect: 我们走吗，现在很晚了。" — This sentence is not ungrammatical. With 吗 it’s a neutral yes–no question (Are we leaving?), not a softened suggestion. Minimal fix: Don’t label it incor |
| `gr_bei_passive` 被 (bèi) passive construction | major | Claim in common mistake: "...leaving the verb bare with no complement." Why this is over-broad/wrong: 被-sentences can legitimately have a bare verb (no resultative complement and n |
| `gr_bi_degree_diff` 比 + adj + amount of difference | major | "With 比, the amount of difference goes AFTER the adjective" — This is over-broad. With numeral–measure phrases and dimensional adjectives, the amount can also precede the adjective |
| `gr_chule_yiwai` 除了……以外 (besides / except) | major | "除了……(以外) pairs with 都 (except: everyone else) or 还/也 (besides: in addition)." – This sounds mandatory, but 除了…(以外) can also combine with other structures (e.g., 没/没有/没人, 只有/就, 其他/ |
| `gr_cong_dao` 从……到…… (from ... to) | major | Claim: "Using 到 alone" [is a common mistake]. Why wrong: In ranges, A到B without 从 is fully grammatical and very common for time and space (and other ranges). Examples: 我九点到五点工作; 北京 |
| `gr_dao_resultative` 到 as a resultative (找到 / 看到) | major | "Omitting 到, so successful attainment is not expressed." — This is over-broad. With some verbs (e.g., 找/看/听/等), leaving off 到 does lose the attainment meaning (找→‘look for’ vs 找到→‘ |
| `gr_dei_must` 得 (děi) must / have to | major | "incorrect: 现在很晚了，我不得走。 → correct: 现在很晚了，我得走了。" — 我不得走 is not ungrammatical; 不得 means “must not/are not allowed to,” so this sentence can be correct in contexts (e.g., 宿舍关门了，我不得走). |
| `gr_deshihou` ……的时候 (when / while) | major | "Using an English-style front 'when' without 的时候." — This is over-broad. In standard Mandarin, 当 can function as a conjunction without 的时候 when followed by a full clause (e.g., 当你准 |
| `gr_di_ordinal` 第 (dì) ordinal numbers | major | "Omitting 第 for an ordinal (using a bare cardinal)." — This is over-broad. Many perfectly standard ordinals in Mandarin do not take 第, especially in naming/labeling contexts where  |
| `gr_double_le` Verb + 了 + object + 了 (ongoing up to now) | major | Claim: “Using one 了 and losing the 'and still continuing' meaning.” Why this is wrong/over-broad: Many perfectly correct ongoing-present sentences use only the sentence-final 了 and |
| `gr_gei_resultative` Verb + 给 + recipient (送给 / 还给) | major | 'Common mistake' note: 'Omitting 给 or misordering the recipient.' — Labeling omission of 给 as a mistake is over-broad and wrong for common transfer verbs like 送 and 还. In standard  |
| `gr_haishi_huozhe` 还是 (háishì) vs 或者 (huòzhě) — 'or' | major | Claim: "Using 或者 in a choice question or 还是 in a statement." — Labeling "还是 in a statement" as a mistake is wrong. 还是 is regularly used inside statements in embedded/indirect choic |
| `gr_hui_de_certainty` 会……的 future certainty | major | Common mistake: "Dropping 会 or the framing 的" — Treating the sentence-final 的 as required is over-broad. 的 adds a reassuring/insistent tone, but "他会来" (without 的) is fully grammati |
| `gr_hui_neng_keyi` 会 / 能 / 可以 (huì/néng/kěyǐ) modals | major | "Common mistake: Using 能 for learned skills" — In standard Mandarin, 能 can be (and often is) used to state ability/skill, e.g., 你能说中文吗? is natural; the preference is to use 会 when  |
| `gr_ji_duoshao` 几 vs 多少 (how many) | major | "多少 asks about larger or unknown quantities and needs no measure word (多少钱)." → Over-broad/wrong: With count nouns, 多少 typically takes a classifier (e.g., 多少本书, 多少个苹果). It can omit |
| `gr_jiu_cai` 就 (jiù) vs 才 (cái) | major | Common mistake: "Adding 了 after 才" — This labels grammatical sentences as wrong. In the ‘not until’ sense, 才 typically doesn’t take verbal 了 (他九点才来 is natural), but 了 can appear se |
| `gr_le_negation_drop` 没 negates a completed action and drops 了 | major | "Common mistake: Keeping 了 after 没 (没……了)." — Over-broad. 没…了 is perfectly grammatical in standard Mandarin in patterns like duration up to now or change of state, e.g. 我已经三天没吃饭了,  |
| `gr_liang_er` 两 (liǎng) vs 二 (èr) | major | 'Common mistake' note: "Using 二 before a measure word (二个人)." — This is over-broad. While 二个(人) is nonstandard (use 两个/两个人), 二 can precede measure words in several common, correct  |
| `gr_ma_question` 吗 (ma) yes/no question particle | major | Claim: "Do not use it when the sentence already contains a question word." Why: This is over‑broad. 吗 normally doesn’t appear with true wh‑information questions (哪儿/什么时候/为什么/怎么等),  |
| `gr_mei_every` 每 (měi) + measure word (every) | major | Claim: "Omitting the measure word after 每" (as a blanket mistake). Why over-broad: Many words can follow 每 without an extra classifier, e.g., 每天、每年、每月、每人, and measure-like words su |
| `gr_money_spoken` Spoken money (块 / 毛 / 分) | major | Claim: "Using written 元/角 in speech" [is a common mistake]. Why it’s wrong: 元 and 角 are acceptable in spoken Mandarin, especially in neutral/formal contexts (e.g., prices read out  |
| `gr_qilai_inchoative` 起来 — inception / 'seem' / recall | major | Example labeled as correct is ungrammatical/nonnative: “我突然想起来那个词了。” In resultative constructions with 起来, 了 should either follow the whole complement (想起来了) or the object should b |
| `gr_resultative` Resultative complements (看完, 听懂) | major | "Negate with 没 (没看完), not 不." — Over-broad. While factual non-achievement is negated with 没(有) (e.g., 我没看完), 不 is common and grammatical in potential complements to express inabili |
| `gr_ruguo_jiu` 如果……就…… (if ... then) | major | Claim: "如果 (+的话) in the condition clause pairs with 就 in the result clause: 如果你有时间，就来我家." Why over-broad: This implies 就 must appear after 如果, but in standard Mandarin 就 is optiona |
| `gr_shi_de` 是……的 (shì...de) emphasis construction | major | "Using 了 instead of 是……的 to highlight the time/place/manner of a known past event." — This overstates it as an error. Sentences with 了 that include time/place/manner are often perf |
| `gr_suiran_danshi` 虽然……但是…… (suīrán...dànshì) although | major | "Both are used together in Chinese." — Over-broad. 虽然 often pairs with 但是/可是, but 但是 can be omitted when the contrast is clear, and other markers (却/还是/但/不过) or no overt marker are |
| `gr_time_before_place` Word order: time and place before the verb | major | "Chinese puts time-when and place adverbials BEFORE the verb, not after: Subject + Time + Place + Verb + Object." — Over-broad. Place phrases often appear after the verb as the com |
| `gr_verb_reduplication` Verb reduplication (看看 / 休息休息) | major | Claim: "two-syllable ABAB (休息休息), NOT AABB." Why it’s over-broad: Many very common two-syllable verbs are separable VO verbs (离合词) and do not reduplicate as ABAB productively; inst |
| `gr_weile_purpose` 为了 (wèile) in order to | major | "Placing the purpose at the end, or using 因为 (because) for a purpose." — Labeling sentence-final purpose placement as a mistake is incorrect. Standard Mandarin allows the purpose a |
| `gr_wulun_dou` 无论/不管……都…… (no matter) | major | Claim: "Dropping 都/也" [is a common mistake]. Why over-broad/wrong: In standard Mandarin, 都/也 is common after 无论/不管, but it is not mandatory. Many perfectly natural sentences omit i |
| `gr_xian_ranhou` 先……然后…… (first ... then) | major | Common mistake note: "Reversing 先/然后 or omitting 先." — Labeling "omitting 先" as a mistake is over-broad. In standard Mandarin, 先 is often optional when the sequence is clear, and s |
| `gr_xiang_yao_want` 想 vs 要 (to want) | major | "Using 要 for a polite wish where 想 is more appropriate." — Over-broad. 要 is often perfectly acceptable and not impolite in many contexts (e.g., service encounters or casual equal-s |
| `gr_xiaqu_continue` 下去 — continue an action | major | Claim: "Using 下来 for 'continue', or 继续 awkwardly without the complement." Problem: 继续 does not require 下去 and is perfectly natural on its own (e.g., 老师让我们继续读; 请继续; 我们明天继续). The rea |
| `gr_yao_le_imminent` (快)要……了 imminent action | major | “The final 了 is required.” — Over-broad. In the imminent ‘要/快要/就要…了’ pattern, 了 is normally used to mark the impending change, and omitting it often shifts the meaning toward ‘want |
| `gr_yinwei_suoyi` 因为……所以…… (yīnwèi...suǒyǐ) cause and result | major | "Assuming that using both 'because' and 'so' is wrong, as it would be in English, and dropping 所以." — This implies that dropping 所以 is a mistake, but in standard Mandarin using onl |
| `gr_yiqian_yihou` 以前 / 以后 clause order | major | 'Common mistake' note: Following English order and putting 以前/以后 first. — Over-broad. 以前/以后 can appear sentence-initial when used as independent time adverbs meaning ‘previously/in |
| `gr_yong_instrument` 用 (yòng) + tool + verb (by means of) | major | Claim: "Following English 'with ...' order and putting the tool after the verb." Why it's wrong/over-broad: In Mandarin, placing the instrument as a postverbal 用-phrase is grammati |
| `gr_youdianr_yidianr` 有点儿 (yǒudiǎnr) vs 一点儿 (yìdiǎnr) | major | "Swapping them: 一点儿贵 or 有点儿便宜 in the wrong slot." — Labeling 有点儿便宜 as a blanket error is over-broad. 有点儿 often conveys a mildly negative/undesirable nuance, so 有点儿便宜 is perfectly n |
| `gr_yuelaiyue` 越来越 (yuèláiyuè) more and more | major | Claim: “越来越 + Adjective/Verb = more and more.” Why it’s over-broad: 越来越 can directly take adjectives and many stative/mental verbs (e.g., 喜欢/想/担心/懂), but it does not freely take dy |
| `gr_zai_location_verb` 在 + place + verb (do at a location) | major | "Common mistake: Following English order and putting the place after the verb." — This is over-broad. Many verbs naturally take 在+place after the verb (e.g., 我住在北京, 把书放在桌子上, 他站在门口) |
| `gr_zai_progressive` 在/正在 (zài/zhèngzài) progressive aspect | major | Claim: "This describes ongoing actions, not states." Why it's over-broad: 在/正在 can also appear with some state-like or situation predicates to mean “to be in the middle of that sta |
| `gr_zai_you_again` 再 vs 又 (again: future vs past) | major | "又 = again for a past/realised one" — This is over-broad. 又 can also mark expected/near-future or imminent repetition, especially with 要/会/能 or a future time adverbial, e.g., "明天又要 |
| `gr_zhi_only` 只 (zhǐ) only — before the verb | major | Claim: "Placing 只 after the verb, or using 就 for 'only'." — The blanket prohibition on using 就 for “only” is wrong. In standard Mandarin, 就 often means “only/just,” especially befo |
| `gr_zhiyao_jiu` 只要……就…… (as long as) | major | "Pairing 只要 with 才 (that belongs to 只有)." — Over-broad/wrong: In standard Mandarin, 只要…才… is attested and natural; it shifts the meaning from a sufficient condition to emphasizing  |
| `gr_ba_disposal` 把 (bǎ) disposal construction | minor | “The verb must be transitive …” — This is over‑broad. In standard usage, verbs that aren’t canonically transitive or are adjective‑like can appear in 把 sentences when they form a c |
| `gr_bushi_ershi` 不是……而是…… (not A but B) | minor | "Using 但是 instead of 而是 for a correction." — This overgeneralizes. 但是 can express the same correction/contrast if the second part is a full clause, e.g., 这不是茶，但是是咖啡/但是这是咖啡/但是它是咖啡.  |
| `gr_de_complement` 得 (de) degree/manner complement | minor | "If the verb has an object, repeat the verb: 他说汉语说得很好." — This is over-broad. You must repeat the verb only if the object stays after the verb; you can also front the object and no |
| `gr_de_di_de` 的 / 得 / 地 (de) distinction | minor | Claim: "得 links a verb to a complement of degree/result (走得慢)." Why over-broad/wrong: 得 also attaches to adjective predicates, not only verbs, e.g., 高兴得不得了, 累得要命, 冷得发抖. Minimal fix |
| `gr_directional` Directional complements (进来, 出去) | minor | "来/去 and directional verbs (上下进出回过) attach to a verb to show direction relative to the speaker" — Over-broad: 来/去 mark motion relative to the deictic center, which is usually the s |
| `gr_dou_all` 都 (dōu) all/both — before the verb, scope to its left | minor | Common mistake: "Placing 都 before the subject it quantifies, or after the verb." — The blanket ban on "after the verb" is over-broad: in standard Mandarin there are set patterns wh |
| `gr_duo_approx` Number + 多 approximation | minor | “Putting 多 before the number” (as a blanket mistake). In other valid structures, 多 can precede the number to mean “an extra N,” e.g., 再多三天, 多两个人, 多三块钱. Minimal fix: “In this ‘-odd/ |
| `gr_duration_complement` Duration complement (time how long) | minor | "Placing the duration before the verb like a time-when phrase (我两年学汉语)." — Over-broad. Preverbal duration is not always wrong in standard Mandarin: it is natural with negation to m |
| `gr_frequency_adverb` 常常 / 经常 frequency — before the verb | minor | Claim: “Placing the frequency adverb after the verb or at the end.” — stated as categorically wrong. Why over-broad: In V‑得 complement structures, frequency words can appear after  |
| `gr_gei_coverb` 给 (gěi) + recipient + verb (for / to) | minor | "Omitting 给, or following English order (verb before recipient) where the coverb is expected." — This overstates that placing the verb before the recipient is a mistake. In many ca |
| `gr_jian_perception` 见 for involuntary perception (看见 / 听见) | minor | "见 for involuntary perception (看见 / 听见)" — Calling 见 "involuntary" is over-broad. 见 as a resultative complement simply marks that the sensory event was achieved; it does not by its |
| `gr_lai_qu_purpose` 来/去 + verb phrase (come/go to do) | minor | Claim: "Inserting 为了 / an English 'to' marker between the motion and the purpose verb." Why over-broad: While placing bare 为了 right after 来/去 is generally ungrammatical or awkward  |
| `gr_le_change` 了 (le) as change of state (sentence-final) | minor | "It reports that something is now different from before." — Sentence‑final 了 can also mark an impending change, not only a state that is already true (e.g., 快下雨了, 要迟到了, 天要黑了). Mini |
| `gr_li_distance` 离 (lí) distance from | minor | "Using 从 for a static distance." — This is over-broad. While the structure "A 从 B 很近/很远" is ungrammatical (you should use 离), 从 can express distance in static statements when paire |
| `gr_measure_words` Measure words (量词) | minor | "Chinese requires a measure word between a number/demonstrative and a noun: Number + Measure Word + Noun." — This is over-broad. With numbers, many words are themselves measurement |
| `gr_meiyou_comparison` A 没有 B (那么) + adj — not as ... as | minor | "不比 (which means 'not necessarily more than')" — The phrase 'not necessarily more than' suggests it could still be more, which is wrong. 不比X高 means 'no taller than X' (i.e., not ta |
| `gr_shi_identity` 是 (shì) identity — no 是 before an adjective | minor | Claim: "It is NOT used before an adjective predicate — use 很 there instead." Why over-broad: In simple descriptive sentences this is correct, but 是 can appear before adjectives in  |
| `gr_tai_le` 太……了 (too / so) | minor | "Omitting 了 after 太" (as a blanket 'common mistake'). 了 is very common in the standalone/exclamatory 太… predicate, but it is not required in all uses of 太: e.g., attributive modifi |
| `gr_xie_some` 些 / 一些 / 这些 (some, plural) | minor | "It replaces number+MW and takes no measure word of its own." — Over-broad. In colloquial Mandarin, 个 can appear after 些/这些/那些 for emphasis (e.g., 一些个苹果, 这些个孩子; also 好些个… is common |
| `gr_ye_also` 也 (yě) also — before the verb | minor | Claim: "也 (also/too) goes before the verb or adjective, never at the end." Why over-broad: In full sentences, 也 is not sentence-final, but in common elliptical replies the predicat |
| `gr_yi_jiu` 一……就…… (as soon as) | minor | Claim: "Using 然后 for the immediate second event, or dropping 就." (specifically: "dropping 就") — This overstates that 就 is obligatory. In modern Mandarin, 就 is strongly preferred in |
| `gr_yinggai_should` 应该 (yīnggāi) should / ought to | minor | "Placing 应该 at the end like an English tag, or omitting it." — Omitting 应该 is not inherently a mistake in Chinese; speakers often leave it out to make an imperative or use other su |
| `gr_yue_yue` 越 A 越 B — the more ... the more | minor | "越 + Verb1 + 越 + Verb2/Adj = the more A, the more B" — This makes it sound like the first slot must be a verb, but in standard usage both slots can be verbs, adjectives, or even sh |
| `gr_zai_location` 在 (zài) to be located at | minor | "Using 有 or 是 for the location of a specific known thing." — Over-broad. 有 can appear in existential sentences with a place topic even when the noun is specific (e.g., 桌子上有我的手机/你要找 |
| `gr_zhe_durative` 着 (zhe) durative / accompanying state | minor | "It describes a persisting state, not a dynamic action in progress (that is 在)." — This is too absolute: in colloquial Mandarin, V+着+呢 (and with some verbs like weather verbs) can  |
| `gr_zhiyou_cai` 只有……才…… (only if) | minor | “Pairing 只有 with 就 (that belongs to 只要).” — Over-broad. In the conditional ‘only if’ pattern, 只有…才… is correct and 只有…就… is wrong, but 只有 also has a different meaning (‘only/there  |

## Detail — every flag (quote → problem → fix)

### `gr_adj_predicate_hen` — Adjective predicate takes 很, not 是  _(major)_
- **common_mistake:** Using 是 before the adjective, or leaving a neutral statement with a bare adjective.
- **flag:** “An adjective predicate needs a degree adverb (usually a bland 很) and NO 是: 他很高.” — This is too absolute. Bare adjectives are fine in several common contexts (e.g., negation: 他不高; A‑not‑A/questions: 他高不高/他高吗; exclamatives: 你高啊), and 是 can appear with adjectives when nominalized with 的 or used for emphasis (他是对的; 他是高，但是不壮). Minimal fix: “In simple neutral statements, an adjective predicate usually takes a degree adverb (often neutral 很) and not 是. Don’t use 是 as a copula before a bare adjective (他很高, not 他是高).”
- **flag:** “incorrect: 今天天气好。 → correct: 今天天气很好。” — 今天天气好 is not incorrect; it’s idiomatic and often used (though it can sound contrastive/contextual). Minimal fix: label it as a preference, e.g., “Neutral statement: 今天天气很好。 Bare adjective is also possible but often sounds contrastive: 今天天气好(啊).”

### `gr_ba_suggestion` — 吧 (ba) suggestion / supposition  _(major)_
- **common_mistake:** Using 吗 for a suggestion or a 'right?' supposition where 吧 is natural.
- **flag:** "incorrect: 我们走吗，现在很晚了。" — This sentence is not ungrammatical. With 吗 it’s a neutral yes–no question (Are we leaving?), not a softened suggestion. Minimal fix: Don’t label it incorrect; contrast meanings instead, e.g. 我们走吧，现在很晚了。(Let’s go; it’s late.) vs 我们走吗？现在很晚了。(Are we going to leave? It’s late.)
- **flag:** "Using 吗 for a suggestion or a 'right?' supposition where 吧 is natural." — Over-broad. Using 吗 isn’t a mistake per se; it changes the nuance from suggestion/supposition to a neutral confirmation question (e.g., 你是老师吗？). Minimal fix: "Using 吗 turns it into a neutral yes–no question; use 吧 to soften a suggestion (我们走吧) or to voice an assumption seeking confirmation (你是老师吧？)."

### `gr_bei_passive` — 被 (bèi) passive construction  _(major)_
- **common_mistake:** Combining 被 with 把 in one clause, or leaving the verb bare with no complement.
- **flag:** Claim in common mistake: "...leaving the verb bare with no complement." Why this is over-broad/wrong: 被-sentences can legitimately have a bare verb (no resultative complement and no 了), especially for habitual/generic statements or in formal/news style. Examples: 他经常被批评。/ 她常被人欺负。/ 嫌疑人被捕（headline/register). Minimal fix: Rephrase to "In one-off, event-focused passives, it’s more natural to show a result or completion (了, a resultative complement, a quantity/object, etc.). Bare verbs are fine in habitual/generic statements (经常/常/总是被...), and in formal/news style."

### `gr_bi_degree_diff` — 比 + adj + amount of difference  _(major)_
- **common_mistake:** Placing the amount before the adjective, or using 很/非常.
- **flag:** "With 比, the amount of difference goes AFTER the adjective" — This is over-broad. With numeral–measure phrases and dimensional adjectives, the amount can also precede the adjective, e.g. 他比我三岁大; 这条河比那条河三米宽; 他比我两公分高. Minimal fix: "In 比-comparisons the amount usually follows the adjective (高一点儿/高得多/高两公分). With numeral–measure phrases (三厘米/两岁/三米) and dimensional adjectives (高、矮、长、短、宽、厚、大、小、重等), the amount can go before or after the adjective: 他比我高两公分/他比我两公分高. Note that 一点儿/一些/得多 must follow the adjective."
- **flag:** "Common mistake: Placing the amount before the adjective, or using 很/非常." — This labels some correct sentences as errors and is too absolute. Preposing a numeral–measure amount (他比我两公分高) is fine, and 非常 can appear in 得-constructions (他比我高得非常多). Minimal fix: "Don’t put 很/非常 directly before the adjective in a 比-comparison (✗ 他比我很高). Use 更/还 or degree complements instead (他比我更高/高很多/高得非常多). Preposing a numeral–measure amount is acceptable with dimensional adjectives (他比我两公分高)."

### `gr_chule_yiwai` — 除了……以外 (besides / except)  _(major)_
- **common_mistake:** Dropping the paired 都/还/也 in the main clause.
- **flag:** "除了……(以外) pairs with 都 (except: everyone else) or 还/也 (besides: in addition)." – This sounds mandatory, but 除了…(以外) can also combine with other structures (e.g., 没/没有/没人, 只有/就, 其他/其余) or sometimes omit these adverbs without being ungrammatical. Minimal fix: "除了……(以外) often pairs with 都 for the ‘except’ meaning and with 还/也 for the ‘besides’ meaning, though other patterns like 除了他以外，没有人去了 / 除了他以外，其他人去了 / 除了他以外，就我们去了 are also common."
"Dropping the paired 都/还/也 in the main clause." – Presented as a blanket "mistake," but many correct sentences don’t use them (e.g., 除了他以外，没有人去了; 除了他以外，其他人去了). Minimal fix: "In beginner target patterns, forgetting 都/还/也 often makes the meaning unclear or sounds odd; use them when stating ‘everyone else’ or ‘in addition.’ But it’s not mandatory in all structures (e.g., with 没/没有/没人, 只有/就, 其他)."

### `gr_cong_dao` — 从……到…… (from ... to)  _(major)_
- **common_mistake:** Using 到 alone, or following English word order with the times after the verb.
- **flag:** Claim: "Using 到 alone" [is a common mistake]. Why wrong: In ranges, A到B without 从 is fully grammatical and very common for time and space (and other ranges). Examples: 我九点到五点工作; 北京到上海有很多航班; 周一到周五上班. Minimal fix: Rephrase to "Avoid putting the time range after the verb (我工作九点到五点✗). Put it before the verb: 我九点到五点工作. Both 从A到B and A到B are acceptable to show a span; 从…到… is the full form and is often a bit more explicit/formal."

### `gr_dao_resultative` — 到 as a resultative (找到 / 看到)  _(major)_
- **common_mistake:** Omitting 到, so successful attainment is not expressed.
- **flag:** "Omitting 到, so successful attainment is not expressed." — This is over-broad. With some verbs (e.g., 找/看/听/等), leaving off 到 does lose the attainment meaning (找→‘look for’ vs 找到→‘find’), but with others like 买, the plain verb with 了 already implies success (我买了票了 is perfectly natural and means ‘I bought the ticket’). 到 with 买 often adds an ‘managed to/after some difficulty’ nuance. Minimal fix: "With activity verbs like 找/看, omitting 到 usually loses the ‘found/saw’ result. With verbs like 买, 买了 already expresses success; 买到 adds an ‘managed to’/emphasis on attainment."

### `gr_dei_must` — 得 (děi) must / have to  _(major)_
- **common_mistake:** Negating with 不得 to mean 'don't have to'.
- **flag:** "incorrect: 现在很晚了，我不得走。 → correct: 现在很晚了，我得走了。" — 我不得走 is not ungrammatical; 不得 means “must not/are not allowed to,” so this sentence can be correct in contexts (e.g., 宿舍关门了，我不得走). The problem is only if the learner intends “don’t have to.” Minimal fix: clarify the meaning contrast and show the proper negation: incorrect for ‘don’t have to’: 现在很晚了，我不得走。 → correct: 现在很晚了，我不用走。/ 我不必走。 Also note: 不得 means ‘must not/Not allowed to.’

### `gr_deshihou` — ……的时候 (when / while)  _(major)_
- **common_mistake:** Using an English-style front 'when' without 的时候.
- **flag:** "Using an English-style front 'when' without 的时候." — This is over-broad. In standard Mandarin, 当 can function as a conjunction without 的时候 when followed by a full clause (e.g., 当你准备好了，我们就出发。). The problem in the example is specifically 当我小, which is ungrammatical because 当 + adjective phrase is odd, not because 的时候 is always required. Minimal fix: "Avoid 当 + adjective like 当我小. For this meaning, say 我小的时候/小时候…, or use 当…时/当…的时候 with a full clause (e.g., 当你准备好了，我们就出发。)."

### `gr_di_ordinal` — 第 (dì) ordinal numbers  _(major)_
- **common_mistake:** Omitting 第 for an ordinal (using a bare cardinal).
- **flag:** "Omitting 第 for an ordinal (using a bare cardinal)." — This is over-broad. Many perfectly standard ordinals in Mandarin do not take 第, especially in naming/labeling contexts where a bare numeral + classifier is used: 星期一/周一 (Monday), 二楼/二层 (2nd floor), 二号线 (Line 2), 二号 (the 2nd/day number/No. 2), 二班 (Class 2), 二队 (Team 2). Minimal fix: "Often a mistake when you mean ‘the Nth time/position/item in a sequence’ (e.g., 第一次, 第三章, 第五个), but many set names and labels use a bare numeral + classifier instead of 第 (e.g., 星期一, 二楼, 二号线, 二号)."

### `gr_double_le` — Verb + 了 + object + 了 (ongoing up to now)  _(major)_
- **common_mistake:** Using one 了 and losing the 'and still continuing' meaning.
- **flag:** Claim: “Using one 了 and losing the 'and still continuing' meaning.” Why this is wrong/over-broad: Many perfectly correct ongoing-present sentences use only the sentence-final 了 and no verb-after 了, e.g., 我来中国三年了, 我们认识三年了, 他们结婚三年了. Labeling “one 了” as a mistake would mark these natural sentences wrong. Minimal fix: “Leaving off the sentence-final 了 often loses the ‘still continuing’ meaning. In many verbs/structures the first 了 is optional or not used; what’s essential here is usually the sentence-final 了.”
- **flag:** Claim (rule name): “Verb + 了 + object + 了 (ongoing up to now).” Why this is wrong/over-broad: The middle slot is typically a duration/quantity phrase, not an ‘object’; many correct forms have no object at all (e.g., 学了两年了), and with some verbs the object appears elsewhere. Minimal fix: Rename to “Verb (+ object) + 了 + duration + 了” or simply “Verb + 了 + duration + 了 (ongoing up to now).”
- **flag:** Claim: “Two 了 with a duration mean an action has been going on and continues.” Why this is over-broad: While V + 了 + duration + 了 is a common way to show ongoing action, many ongoing sentences use only the sentence-final 了 (e.g., 我来中国三年了, 我们认识三年了; 结婚三年了), and with certain verbs the first 了 is odd or avoided. Minimal fix: “A common pattern for ongoing action is V + 了 + duration + 了; often the sentence-final 了 is the key to ‘up to now’. The first 了 may be optional or omitted with certain verbs.”

### `gr_gei_resultative` — Verb + 给 + recipient (送给 / 还给)  _(major)_
- **common_mistake:** Omitting 给 or misordering the recipient.
- **flag:** 'Common mistake' note: 'Omitting 给 or misordering the recipient.' — Labeling omission of 给 as a mistake is over-broad and wrong for common transfer verbs like 送 and 还. In standard Mandarin, both 我送他一本书 and 我送给他一本书 are correct; likewise 我还你钱 and 我还给你钱 are both fine. Minimal fix: "With some transfer verbs (e.g., 送, 还), 给 is optional when the recipient directly follows the verb (我送他一本书 / 我还你钱). With others (e.g., 递, 交, 发), 给 is typically needed before the recipient (我递给他一本书). The real mistake is placing 给 after the object (✗ 我送他一本书给)."

### `gr_haishi_huozhe` — 还是 (háishì) vs 或者 (huòzhě) — 'or'  _(major)_
- **common_mistake:** Using 或者 in a choice question or 还是 in a statement.
- **flag:** Claim: "Using 或者 in a choice question or 还是 in a statement." — Labeling "还是 in a statement" as a mistake is wrong. 还是 is regularly used inside statements in embedded/indirect choice clauses and in “whether A or B” patterns, e.g., 我不知道他是坐地铁还是打车来 and 不管你去还是不去，我都支持你. Minimal fix: "Using 或者 in a direct choice question (use 还是 there). Note: 还是 can appear in statements inside embedded ‘whether A or B’ clauses (e.g., 我不知道他是去北京还是去上海), but for simple declarative ‘A or B’ use 或者."

### `gr_hui_de_certainty` — 会……的 future certainty  _(major)_
- **common_mistake:** Dropping 会 or the framing 的; using 要 for a confident prediction.
- **flag:** Common mistake: "Dropping 会 or the framing 的" — Treating the sentence-final 的 as required is over-broad. 的 adds a reassuring/insistent tone, but "他会来" (without 的) is fully grammatical and common. Minimal fix: say that 会 is needed for the prediction here, while sentence-final 的 is optional and adds reassurance (e.g., 他会来 vs. 他会来的).
- **flag:** Common mistake: "using 要 for a confident prediction" — 要 is not categorically wrong for confident future statements; it often marks plans/schedules or imminence and can convey strong certainty (e.g., 他明天要来, 他要来了, 快要下雨了). Minimal fix: note that 要 typically expresses plan/intention or imminence, whereas 会…的 is a natural choice to reassure; avoid labeling 要 as an error across the board.

### `gr_hui_neng_keyi` — 会 / 能 / 可以 (huì/néng/kěyǐ) modals  _(major)_
- **common_mistake:** Using 能 for learned skills or 会 for permission.
- **flag:** "Common mistake: Using 能 for learned skills" — In standard Mandarin, 能 can be (and often is) used to state ability/skill, e.g., 你能说中文吗? is natural; the preference is to use 会 when highlighting an acquired skill. Minimal fix: "For learned skills, prefer 会; 能 is also possible when you’re emphasizing general ability or circumstances."
- **flag:** "incorrect: 我能说三种语言。 → correct: 我会说三种语言。" — 我能说三种语言 is not incorrect; it’s acceptable, though 我会说三种语言 better highlights a learned skill. Minimal fix: label it "Less natural: 我能说三种语言 → More natural (emphasizing learned skill): 我会说三种语言," or replace with a true error for permission (e.g., "incorrect: 这里会抽烟吗 → correct: 这里可以/能抽烟吗").

### `gr_ji_duoshao` — 几 vs 多少 (how many)  _(major)_
- **common_mistake:** Using 几 for large amounts, or inserting a measure word that is not needed after 多少.
- **flag:** "多少 asks about larger or unknown quantities and needs no measure word (多少钱)." → Over-broad/wrong: With count nouns, 多少 typically takes a classifier (e.g., 多少本书, 多少个苹果). It can omit one mainly in set phrases (多少钱) or with nouns that allow classifier omission (e.g., 多少人) or with mass nouns (多少水). Minimal fix: "多少 asks about larger or unknown quantities. With count nouns, use a measure word (多少本书/多少个苹果); in set phrases or with some nouns you may omit it (多少钱/多少人)."
- **flag:** "Common mistake: Using 几 for large amounts" → Over-broad: 几 can legitimately form large-quantity expressions with 十/百/千/万 to mean "several X" (e.g., 几百块钱, 几千人), which are correct (though not interrogative). The issue is using interrogative 几 to ask about very large/open-ended totals where 多少 is preferred. Minimal fix: "When asking about very large or open-ended quantities, prefer 多少; note that 几 also means 'several' in combinations like 几十/几百/几千 (not questions)."
- **flag:** "Common mistake: ... inserting a measure word that is not needed after 多少." → Misleading: After 多少, a classifier is often required with count nouns (多少个学生, 多少本书). Calling classifier insertion a mistake is incorrect. Minimal fix: "Don’t add a classifier in fixed phrases like 多少钱, but do use one with count nouns (多少个学生/多少本书)."

### `gr_jiu_cai` — 就 (jiù) vs 才 (cái)  _(major)_
- **common_mistake:** Adding 了 after 才, or reversing the earlier/later nuance.
- **flag:** Common mistake: "Adding 了 after 才" — This labels grammatical sentences as wrong. In the ‘not until’ sense, 才 typically doesn’t take verbal 了 (他九点才来 is natural), but 了 can appear sentence‑finally (他现在才来了) and with certain verbs like 发现/想到 to mark perfective (我才发现了一个问题). Minimal fix: “When 才 means ‘not until,’ usually don’t add 了 right after the verb (他九点才来). Sentence‑final 了 is fine (他现在才来了), and with verbs of realization it’s also common (我才发现了一个问题).”

### `gr_le_negation_drop` — 没 negates a completed action and drops 了  _(major)_
- **common_mistake:** Keeping 了 after 没 (没……了).
- **flag:** "Common mistake: Keeping 了 after 没 (没……了)." — Over-broad. 没…了 is perfectly grammatical in standard Mandarin in patterns like duration up to now or change of state, e.g. 我已经三天没吃饭了, 他很久没联系我了, 我没钱了. What is ungrammatical here is the perfective 了 placed right after the verb when negating a specific past event (e.g., *昨天我没去了). Minimal fix: "Common mistake: Adding the perfective 了 after the verb (没 + V + 了) when negating a completed event. Note: 没…了 is correct in patterns expressing ‘haven’t V‑ed for… (up to now)’ or change of state (e.g., 我三天没睡觉了)."
- **flag:** "To negate a completed action, use 没(有) before the verb and DROP 了: 我没去 … never 我没去了." — As written, "DROP 了" can be misunderstood as banning any 了; the real constraint is the perfective 了 after the verb. Minimal fix: "…use 没(有) before the verb and drop the perfective 了 after the verb: 我没去 (not *我没去了). Sentence‑final 了 can still appear in other patterns (e.g., 我已经三天没吃饭了)."

### `gr_liang_er` — 两 (liǎng) vs 二 (èr)  _(major)_
- **common_mistake:** Using 二 before a measure word (二个人).
- **flag:** 'Common mistake' note: "Using 二 before a measure word (二个人)." — This is over-broad. While 二个(人) is nonstandard (use 两个/两个人), 二 can precede measure words in several common, correct cases: in compound numbers (二十个，不说“两十个”), in fixed labels/names (二号线、二路车、二班), with the polite classifier 位 in formal style (二位来宾), and with the weight measure 两 (二两肉). Minimal fix: "Using 二 directly with a measure word to mean ‘two’ (e.g., 二个人) is nonstandard; use 两个/两个人. Note: 二 is correct before measure words in compound numbers and fixed labels (e.g., 二十个、二号线/二路车), in formal address with 位 (二位), and with the weight 两 (二两)."

### `gr_ma_question` — 吗 (ma) yes/no question particle  _(major)_
- **common_mistake:** Adding 吗 to a question that already has a question word (哪儿 / 什么 / 谁).
- **flag:** Claim: "Do not use it when the sentence already contains a question word."
Why: This is over‑broad. 吗 normally doesn’t appear with true wh‑information questions (哪儿/什么时候/为什么/怎么等), but it can co‑occur with 什么/谁 when they function as indefinites under 有/还有/有没有/想要等, e.g., 你有什么问题吗？还有谁吗？想吃点什么吗？
Minimal fix: "Don’t add 吗 to wh‑information questions (like 哪儿、什么时候、为什么、怎么). But when 什么/谁 mean ‘any/some’ (often with 有/还有/有没有/想要), adding 吗 is fine: 你有什么问题吗？还有谁吗？想吃点什么吗？"
- **flag:** Common mistake note: "Adding 吗 to a question that already has a question word (哪儿 / 什么 / 谁)."
Why: Grouping 什么/谁 with 哪儿 is inaccurate; with 什么/谁 used as indefinites, 吗 is natural (e.g., 你有什么事吗？还有谁吗？). Marking all such cases as mistakes would flag correct sentences.
Minimal fix: "Avoid adding 吗 to content wh‑questions (e.g., 你去哪儿？你什么时候来？). Exception: 什么/谁 can appear with 吗 when they mean ‘any/some’ (often with 有/还有/有没有/想要): 你有什么问题吗？还有谁吗？"

### `gr_mei_every` — 每 (měi) + measure word (every)  _(major)_
- **common_mistake:** Omitting the measure word after 每, or dropping 都.
- **flag:** Claim: "Omitting the measure word after 每" (as a blanket mistake).
Why over-broad: Many words can follow 每 without an extra classifier, e.g., 每天、每年、每月、每人, and measure-like words such as 次 already serve as the classifier (每次). Marking all omissions as errors would wrongly flag very common sentences like 我每天跑步.
Minimal fix: "With countable nouns, add an appropriate classifier after 每 (每个学生、每本书、每位老师). But time words and a few nouns can appear directly (每天、每年、每月、每人、每次)."
- **flag:** Claim: "…or dropping 都" (as a blanket mistake).
Why over-broad: 都 is common when 每-phrase is the subject/topic (每个人都知道), but it’s often not used with time/frequency adverbials or other modifiers: 我每天跑步、他每年回国一次、我每个星期去两次 are all natural without 都.
Minimal fix: "Use 都 when 每 introduces the subject/topic to emphasize ‘all’ (每个人都…); with time/frequency or adverbial 每-phrases (每天、每年、每个星期…), 都 is usually omitted."

### `gr_money_spoken` — Spoken money (块 / 毛 / 分)  _(major)_
- **common_mistake:** Using written 元/角 in speech, or reversing the unit order.
- **flag:** Claim: "Using written 元/角 in speech" [is a common mistake]. Why it’s wrong: 元 and 角 are acceptable in spoken Mandarin, especially in neutral/formal contexts (e.g., prices read out in shops, on announcements). Calling them a mistake mislabels correct usage. Minimal fix: Rephrase to "In casual speech, people usually say 块/毛 (rather than 元/角), which sound more formal/written. Both are correct; 块/毛 just sound more colloquial."

### `gr_qilai_inchoative` — 起来 — inception / 'seem' / recall  _(major)_
- **common_mistake:** Reading 起来 only literally as 'up' and omitting it for these senses.
- **flag:** Example labeled as correct is ungrammatical/nonnative: “我突然想起来那个词了。” In resultative constructions with 起来, 了 should either follow the whole complement (想起来了) or the object should be placed between 起 and 来 with 了 at the end. Minimal fixes: “我突然想起了那个词。” or “我突然想起那个词来了。” (also acceptable: “我突然想起来了那个词。”).

### `gr_resultative` — Resultative complements (看完, 听懂)  _(major)_
- **common_mistake:** Expressing the result separately in English style, or negating with 不 (不看完).
- **flag:** "Negate with 没 (没看完), not 不." — Over-broad. While factual non-achievement is negated with 没(有) (e.g., 我没看完), 不 is common and grammatical in potential complements to express inability (听不懂, 看不完) and in habitual/volitional contexts (e.g., 不做完作业不玩). Minimal fix: "To state the result did not occur (past/factual), use 没(有): 我没看完. Use 不 with potential complements to express inability (看不完/听不懂) or for habitual/volitional negation."
"Expressing the result separately in English style, or negating with 不 (不看完)." — As a blanket “mistake,” this is too strong. 不+V+RC is ungrammatical for past factual negation, but it is fine in conditional/volitional patterns (不看完这本书不睡觉) and the V不RC potential form is very common (听不懂/看不完). Minimal fix: "Mistake: using 不 for simple past/non-achievement (✗我不看完). Use 没(有). Note: 不 is fine in potential forms (听不懂/看不完 ‘can’t…’) and in conditional/volitional patterns (不做完作业不玩)."

### `gr_ruguo_jiu` — 如果……就…… (if ... then)  _(major)_
- **common_mistake:** Dropping 就 in the result clause.
- **flag:** Claim: "如果 (+的话) in the condition clause pairs with 就 in the result clause: 如果你有时间，就来我家." Why over-broad: This implies 就 must appear after 如果, but in standard Mandarin 就 is optional; e.g., "如果下雨，我们不去" and "如果下雨，我们就不去" are both correct, with 就 adding a sense of natural/resulting action. Minimal fix: "如果… often pairs with 就 in the result clause, but 就 is optional: 如果你有时间，（就）来我家。就 makes the result feel more immediate or like a natural consequence."
- **flag:** Claim (Common mistake): "Dropping 就 in the result clause." Why wrong: Omitting 就 is not an error; it’s common and grammatical in both spoken and written Mandarin, e.g., "如果你有时间，来我家。" Minimal fix: "Not a mistake: 就 is optional. Using 就 is very common and can make the relation clearer or more emphatic, but leaving it out is also correct."
- **flag:** Example labeling: "incorrect: 如果你有时间，来我家。 → correct: 如果你有时间，就来我家。" Why wrong: The sentence without 就 is acceptable; marking it incorrect teaches a false rule. Minimal fix: Show both as correct with a note on nuance: "如果你有时间，来我家。/ 如果你有时间，就来我家。就 adds a sense of ‘then/right away’ or clear linkage."

### `gr_shi_de` — 是……的 (shì...de) emphasis construction  _(major)_
- **common_mistake:** Using 了 instead of 是……的 to highlight the time/place/manner of a known past event.
- **flag:** "Using 了 instead of 是……的 to highlight the time/place/manner of a known past event." — This overstates it as an error. Sentences with 了 that include time/place/manner are often perfectly correct (e.g., 他昨天来了 / 他昨天在上海买了票). They simply don’t create the same focus as 是……的. Minimal fix: "Using 了 is grammatical, but it doesn’t add the same focus. To highlight the circumstance of a known past event, prefer 是……的. Note: with 怎么 to ask ‘by what means,’ use 是……的 (or just 怎么…的); 怎么…了 usually means ‘how come’."

### `gr_suiran_danshi` — 虽然……但是…… (suīrán...dànshì) although  _(major)_
- **common_mistake:** Dropping 但是 because English uses only 'although'.
- **flag:** "Both are used together in Chinese." — Over-broad. 虽然 often pairs with 但是/可是, but 但是 can be omitted when the contrast is clear, and other markers (却/还是/但/不过) or no overt marker are common. Also, 但是 can appear without 虽然. Minimal fix: "虽然 usually pairs with 但是/可是, especially in beginner usage, but 但是 may be omitted if the contrast is clear (often with 还是/却), and 但是 can also be used on its own."
- **flag:** "Common mistake: Dropping 但是 because English uses only 'although'." — Mislabels correct usage as an error. Omitting 但是 is acceptable: e.g., 虽然很累，我还是/却很开心。Even 虽然很累，我很开心 is acceptable in many contexts. Minimal fix: "Beginner pitfall: Omitting any clear contrast in the second clause. To be safe, include 但是/可是 or use adverbs like 还是/却 to mark the contrast."
- **flag:** "incorrect: 虽然很累，我很开心。 → correct: 虽然很累，但是我很开心。" — The first sentence is not incorrect in standard Mandarin; it's acceptable (often improved with 还是/却). Minimal fix: Present both as acceptable, e.g., "虽然很累，但是我很开心。/ 虽然很累，我还是很开心。" and note that including 但是/可是 is the safest pattern for beginners.

### `gr_time_before_place` — Word order: time and place before the verb  _(major)_
- **common_mistake:** Following English order and putting time/place after the verb or object.
- **flag:** "Chinese puts time-when and place adverbials BEFORE the verb, not after: Subject + Time + Place + Verb + Object." — Over-broad. Place phrases often appear after the verb as the complement/object of motion or location verbs: e.g., 我明年去中国, 他住在北京, 把书放在桌子上. Minimal fix: "In neutral statements, put time-when before the verb. Place can appear before the main verb as a 在/到/从 phrase (我在家看书), or after motion/location verbs as their complement/object (我去中国, 他住在北京). Avoid putting a simple time-when at the very end."
- **flag:** "Common mistake: Following English order and putting time/place after the verb or object." — Misleading for "place": placing the place after certain verbs is correct (我去中国/他住在北京). Minimal fix: "Common mistake: putting a simple time-when at the end (×我去中国明年). Keep 在/到/从 phrases before the main verb (我在家看书), but let motion/location verbs take their place complement after the verb (我去中国)."

### `gr_verb_reduplication` — Verb reduplication (看看 / 休息休息)  _(major)_
- **common_mistake:** Reduplicating a two-syllable verb as AABB (休休息息).
- **flag:** Claim: "two-syllable ABAB (休息休息), NOT AABB."
Why it’s over-broad: Many very common two-syllable verbs are separable VO verbs (离合词) and do not reduplicate as ABAB productively; instead they typically reduplicate by doubling only the verb (AA + O), e.g., 见见面、聊聊天、跳跳舞、帮帮忙、睡睡觉. Saying all two-syllable verbs take ABAB will mislead learners to produce unnatural forms like 见面见面.
Minimal fix: "For most non-separable disyllabic verbs, use ABAB (休息休息、讨论讨论). For separable VO verbs (e.g., 见面、聊天、帮忙), reduplicate only the verb: AA + O (见见面、聊聊天、帮帮忙、睡睡觉). AABB like 休休息息 is not used for verb reduplication."

### `gr_weile_purpose` — 为了 (wèile) in order to  _(major)_
- **common_mistake:** Placing the purpose at the end, or using 因为 (because) for a purpose.
- **flag:** "Placing the purpose at the end, or using 因为 (because) for a purpose." — Labeling sentence-final purpose placement as a mistake is incorrect. Standard Mandarin allows the purpose after the main clause with 是: 我学中文是为了找到好工作, and also after the subject: 我为了找到好工作学中文. Minimal fix: "Don’t use bare 因为 + 动词短语 to mean 'in order to.' Note: The 为了-phrase can go before the main clause, after the subject, or after the clause with 是: 我为了找到好工作学中文 / 我学中文是为了找到好工作."
- **flag:** "…or using 因为 (because) for a purpose." — This is over-broad. 因为 can introduce a motive if the clause expresses intention/desire: 我学中文是因为想/要找到好工作. The actual error is bare 因为 + VP like 我学中文因为找到好工作. Minimal fix: "Avoid bare 因为 + VP for purpose (e.g., 我学中文因为找到好工作 ×). Use 为了 + VP, or with 因为 add 想/要/希望: 我学中文是因为想/要找到好工作."

### `gr_wulun_dou` — 无论/不管……都…… (no matter)  _(major)_
- **common_mistake:** Dropping 都/也, or using 虽然.
- **flag:** Claim: "Dropping 都/也" [is a common mistake]. Why over-broad/wrong: In standard Mandarin, 都/也 is common after 无论/不管, but it is not mandatory. Many perfectly natural sentences omit it, e.g. "不管他来不来，我不等了。/ 不管你信不信，我是真的。/ 无论多少钱，我就不买。" Minimal fix: Rephrase to "After 无论/不管, 都/也 is very common and a safe default, but it can be omitted, especially when the main clause has 要/会/能/就/还是/一定等 or the meaning is clear."
Claim (example labeling): "incorrect: 不管天气怎么样，我去。 → correct: 不管天气怎么样，我都去。" Why over-broad/wrong: "不管天气怎么样，我去。" is acceptable and natural; adding 都 just makes the correlation more explicit. Minimal fix: Present both as correct with a preference note: "不管天气怎么样，我（都）去。/ 不管天气怎么样，我还是要去。"

### `gr_xian_ranhou` — 先……然后…… (first ... then)  _(major)_
- **common_mistake:** Reversing 先/然后 or omitting 先.
- **flag:** Common mistake note: "Reversing 先/然后 or omitting 先." — Labeling "omitting 先" as a mistake is over-broad. In standard Mandarin, 先 is often optional when the sequence is clear, and sentences like "我们吃饭，然后看电影" are perfectly natural and correct. Minimal fix: Change to "Reversing 先/然后 is a mistake. Note: 先 is optional; it just highlights the first action. You can also say: 我们吃饭，然后看电影 or 先……再…… (e.g., 我们先吃饭，再看电影)."

### `gr_xiang_yao_want` — 想 vs 要 (to want)  _(major)_
- **common_mistake:** Using 要 for a polite wish where 想 is more appropriate.
- **flag:** "Using 要 for a polite wish where 想 is more appropriate." — Over-broad. 要 is often perfectly acceptable and not impolite in many contexts (e.g., service encounters or casual equal-status situations: 我要一杯咖啡。/ 我要买两张票。). It’s mainly in deference-sensitive requests (to a teacher, superior, stranger) that 要 can sound blunt. Minimal fix: "In requests to someone you owe deference (e.g., a teacher), 要 before a request can sound too direct; 想 is softer. In many service/ordering contexts, 要 is normal."
- **flag:** "incorrect: 老师，我要看看您的书，可以吗？" — This sentence is grammatically fine; with 可以吗 it is just more direct and may feel pushy toward a teacher, not "incorrect." Minimal fix: label it as "less polite/more direct" rather than incorrect, e.g., "less polite: 老师，我要看看您的书，可以吗？ → more polite: 老师，我想看看您的书，可以吗？" (or "老师，我可以看看您的书吗？").

### `gr_xiaqu_continue` — 下去 — continue an action  _(major)_
- **common_mistake:** Using 下来 for 'continue', or 继续 awkwardly without the complement.
- **flag:** Claim: "Using 下来 for 'continue', or 继续 awkwardly without the complement." Problem: 继续 does not require 下去 and is perfectly natural on its own (e.g., 老师让我们继续读; 请继续; 我们明天继续). The real mistake is using 下来 to mean simple continuation. Minimal fix: "Using 下来 to mean 'continue', or thinking 继续 must be followed by 下去. 继续可单独使用（老师让我们继续读），也可与下去并用以强调（老师让我们继续读下去）。"

### `gr_yao_le_imminent` — (快)要……了 imminent action  _(major)_
- **common_mistake:** Omitting the final 了, or using 会 for an imminent event.
- **flag:** “The final 了 is required.” — Over-broad. In the imminent ‘要/快要/就要…了’ pattern, 了 is normally used to mark the impending change, and omitting it often shifts the meaning toward ‘want to/plan to’. However, in some contexts (e.g., with an explicit time adverbial or before another clause), speakers do drop 了: 再过五分钟就要出发，请大家做好准备。 Minimal fix: “In this pattern 了 is normally used to mark ‘about to’; omitting it often changes the meaning. In some contexts (especially with a time word or before another clause) 了 may be dropped.”
- **flag:** “Omitting the final 了, or using 会 for an imminent event.” — Over-broad. 会 by itself doesn’t specifically mean ‘about to’, but it is perfectly natural with adverbs like 马上/很快/一会儿 to predict a near-future event (e.g., 马上会下雨). Calling any use of 会 for an imminent event a mistake is misleading. Minimal fix: “Don’t use 会 by itself to mean ‘about to’; use 要/快要/就要…了. 会 can be used with time adverbs (马上/很快/一会儿) to predict a near-future event.”

### `gr_yinwei_suoyi` — 因为……所以…… (yīnwèi...suǒyǐ) cause and result  _(major)_
- **common_mistake:** Assuming that using both 'because' and 'so' is wrong, as it would be in English, and dropping 所以.
- **flag:** "Assuming that using both 'because' and 'so' is wrong, as it would be in English, and dropping 所以." — This implies that dropping 所以 is a mistake, but in standard Mandarin using only 因为 at the start is fully correct and common (e.g., 因为下雨，我没去。). Minimal fix: "A common misconception is thinking the pair is ungrammatical; in Chinese you can use both (因为…所以…), or just one: 因为…(no 所以) or …，所以…。"
- **flag:** "incorrect: 因为下雨，我没去。（acceptable, but learners often force English single-conjunction）" — The sentence labeled "incorrect" is actually correct. Minimal fix: relabel as "also correct: 因为下雨，我没去。" and keep "correct: 因为下雨，所以我没去。" (optionally add "下雨了，所以我没去。" to show only 所以 is also fine).

### `gr_yiqian_yihou` — 以前 / 以后 clause order  _(major)_
- **common_mistake:** Following English order and putting 以前/以后 first.
- **flag:** 'Common mistake' note: Following English order and putting 以前/以后 first. — Over-broad. 以前/以后 can appear sentence-initial when used as independent time adverbs meaning ‘previously/in the future’ (e.g., 以前我住在北京。/ 以后我要注意。). Minimal fix: “When you mean ‘before/after [event]’, don’t put 以前/以后 before the event; say 下课以后, not 以后下课. But 以前/以后 can also start a sentence when they mean ‘previously/from now on’.”
- **flag:** incorrect: 以后下课，我回家。 — This can be acceptable if 以后 is read as ‘from now on’: 以后，下课我就回家。 Labeling it simply “incorrect” is misleading. Minimal fix: “Not correct for expressing ‘after class I go home’; use: 下课以后，我回家。 Note: 以后 can start a sentence with the meaning ‘from now on’: 以后，下课我就回家。”

### `gr_yong_instrument` — 用 (yòng) + tool + verb (by means of)  _(major)_
- **common_mistake:** Following English 'with ...' order and putting the tool after the verb.
- **flag:** Claim: "Following English 'with ...' order and putting the tool after the verb." Why it's wrong/over-broad: In Mandarin, placing the instrument as a postverbal 用-phrase is grammatical and common (the problem in the bad example is omitting 用, not its position). Counterexamples: 我吃饭用筷子。/ 你写字用铅笔吗？/ 我上网用手机。 Minimal fix: Change to "Common mistake: Omitting 用 and saying 我吃饭筷子. Remember to mark the instrument with 用. Both 我用筷子吃饭 and 我吃饭用筷子 are correct."

### `gr_youdianr_yidianr` — 有点儿 (yǒudiǎnr) vs 一点儿 (yìdiǎnr)  _(major)_
- **common_mistake:** Swapping them: 一点儿贵 or 有点儿便宜 in the wrong slot.
- **flag:** "Swapping them: 一点儿贵 or 有点儿便宜 in the wrong slot." — Labeling 有点儿便宜 as a blanket error is over-broad. 有点儿 often conveys a mildly negative/undesirable nuance, so 有点儿便宜 is perfectly natural when ‘being too cheap’ is undesirable or suspicious (e.g., 这家店卖得有点儿便宜，我不太放心). Minimal fix: "Common mistake: Saying 一点儿贵 instead of 有点儿贵. Note: 有点儿便宜 is fine when you mean ‘a bit too cheap (undesirably)’. Use 便宜一点儿 when you mean ‘a little cheaper’ as a neutral comparison/request."

### `gr_yuelaiyue` — 越来越 (yuèláiyuè) more and more  _(major)_
- **common_mistake:** Calquing English with 更来更 or repeated 比.
- **flag:** Claim: “越来越 + Adjective/Verb = more and more.” Why it’s over-broad: 越来越 can directly take adjectives and many stative/mental verbs (e.g., 喜欢/想/担心/懂), but it does not freely take dynamic action verbs; saying ✗“他越来越跑” is ungrammatical. With action verbs you typically need a degree/adverbial structure, e.g., “他跑得越来越快” or “他越来越认真地工作,” or use a suitable complement/object, e.g., “我吃得越来越多.” Minimal fix: “越来越 + Adjective or stative/mental verb (e.g., 喜欢/想/担心/懂). For action verbs, use patterns like V + 得 + 越来越 + Adj. (跑得越来越快) or 越来越 + Adj. + 地 + V (越来越认真地工作).”

### `gr_zai_location_verb` — 在 + place + verb (do at a location)  _(major)_
- **common_mistake:** Following English order and putting the place after the verb.
- **flag:** "Common mistake: Following English order and putting the place after the verb." — This is over-broad. Many verbs naturally take 在+place after the verb (e.g., 我住在北京, 把书放在桌子上, 他站在门口). Minimal fix: "With general activity verbs like 学习/工作/吃饭, don’t put the 在-place after the verb (e.g., ✘我学习在图书馆 → ✔我在图书馆学习). Note: Some verbs do take 在+place after the verb, e.g., 我住在北京, 他站在门口."

### `gr_zai_progressive` — 在/正在 (zài/zhèngzài) progressive aspect  _(major)_
- **common_mistake:** Applying 在……呢 to stative verbs (在知道), or confusing progressive 在 with the locational 在 (to be at).
- **flag:** Claim: "This describes ongoing actions, not states." Why it's over-broad: 在/正在 can also appear with some state-like or situation predicates to mean “to be in the middle of that state,” e.g., 他在忙呢/他正在忙, 他正在住院, 她正(在)怀孕. Minimal fix: “It’s generally used with dynamic actions and not with stative verbs like 知道、喜欢、认识, but it can also occur with ongoing situations such as 忙、住院、怀孕 to mean ‘be in the middle of.’”

### `gr_zai_you_again` — 再 vs 又 (again: future vs past)  _(major)_
- **common_mistake:** Swapping them — 再 for a completed repetition or 又 for a future one.
- **flag:** "又 = again for a past/realised one" — This is over-broad. 又 can also mark expected/near-future or imminent repetition, especially with 要/会/能 or a future time adverbial, e.g., "明天又要下雨了", "他又要迟到了", "我们下周又见面". Minimal fix: "又 typically indicates repetition that has happened or is seen as certain/imminent (often with 要/会/能 or a future time), e.g., 他又迟到了; 明天又要下雨了."
- **flag:** "Common mistake: Swapping them — … 又 for a future one." — This incorrectly labels some correct sentences as errors, since 又 is acceptable for (near) future repetition in patterns like 又要/又会… (e.g., "明天又要开会"). Minimal fix: "Common mistake: Using 再 for a completed repetition. Note: 又 is also used for expected/near-future repetition (又要/又会…), while 再 is for planned/volitional future actions (再来一次/我们明天再说)."

### `gr_zhi_only` — 只 (zhǐ) only — before the verb  _(major)_
- **common_mistake:** Placing 只 after the verb, or using 就 for 'only'.
- **flag:** Claim: "Placing 只 after the verb, or using 就 for 'only'." — The blanket prohibition on using 就 for “only” is wrong. In standard Mandarin, 就 often means “only/just,” especially before numerals or small quantities, and even with 有 or verbs (e.g., 我就有两个 ‘I only have two,’ 就我们三个人 ‘there are only three of us,’ 我就问一个问题 ‘I’ll only ask one question’). Minimal fix: Keep “Don’t place 只 after the verb,” but change the rest to: “Note: 就 can also mean ‘only/just,’ especially before numbers. Use 只 before verbs like 有/喜欢 (e.g., 我只有两个 / 他只喜欢你).”

### `gr_zhiyao_jiu` — 只要……就…… (as long as)  _(major)_
- **common_mistake:** Pairing 只要 with 才 (that belongs to 只有).
- **flag:** "Pairing 只要 with 才 (that belongs to 只有)." — Over-broad/wrong: In standard Mandarin, 只要…才… is attested and natural; it shifts the meaning from a sufficient condition to emphasizing necessity (close to 只有…才…). E.g., 只要坚持，我们才能成功; 只要你去，我才去. Minimal fix: "For this pattern, we usually teach 只要…就… to express a sufficient condition. 只要…才… is also used to emphasize ‘only then,’ similar to 只有…才…."
- **flag:** "incorrect: 只要努力，才能成功。 → correct: 只要努力，就能成功。" — The sentence marked as incorrect is in fact grammatical and common; it means "Only if you work hard can you succeed" (necessary condition). Minimal fix: Present both as correct with different meanings, e.g., "只要努力，就能成功" (sufficient) vs "只要努力，才能成功" ≈ "只有努力，才能成功" (necessary).

### `gr_ba_disposal` — 把 (bǎ) disposal construction  _(minor)_
- **common_mistake:** English speakers use 把 with a bare verb and no result (把书看), or use it with intransitive/stative verbs, or combine it with 被 in the same clause.
- **flag:** “The verb must be transitive …” — This is over‑broad. In standard usage, verbs that aren’t canonically transitive or are adjective‑like can appear in 把 sentences when they form a causative/resultative predicate, e.g., 这话把我笑死了, 这消息把他高兴坏了, 把我急坏了. Minimal fix: “The verb should denote an action that affects the object (typically a transitive verb) and is usually followed by a result/complement or 了.”
- **flag:** “…use it with intransitive/stative verbs” (as a blanket ‘common mistake’) — Over‑broad as written. While bare intransitives/statives (e.g., 来/去/是/在/有) or a bare verb like 把书看 are wrong, many adjective‑like/stative verbs are fine in 把 when they form a resultative affecting the object (e.g., 把他气坏了/笑死了/累坏了). Minimal fix: “Don’t use 把 with bare intransitives or non‑affecting statives (来、去、是、在、有), or with a bare verb lacking a result; adjective‑like verbs are fine when they form a resultative (e.g., 这消息把他高兴坏了).”

### `gr_bushi_ershi` — 不是……而是…… (not A but B)  _(minor)_
- **common_mistake:** Using 但是 instead of 而是 for a correction.
- **flag:** "Using 但是 instead of 而是 for a correction." — This overgeneralizes. 但是 can express the same correction/contrast if the second part is a full clause, e.g., 这不是茶，但是是咖啡/但是这是咖啡/但是它是咖啡. The problem in the example is dropping 是 and using 但是 to link a bare noun phrase. Minimal fix: Clarify that in the fixed pattern use 而是 to connect A and B; if you use 但是, the B-part must be a full clause with 是/subject (e.g., 这不是茶，但是是咖啡/但是这是咖啡).

### `gr_de_complement` — 得 (de) degree/manner complement  _(minor)_
- **common_mistake:** Omitting the repeated verb when there is an object (他说汉语得很好), or confusing 得 with 的/地.
- **flag:** "If the verb has an object, repeat the verb: 他说汉语说得很好." — This is over-broad. You must repeat the verb only if the object stays after the verb; you can also front the object and not repeat the verb, e.g., "他汉语说得很好/汉语他说得很好," or use 把: "他把汉字写得很漂亮." Minimal fix: "If the object stays after the verb, repeat the verb (他说汉语说得很好). Alternatively, move the object before the verb (他汉语说得很好) or use 把 (他把汉字写得很漂亮)."
- **flag:** "Omitting the repeated verb when there is an object (他说汉语得很好)" — As phrased, this implies you must always repeat the verb whenever there is an object, which isn’t true if the object is fronted (e.g., "他汉语说得很好"). Minimal fix: "Omitting the repeated verb when the object follows the verb (他说汉语得很好). If you move the object before the verb, repetition isn’t needed: 他汉语说得很好."

### `gr_de_di_de` — 的 / 得 / 地 (de) distinction  _(minor)_
- **common_mistake:** Writing 的 for all three because they sound the same.
- **flag:** Claim: "得 links a verb to a complement of degree/result (走得慢)." Why over-broad/wrong: 得 also attaches to adjective predicates, not only verbs, e.g., 高兴得不得了, 累得要命, 冷得发抖. Minimal fix: "得 links a predicate (verb or adjective) to a complement of degree/extent/result, e.g., 走得慢, 高兴得不得了."

### `gr_directional` — Directional complements (进来, 出去)  _(minor)_
- **common_mistake:** Wrong order of the place object and 来/去, or omitting the direction.
- **flag:** "来/去 and directional verbs (上下进出回过) attach to a verb to show direction relative to the speaker" — Over-broad: 来/去 mark motion relative to the deictic center, which is usually the speaker but can also be the listener or a previously established location in narrative (e.g., 小王从外面走进来, even if the narrator isn’t in that room). Minimal fix: "…show direction relative to the deictic center (usually the speaker)."
- **flag:** "Common mistake: Wrong order of the place object and 来/去, or omitting the direction." — Over-broad/ambiguous: It’s often grammatical to omit 来/去 (e.g., 他跑进教室了), so saying "omitting the direction" risks labeling correct sentences as errors. The typical learner error is using 来/去 without a needed simple directional like 进/出 (e.g., 他跑来教室). Minimal fix: "…or using 来/去 without a needed simple directional (如 进/出/上/下), e.g., 他跑来教室；注意 来/去 并非总是必须：他跑进教室(了) 也对。"

### `gr_dou_all` — 都 (dōu) all/both — before the verb, scope to its left  _(minor)_
- **common_mistake:** Placing 都 before the subject it quantifies, or after the verb.
- **flag:** Common mistake: "Placing 都 before the subject it quantifies, or after the verb." — The blanket ban on "after the verb" is over-broad: in standard Mandarin there are set patterns where 都 follows an initial copy of the verb (e.g., 看都不看, 去都去了, 说都说了), which are grammatical but involve a different use from the quantifier 'all/both'. Minimal fix: "In the ‘all/both’ use taught here, don’t put 都 after the main predicate; it typically appears before the verb phrase and associates with material to its left. Note there are other patterns (e.g., 看都不看, V都V了) where 都 can follow a first verb—those are different uses."

### `gr_duo_approx` — Number + 多 approximation  _(minor)_
- **common_mistake:** Putting 多 before the number, or omitting it for 'more than'.
- **flag:** “Putting 多 before the number” (as a blanket mistake). In other valid structures, 多 can precede the number to mean “an extra N,” e.g., 再多三天, 多两个人, 多三块钱. Minimal fix: “In this ‘-odd/more than’ pattern, don’t put 多 before the number (say 三十多岁, not 多三十岁).”

### `gr_duration_complement` — Duration complement (time how long)  _(minor)_
- **common_mistake:** Placing the duration before the verb like a time-when phrase (我两年学汉语).
- **flag:** "Placing the duration before the verb like a time-when phrase (我两年学汉语)." — Over-broad. Preverbal duration is not always wrong in standard Mandarin: it is natural with negation to mean “for X time not V” (e.g., 我两年没学汉语, 他三天没来) and with resultative/achievement meanings to express “it took X time to …” (e.g., 他三天就学会了游泳, 我两年才学会汉语). Minimal fix: "For expressing how long you did something, don’t put the duration before the verb (avoid 我两年学汉语 for ‘I studied Chinese for two years’). Note: preverbal duration is fine in patterns like 他三天没来 or 他三天就学会了游泳."
- **flag:** "With an object, repeat the verb or place duration between verb and object: 我学汉语学了两年 / 我学了两年汉语." — Incomplete to the point of being over-broad. A very common, fully correct option is to place the duration after the object (often with sentence-final 了 when meaning ‘up to now’): 我学汉语两年了, 我等你两个小时了. Minimal fix: add a third option: "…or put the duration after the object (especially with 了): 我学汉语两年了."

### `gr_frequency_adverb` — 常常 / 经常 frequency — before the verb  _(minor)_
- **common_mistake:** Placing the frequency adverb after the verb or at the end.
- **flag:** Claim: “Placing the frequency adverb after the verb or at the end.” — stated as categorically wrong. Why over-broad: In V‑得 complement structures, frequency words can appear after the verb, e.g., 他来得不常 / 他联系得不经常 are natural, so not every post‑verb placement is ungrammatical. Minimal fix: “In simple SVO sentences, don’t put these after the verb or at the sentence end (e.g., 我去常常那儿/我去那儿常常 ✗). Note: in V‑得 complements, forms like 不常/不经常 can follow 得 (e.g., 他来得不常).”

### `gr_gei_coverb` — 给 (gěi) + recipient + verb (for / to)  _(minor)_
- **common_mistake:** Omitting 给, or following English order (verb before recipient) where the coverb is expected.
- **flag:** "Omitting 给, or following English order (verb before recipient) where the coverb is expected." — This overstates that placing the verb before the recipient is a mistake. In many cases, V + 给 + recipient is perfectly standard (e.g., 我打电话给你, 写信给他, 发邮件给她). Minimal fix: "Don’t drop 给 with verbs like 打电话/写信/发短信: say 给你打电话 or 打电话给你, not 我打电话你."
- **flag:** "Omitting 给" framed as a general mistake is over-broad. Some verbs take a recipient directly without 给 (e.g., 送他一本书, 教他中文, 告诉你). Minimal fix: qualify it to "With verbs that need 给 to introduce the recipient (e.g., 打电话/写信/发短信), don’t omit 给."

### `gr_jian_perception` — 见 for involuntary perception (看见 / 听见)  _(minor)_
- **common_mistake:** Using bare 看/听 when the perceptual result is meant.
- **flag:** "见 for involuntary perception (看见 / 听见)" — Calling 见 "involuntary" is over-broad. 见 as a resultative complement simply marks that the sensory event was achieved; it does not by itself encode (in)voluntariness. E.g., 我仔细听，终于听见了他的脚步声 shows deliberate effort with 听见. Minimal fix: rename to "见 for perception result" or "用“见”表示感知到的结果".
- **flag:** "Common mistake: Using bare 看/听 when the perceptual result is meant." — Over-broad as a blanket warning. Bare 看/听 can validly express completed perception in many collocations (e.g., 我看了那份通知了 ‘I read the notice,’ 我已经听了录音), whereas when reporting detecting a specific stimulus like 人/声音/动静, a resultative complement (见/到) is typically needed. Minimal fix: "Relying only on 看/听 to report that you perceived a specific stimulus (e.g., 声音/人/动静); add a resultative complement like 见/到 (看见/看到, 听见/听到) to show the result."

### `gr_lai_qu_purpose` — 来/去 + verb phrase (come/go to do)  _(minor)_
- **common_mistake:** Inserting 为了 / an English 'to' marker between the motion and the purpose verb.
- **flag:** Claim: "Inserting 为了 / an English 'to' marker between the motion and the purpose verb." Why over-broad: While placing bare 为了 right after 来/去 is generally ungrammatical or awkward (e.g., 我去为了买东西商店), 为了 can appear with 来/去 in correct patterns, such as 我去商店是为了买东西 or 我为了买东西去商店. Minimal fix: "Don’t put bare 为了 directly after 来/去 to mark purpose. Say 我去商店买东西. If you want 为了, use 我为了买东西去商店 or 我去商店是为了买东西."

### `gr_le_change` — 了 (le) as change of state (sentence-final)  _(minor)_
- **common_mistake:** Omitting sentence-final 了 when reporting a new state, or confusing it with the verbal completion 了.
- **flag:** "It reports that something is now different from before." — Sentence‑final 了 can also mark an impending change, not only a state that is already true (e.g., 快下雨了, 要迟到了, 天要黑了). Minimal fix: "Sentence‑final 了 signals a new or impending situation/change; it often indicates that something is now (or about to be) different from before."
- **flag:** "Omitting sentence‑final 了 when reporting a new state" (and labeling 我今年二十岁 as incorrect) — Omitting 了 is not categorically wrong; without 了 it reads as a general/current fact and is acceptable in contexts like answering 你今年多大? Minimal fix: "To highlight a newly reached state (e.g., just turned an age), add 了; without 了 it sounds like a general fact rather than emphasizing the change (better: 我今年二十岁了)." Replace “incorrect” with “less precise/natural for ‘just turned’ meaning.”

### `gr_li_distance` — 离 (lí) distance from  _(minor)_
- **common_mistake:** Using 从 for a static distance.
- **flag:** "Using 从 for a static distance." — This is over-broad. While the structure "A 从 B 很近/很远" is ungrammatical (you should use 离), 从 can express distance in static statements when paired with 到, e.g., "从这儿到学校很近/不远." Minimal fix: "Don’t use the pattern A 从 B 近/远; use A 离 B 近/远. However, you can say 从 A 到 B 很近/很远 to describe distance."

### `gr_measure_words` — Measure words (量词)  _(minor)_
- **common_mistake:** Dropping the measure word (三书) or defaulting to 个 for everything (三个书).
- **flag:** "Chinese requires a measure word between a number/demonstrative and a noun: Number + Measure Word + Noun." — This is over-broad. With numbers, many words are themselves measurement units and take no extra classifier (e.g., 三天, 两年, 五岁, 三点). With demonstratives, some high-frequency nouns can omit 个 in standard colloquial or set phrases (e.g., 这人/那事), and formal style allows 人 without a classifier after numbers (三人). Minimal fix: "In general, when a number or 这/那 modifies a countable noun, use a measure word: Number/这(那) + Measure Word + Noun. Common exceptions include time/age/measurement units (天、年、岁、点、分等), set phrases like 三人, and colloquial 这人/那事 where 个 is often omitted."

### `gr_meiyou_comparison` — A 没有 B (那么) + adj — not as ... as  _(minor)_
- **common_mistake:** Using 不比 (which means 'not necessarily more than') to mean 'not as ... as'.
- **flag:** "不比 (which means 'not necessarily more than')" — The phrase 'not necessarily more than' suggests it could still be more, which is wrong. 不比X高 means 'no taller than X' (i.e., not taller; could be equal or shorter), never 'possibly taller.' Minimal fix: say "不比 means 'no more … than' / 'not …‑er than' (may be equal or less)."
- **flag:** "incorrect: 我不比他高。" — This sentence is grammatical and natural, meaning "I’m not taller than him" (i.e., no taller). It's only wrong if used to mean "I’m shorter than him." Minimal fix: label it "Not correct for expressing 'not as tall as'; use 我没有他高."

### `gr_shi_identity` — 是 (shì) identity — no 是 before an adjective  _(minor)_
- **common_mistake:** Inserting 是 before an adjective (他是高 / 他是很忙).
- **flag:** Claim: "It is NOT used before an adjective predicate — use 很 there instead." Why over-broad: In simple descriptive sentences this is correct, but 是 can appear before adjectives in other well-formed structures, e.g., as a focus marker with 的 for emphasis (他是很忙的) or in contrastive sentences (他是高，但是……). Minimal fix: "In simple descriptive sentences, don’t put 是 directly before an adjective; use 很 (or other degree words) instead: 他很忙. Note: 是 can appear with adjectives in emphatic patterns like 是…的 (他是很忙的) or in contrastive focus (他是高，但是……)."
- **flag:** Common mistake note: "Inserting 是 before an adjective (他是高 / 他是很忙)." Why over-broad: As an across-the-board ban this labels forms that are acceptable in emphasis/contrast or in 是…的 as wrong (e.g., 他是很忙的; 他是高，但是…). Minimal fix: "In simple statements, inserting 是 before a bare adjective is incorrect (say 他很忙). It’s fine in emphatic/contrastive patterns or with 的 (e.g., 他是很忙的; 他是高，但是…)."

### `gr_tai_le` — 太……了 (too / so)  _(minor)_
- **common_mistake:** Omitting 了 after 太, or replacing 太 with 很.
- **flag:** "Omitting 了 after 太" (as a blanket 'common mistake'). 了 is very common in the standalone/exclamatory 太… predicate, but it is not required in all uses of 太: e.g., attributive modifier 太贵的手机我不买, or clipped/casual predications/exclamations like 这个太贵。/ 今天太热。 are natural in speech and writing. Minimal fix: "In standalone exclamations/predications, 太 usually takes sentence-final 了 to sound natural (这个太贵了). Without 了 is fine before 的 (太贵的…) or in clipped/casual comments (这个太贵)."
- **flag:** Labeling "incorrect: 这个太贵。 → correct: 这个太贵了。" as an error. 这个太贵。 is acceptable (especially in casual speech or when followed by a clause), though 这个太贵了。 is the canonical beginner-friendly pattern. Minimal fix: present it as a preference: "More natural/standard: 这个太贵了。 Colloquial/clipped: 这个太贵。"

### `gr_xie_some` — 些 / 一些 / 这些 (some, plural)  _(minor)_
- **common_mistake:** Adding a measure word after 些 (一些个) or a number before it.
- **flag:** "It replaces number+MW and takes no measure word of its own." — Over-broad. In colloquial Mandarin, 个 can appear after 些/这些/那些 for emphasis (e.g., 一些个苹果, 这些个孩子; also 好些个… is common). Minimal fix: "Generally 些 is used directly before a noun and does not take a measure word; in colloquial speech 个 may appear after 些 (一些个/这些个), but avoid this in neutral or formal style."
- **flag:** "Common mistake: Adding a measure word after 些 (一些个)" and marking "我买了一些个苹果。" as incorrect — This treats an attested colloquial pattern as an error. Minimal fix: Recast as a register note: "In standard written Mandarin, avoid adding 个 after 些; forms like 一些个 are colloquial/emphatic (more common in northern speech). Prefer 一些苹果 in neutral style." Change the example labels to "colloquial → neutral" rather than "incorrect → correct."
- **flag:** "...or a number before it." — As written this would also forbid 一, yet 一些 is standard. Minimal fix: "...or a number other than 一 (些 doesn’t combine with other numerals like 三些)."

### `gr_ye_also` — 也 (yě) also — before the verb  _(minor)_
- **common_mistake:** Placing 也 at the end like English 'too'.
- **flag:** Claim: "也 (also/too) goes before the verb or adjective, never at the end."
Why over-broad: In full sentences, 也 is not sentence-final, but in common elliptical replies the predicate is omitted and 也 can appear last (e.g., A: 我去。 B: 我也。 ‘Me too.’), which is perfectly natural in modern Mandarin.
Minimal fix: "In full sentences, 也 goes before the verb or adjective and should not be sentence-final. In short elliptical replies like ‘我也。’ (‘me too’), 也 can appear at the end because the verb is omitted."

### `gr_yi_jiu` — 一……就…… (as soon as)  _(minor)_
- **common_mistake:** Using 然后 for the immediate second event, or dropping 就.
- **flag:** Claim: "Using 然后 for the immediate second event, or dropping 就." (specifically: "dropping 就") — This overstates that 就 is obligatory. In modern Mandarin, 就 is strongly preferred in the 一…就… pattern, but it can be omitted when the result is clear, often with 了 in the second clause (e.g., "他一来，我走了。" "天一黑，我们回家了。" "他一说话，大家都笑了。"). Minimal fix: "In this pattern, 就 is strongly preferred and usually expected; beginners should keep 就. It can sometimes be omitted when the result is clear (often with 了), but don’t drop it in sentences like 我一到家就给你打电话."

### `gr_yinggai_should` — 应该 (yīnggāi) should / ought to  _(minor)_
- **common_mistake:** Placing 应该 at the end like an English tag, or omitting it.
- **flag:** "Placing 应该 at the end like an English tag, or omitting it." — Omitting 应该 is not inherently a mistake in Chinese; speakers often leave it out to make an imperative or use other suggestion forms (e.g., 你去看医生吧, 我们现在走). It’s only a mistake if the learner intends to express the specific meaning of “should.” Minimal fix: "Don’t put 应该 at the end. If you want to say ‘should,’ place 应该 before the predicate. It’s fine to omit 应该 if you mean an imperative or use another modal (e.g., 最好/得/该)."

### `gr_yue_yue` — 越 A 越 B — the more ... the more  _(minor)_
- **common_mistake:** Using 更 twice, or English 'the more ... the more' word order.
- **flag:** "越 + Verb1 + 越 + Verb2/Adj = the more A, the more B" — This makes it sound like the first slot must be a verb, but in standard usage both slots can be verbs, adjectives, or even short clauses. Counterexamples: 越多越好, 天气越冷，人越懒, 越复杂越有意思. Minimal fix: "越 + X + 越 + Y (X/Y can be verbs, adjectives, or short clauses) = the more A, the more B."

### `gr_zai_location` — 在 (zài) to be located at  _(minor)_
- **common_mistake:** Using 有 or 是 for the location of a specific known thing.
- **flag:** "Using 有 or 是 for the location of a specific known thing." — Over-broad. 有 can appear in existential sentences with a place topic even when the noun is specific (e.g., 桌子上有我的手机/你要找的那部手机) to present what is at a place. Minimal fix: "Don’t use X + 有 + 地方 to mean ‘X is at Y’; use 在. 有 is for Place + 有 + N to introduce what exists/appears there (typically new or non-specific)."
- **flag:** "Using 有 or 是 for the location of a specific known thing." — Over-broad. 是 can be used in the focus pattern 是…在… to emphasize location (e.g., 手机是在桌子上，不是在沙发上). Minimal fix: "Don’t use bare 是 as the main verb for location; use 在. 是…在… is possible for emphasis.

### `gr_zhe_durative` — 着 (zhe) durative / accompanying state  _(minor)_
- **common_mistake:** Using 着 for a plain ongoing action where 在 is needed, or dropping 着 for an accompanying manner.
- **flag:** "It describes a persisting state, not a dynamic action in progress (that is 在)." — This is too absolute: in colloquial Mandarin, V+着+呢 (and with some verbs like weather verbs) can mark an ongoing action, e.g., 外面下着雨呢 ‘It’s raining,’ 他哭着呢 ‘He’s crying.’ Minimal fix: "It typically marks a persisting state or a background manner, not a plain ongoing action (use 在/正在 for that). Note: V+着+呢 and some verbs (e.g., 下着雨) can also express an action currently happening."
- **flag:** "Using 着 for a plain ongoing action where 在 is needed" — Over-broad as stated; V+着+呢 can indicate ongoing action in everyday speech (e.g., 她笑着呢). Minimal fix: "Generally don’t use 着 by itself for plain ongoing actions; prefer 在/正在. Exception: V+着+呢 (and some set patterns like 下着雨) can also show an action is in progress."

### `gr_zhiyou_cai` — 只有……才…… (only if)  _(minor)_
- **common_mistake:** Pairing 只有 with 就 (that belongs to 只要).
- **flag:** “Pairing 只有 with 就 (that belongs to 只要).” — Over-broad. In the conditional ‘only if’ pattern, 只有…才… is correct and 只有…就… is wrong, but 只有 also has a different meaning (‘only/there is only’) where 就 is fine, e.g., 只有一个人就行了/够了. Minimal fix: “In the conditional ‘only if’ structure, use 只有…才…; don’t pair 只有 with 就 there. (就 goes with 只要…就… to mean ‘as long as… then…’.) Note: 只有 can also mean ‘only/there is only,’ where 就 may appear, e.g., 只有一个人就行了.”

## Caveats

- **Triage, not truth.** gpt-5 is strong on this class (it caught the 把/被 over-broad claim a weaker judge missed), but it is not infallible — a native/expert reviewer must confirm each flag before editing the corpus. Read `major` first.
- **Silence is not a guarantee.** An unflagged rule is 'no issue the judge could see', not 'verified correct'. A second judge or human sweep is the way to raise recall.
- Fixing a confirmed flag edits `data/grammar_rules.json`; re-seed the corpus (or wipe `/var/data` on the VM) so grounded replies pick up the corrected rule.
