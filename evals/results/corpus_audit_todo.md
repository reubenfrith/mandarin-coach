# Corpus audit — harm re-rank (the actionable to-do list)

Re-ranked the 71 audit-flagged rules by the one criterion that matters: would the rule, applied literally, make the coach mark a CORRECT level-appropriate (HSK 1-4) learner sentence WRONG? Judge = **gpt-5**.

## To fix: 69/71 flagged rules would reject correct usage

_(The other 2 are merely incomplete — they omit advanced/edge-register exceptions a beginner won't produce; leave them for a beginner tool. Still a human's call.)_

| rule | correct sentence it would wrongly reject | minimal fix |
|---|---|---|
| `gr_ba_disposal` 把 (bǎ) disposal construction | 请把书给我。 (Please give me the book.) | Clarify that the verb just can’t be bare; it must be followed by something — a result/directional/state complement, 了/着, a duration/measure or location phrase,  |
| `gr_bei_passive` 被 (bèi) passive construction | 我没被邀请。 (I wasn’t invited.) | Edit the line to: “In 被-sentences the verb phrase is usually not bare — it often has 了, a result, an object, or other info. But after 没/没有 don’t use 了 (我没被邀请),  |
| `gr_le_change` 了 (le) as change of state (sentence-final) | 我饿。 (I’m hungry.) | Add: “Sentence-final 了 highlights a new/changed situation; it’s not required if you’re simply stating a current fact.” Update Common mistake: “Thinking you must |
| `gr_shi_de` 是……的 (shì...de) emphasis construction | 你怎么来的？ (How did you get here/by what means?) | Common mistake: Thinking you must use 是……的. Plain past with 了 is also correct; 是……的 just adds focus to the time/place/manner. For example, 你怎么来的？ and 你是怎么来的？ ar |
| `gr_measure_words` Measure words (量词) | 我们两人都去。 (The two of us are going.) | Change to: “Chinese usually requires a measure word between a number/demonstrative and a noun: Number + Measure Word + Noun. Common beginner exceptions: with or |
| `gr_zai_progressive` 在/正在 (zài/zhèngzài) progressive aspect | 我看书呢。 (I'm reading.) | Clarify that 呢 can also directly mark an action in progress by itself after the verb: 我看书呢。 You can also combine it with 在/正在 for extra emphasis: 我在看书呢。 (Still  |
| `gr_de_complement` 得 (de) degree/manner complement | 他把字写得很漂亮。 (He writes characters very beautifully.) | Say: Use V + O + V + 得 + complement when the object comes directly after the verb (他说汉语说得很好). If the object is moved before the verb (topic or in 把/被), don’t re |
| `gr_de_di_de` 的 / 得 / 地 (de) distinction | 他认真学习汉语。 (He studies Chinese diligently.) | Add: “地 usually marks an adverbial before a verb, but in modern usage it’s often omitted with common short adverbials/adjectives: 慢慢走、认真学习 are also correct. Don |
| `gr_time_before_place` Word order: time and place before the verb | 我住在北京。 (I live in Beijing.) | Edit the explanation to: “Time-when goes before the verb. Place is often set with 在 + place before the verb (我明天在家看书), but with many verbs it naturally comes af |
| `gr_duration_complement` Duration complement (time how long) | 我三天没吃饭。 (I haven’t eaten for three days.) | Clarify: In affirmative sentences, duration goes after the verb. With an object, you can use (a) V 了 Duration O (我学了两年汉语), (b) V O V 了 Duration (我学汉语学了两年), or ( |
| `gr_liang_er` 两 (liǎng) vs 二 (èr) | 你是第二个人。 (You are the second person.) | Revise the common-mistake note: “不要在量词前用‘二’来表示‘两个’（×二个人 → ✓两个人；×二杯 → ✓两杯）。但在这些情况下用‘二’没问题：第二个、二十个；以及和百/千/万/亿连用时（如二百/两百都可以）。” |
| `gr_youdianr_yidianr` 有点儿 (yǒudiǎnr) vs 一点儿 (yìdiǎnr) | 这个有点儿便宜。 (This is a bit too cheap.) | 有点儿 + 形容词多表示轻微抱怨/不理想（有点儿贵）。当“便宜”被视为不理想时，也可以说“有点儿便宜”。形容词 + 一点儿用于比较，表示“再/更……一点儿”（便宜一点儿）。不要把“一点儿”放在形容词前（不用：一点儿贵）。 |
| `gr_hui_neng_keyi` 会 / 能 / 可以 (huì/néng/kěyǐ) modals | 我能说三种语言。 (I can speak three languages.) | Change the “Common mistake” to: “For learned skills, 会 is more natural; 能 is also used and not wrong. Use 可以 (not 会) for permission.” Update the example label t |
| `gr_jiu_cai` 就 (jiù) vs 才 (cái) | 他九点才来了。 (He didn’t come until nine.) | Revise the note to: “With 才, don’t put 了 right after the verb in simple past statements (他九点才来). Sentence-final 了 is OK to show a new situation: 他九点才来了。” |
| `gr_resultative` Resultative complements (看完, 听懂) | 我听不懂老师的话。 (I can’t understand what the teacher says.) | Negate a result that didn’t happen with 没(有): 我没看完。/ 我没听懂。 To express inability or predicted non-completion, put 不 between the verb and the result: 我看不完、听不懂、找不到 |
| `gr_directional` Directional complements (进来, 出去) | 我回家。 — I’m going home. | Edit the explanation to: “If there is a place noun, put it before 来/去, but 来/去 is optional and only used to show toward/away from the speaker: 他跑进教室(来); 我回家。” E |
| `gr_yinwei_suoyi` 因为……所以…… (yīnwèi...suǒyǐ) cause and result | 因为下雨，我没去。 (Because it rained, I didn’t go.) | Explanation: 因为…所以… is a common and natural pairing, but in everyday Chinese 所以 is often optional after 因为; you can also use only 所以 (…，所以…). Common mistake: Th |
| `gr_suiran_danshi` 虽然……但是…… (suīrán...dànshì) although | 虽然很累，我很开心。 (Although I’m tired, I’m happy.) | Revise explanation: “虽然 (although) often pairs with 但是/可是 (but), but 但是/可是 is optional when the contrast is clear. Both 虽然很累，但是我很开心 and 虽然很累，我很开心 are correct.”  |
| `gr_haishi_huozhe` 还是 (háishì) vs 或者 (huòzhě) — 'or' | 我不知道他是学生还是老师。 (I don’t know whether he is a student or a teacher.) | Edit Common mistake to: “Using 或者 in a choice question.” Add a note to the Explanation: “Use 还是 for ‘or’ in direct questions. In normal statements, use 或者. But  |
| `gr_double_le` Verb + 了 + object + 了 (ongoing up to now) | 我学汉语两年了。 (I have been studying Chinese for two years.) | Teach: To express “started before and still true now,” include sentence‑final 了. A common pattern is V + 了 + Duration + 了 (e.g., 我在这儿住了三年了), but the first 了 is  |
| `gr_zhe_durative` 着 (zhe) durative / accompanying state | 我正吃着饭呢。 (I'm eating right now.) | Revise the explanation to: “Verb + 着 usually marks a continuing state or a manner accompanying another action (V1着 + V2): 门开着, 他笑着说. For actions in progress, us |
| `gr_yao_le_imminent` (快)要……了 imminent action | 一会儿会下雨。 (It will rain soon.) | Change “The final 了 is required.” to “In this pattern, 了 is normally used to show ‘about to’; without 了 it often just means a plan/general future, not ‘about to |
| `gr_le_negation_drop` 没 negates a completed action and drops 了 | 他没来了。 (He isn’t coming anymore / He didn’t come after all.) | Say: “To negate a completed action, use 没(有) + V and do not use the perfective 了 right after the verb: 我没去 (not 我没去‘了’ for simple negation). Note: sentence‑fina |
| `gr_ma_question` 吗 (ma) yes/no question particle | 你有什么问题吗？ — Do you have any questions? | Revise to: “Add 吗 at the end of a statement to make a yes/no question (你是学生吗？). Do not add 吗 when a question word is asking for specific information (谁、什么、哪儿、什么 |
| `gr_ba_suggestion` 吧 (ba) suggestion / supposition | 你是老师吗？ (Are you a teacher?) | Tweak the “Common mistake” to: Use 吧 when you want to make a suggestion or a tentative “I think…” guess; use 吗 for a neutral yes/no question. For example: 我们走吗？ |
| `gr_hui_de_certainty` 会……的 future certainty | 别担心，他会来。 (Don't worry, he will come.) | Explain: “会 + Verb (+ 的) expresses a confident prediction; 的 adds reassurance/emphasis and is optional.” Common mistake: “Dropping 会 (changes the meaning). 要 is |
| `gr_xiang_yao_want` 想 vs 要 (to want) | 我要一杯咖啡，谢谢。 (I'd like a cup of coffee, thanks.) | Clarify tone vs. correctness and limit the warning to deferential requests: “想 + 动词 = 较委婉；要 + 动词 = 更坚定/打算（语气更强）。在需要表示客气的请求（如对老师/陌生人求助）里，用 想/想要 或 加上 能/可以…吗 来委婉；在 |
| `gr_yinggai_should` 应该 (yīnggāi) should / ought to | 你去看医生吧。 (A polite suggestion: You should/why don’t you go see a doctor.) | Change the note to: “Don’t put 应该 at the end; it normally comes before the verb. Note: You can also give advice with other patterns (…吧, 最好, 得/要…), which don’t  |
| `gr_dei_must` 得 (děi) must / have to | 你不必来。(You don’t need to come.) | To express “don’t have to/need not,” use 不用 or 不必 (also 不需要), not 不得 (which means “must not,” formal). Note: 不得不 + Verb means “have to.” |
| `gr_ji_duoshao` 几 vs 多少 (how many) | 你们班有多少个人？ (How many people are in your class?) | Change to: “几” asks about small numbers and usually takes a measure word (几个苹果、几点、几岁). “多少” can be used for any/unknown amount and often takes a measure word wi |
| `gr_meiyou_comparison` A 没有 B (那么) + adj — not as ... as | 我不比他高。 — I'm not taller than him (could be the same height or shorter). | Explain: 用 “A 没有 B (那么/这么) + Adj” 表示 A 比 B 程度低/“not as … as”(A < B)。Add to note: “不比”表示“not more … than”(A ≤ B)，句子如“我不比他高”是对的，但如果要表达“我比他矮/不如他高”，用“我没有他高”。Remove  |
| `gr_yuelaiyue` 越来越 (yuèláiyuè) more and more | 我越学越喜欢中文。 (The more I study, the more I like Chinese.) | Keep the core pattern, but add: Related alternatives (also correct): 越 + X + 越 + Y (我越学越喜欢中文) and 一天比一天 + 形容词 (天气一天比一天冷)。不要把这些当错。 |
| `gr_yue_yue` 越 A 越 B — the more ... the more | 他越忙越累。 (The busier he is, the more tired he gets.) | Change the pattern to: 越 + A + 越 + B (A/B can be verbs, adjectives, or quantity words/phrases). Add an example like: 他越忙越累；越多越好。 |
| `gr_bi_degree_diff` 比 + adj + amount of difference | 他比我更高。 — He is even taller than me. | With 比, amounts like 一点儿/得多/多了/两公分 go AFTER the adjective: 他比我高一点儿/高得多/高两公分. You can also use 更 before the adjective: 他比我更高. Do not use 很/非常. |
| `gr_ruguo_jiu` 如果……就…… (if ... then) | 如果你有时间，来我家。 — If you have time, come to my place. | Explanation: Use the pattern 如果……，(就)…… — 就 is common but optional. Common mistake: Thinking 就 is required. Both are correct: 如果你有时间，就来我家 / 如果你有时间，来我家。 |
| `gr_zhiyao_jiu` 只要……就…… (as long as) | 只要你是学生，门票才五十块。 (As long as you’re a student, the ticket is only 50 RMB.) | Common mistake: After 只要, link the result with 就 (只要…就…). Don’t use 才 to mean “only then” (that pattern is 只有…才…). Note: 才 can still appear with other meanings  |
| `gr_zhiyou_cai` 只有……才…… (only if) | 我只有三十块钱，就买不了这个包。 (I only have 30 yuan, so I can’t buy this bag.) | Clarify scope: In the ‘only if’ conditional meaning, use 只有…才…, not 只有…就…. But 只有 can also mean ‘only/only have’ (e.g., 我只有三十块钱), and in that use 才 is not neede |
| `gr_yi_jiu` 一……就…… (as soon as) | 你一到家给我打电话。 — As soon as you get home, call me. | Revise the note to: “不要用‘一……然后……’。一般用‘一……就……’。口语里，尤其在要求/提醒时，可以省略‘就’（如：你一到家给我打电话），但用‘就’更保险：你一到家就给我打电话。” |
| `gr_chule_yiwai` 除了……以外 (besides / except) | 除了他以外，没人去。 (Except for him, nobody went.) | 通常“除了……(以外)”要配“都”（表示“除了A，其余都……”）或“还/也”（表示“除了A，还……”）。但如果主句是否定或疑问，或已用到“没人/没有/其他/只有”等限定词，就可以不再用“都/还/也”。 |
| `gr_xian_ranhou` 先……然后…… (first ... then) | 我们吃饭，然后看电影。 (We eat, then watch a movie.) | Change the common-mistake line to: “把‘然后’放在第一件事前面是错的。‘先’可省略：A，然后/再 B 也对。” And tweak the explanation to: “先 marks the first action; 然后或再 the next.” |
| `gr_bushi_ershi` 不是……而是…… (not A but B) | 这不是茶，是咖啡。 (It’s not tea; it’s coffee.) | Teach: 不是A，而是B 用来纠正；口语里也常说：不是A，是B（可以省略“而”）。不要用“但是”直接连接A和B。 |
| `gr_wulun_dou` 无论/不管……都…… (no matter) | 不管天气怎么样，我去。 (No matter what the weather is like, I’m going.) | Edit to: “无论/不管 + … usually takes 都/也 in the main clause. Use 都/也 to sound clear and natural (especially in writing), but in casual speech it can be omitted: 不管 |
| `gr_deshihou` ……的时候 (when / while) | 我小时候住在北京。 (When I was young, I lived in Beijing.) | Use 的时候 after a verb/adjective clause to mean “when”: 我小的时候… / 我吃饭的时候…. But some fixed time expressions don’t need 的时候 and can stand alone before the main claus |
| `gr_yiqian_yihou` 以前 / 以后 clause order | 以前我不喝咖啡。 (In the past, I didn’t drink coffee.) | Keep 以前/以后 after the specific event they modify (下课以后, 睡觉以前). But when 以前/以后 mean “in the past” / “from now on” as a general time word, they can go at the start |
| `gr_dao_resultative` 到 as a resultative (找到 / 看到) | 我看见他了。 (I saw him.) | Change the note to: “Common mistake: Using just 找/看/买 when you mean ‘successfully’ — add a resultative complement to show the result. 到 is one common choice (找到 |
| `gr_jian_perception` 见 for involuntary perception (看见 / 听见) | 我听到一个奇怪的声音。 (I heard a strange sound.) | 见或到都可以作结果补语来表示确实感知到：看见/看到、听见/听到 都常用。表达“无意中感知到”时，不要用单独的 看/听；用 看见/看到、听见/听到。表达有意的活动时，用 看/听 + 宾语：我看了新闻、我听了音乐。例：更自然（表示听到）→ 我听见/听到一个奇怪的声音。 |
| `gr_gei_resultative` Verb + 给 + recipient (送给 / 还给) | 我送他一本书。 (I give him a book.) | With 送/还 you can use either pattern: 送给/还给 + recipient + object, or 送/还 + recipient + object. Both are common: 我送给他一本书 = 我送他一本书；把书还给我 = 还我书。Don’t put 给 at the e |
| `gr_qilai_inchoative` 起来 — inception / 'seem' / recall | 我突然想起那个词了。(I suddenly remembered that word.) | Change the note to: “Don’t read 起来 only as ‘up’, but also don’t force it. For ‘recall/start/seem’, 起来 is common, but other correct options exist: 想起/想到, 看上去, 下雨 |
| `gr_xiaqu_continue` 下去 — continue an action | 老师让我们继续读。 (The teacher told us to continue reading.) | Update the Common mistake note to: “不要把‘继续’和‘下来’连用。可以说 ‘继续+动词’（老师让我们继续读），也可以说 ‘动词+下去’（老师让我们读下去）。‘继续读下来’不自然。” |
| `gr_cong_dao` 从……到…… (from ... to) | 我九点到五点上班。 (I work from 9 to 5.) | Change the note to: “Don’t put the time range after the verb (e.g., 我工作九点到五点 is unnatural). Note: A 到 B without 从 is also common and correct when the range is c |
| `gr_li_distance` 离 (lí) distance from | 从我家到学校不远。 (From my home to the school is not far.) | Change the note to: “Don’t use 从 by itself for static distance (我家从学校很近 ✗). Use 离: 我家离学校很近 ✓. You can also use 从A到B with distance/time or 远/不远: 从我家到学校不远 / 走十分钟  |
| `gr_gei_coverb` 给 (gěi) + recipient + verb (for / to) | 我打电话给你。 (I’ll call you.) | Teach both common orders and note verbs that don’t use 给: 给 + recipient + 动词, and also 动词 + 给 + recipient are both common with many verbs (e.g., 我给你打电话 / 我打电话给你 |
| `gr_weile_purpose` 为了 (wèile) in order to | 我学中文是为了找到好工作。 (I study Chinese in order to find a good job.) | Allow more positions: 为了+目的 can go at the start (为了找到好工作，我在学中文) or after the subject (我为了找到好工作在学中文); it can also follow the main clause with 是 (我学中文是为了找到好工作). T |
| `gr_yong_instrument` 用 (yòng) + tool + verb (by means of) | 我吃饭用筷子。 (I eat with chopsticks.) | Update the common-mistake note to: “不要把‘用’省略。工具短语可以放在动词前，也可以放在动词（或动宾结构）后：我用筷子吃饭／我吃饭用筷子。‘我吃饭筷子’（没有‘用’）是不对的。” |
| `gr_zai_location_verb` 在 + place + verb (do at a location) | 我住在北京。 (I live in Beijing.) | Explanation: For most activities, put 在 + place before the verb: 我在图书馆学习. But with location verbs like 住/坐/站/放, 在 follows the verb: 我住在北京, 他坐在椅子上. Common mistak |
| `gr_shi_identity` 是 (shì) identity — no 是 before an adjective | 这是对的。 (This is correct.) | Edit to: “Don’t use 是 before a bare adjective predicate — use 很/不 instead: 他很忙/他不高. But when the adjective is turned into a noun with 的, 是 is fine: 这是对的/这个菜是辣的/ |
| `gr_zai_location` 在 (zài) to be located at | 桌子上有我的手机。 (On the table there is my phone.) | Common mistake: Don’t put 有 or 是 after the thing as the subject to express its location (e.g., 我的手机有/是桌子上✗). Use 在: 我的手机在桌子上✓. Note: Use 有 when the place is the |
| `gr_duo_approx` Number + 多 approximation | 一百块多。 — a bit over 100 RMB. | Teach both orders: 多 can go after the number or after the measure word: 三十多岁 / 三十岁多；一百多块 / 一百块多。Don’t put 多 before the number (×他多三十岁). Note: “more than” can al |
| `gr_di_ordinal` 第 (dì) ordinal numbers | 今天三号。 — Today is the 3rd (of the month). | Common mistake: Omitting 第 when it’s needed before many ordered nouns like 次/个/位/课/题 (e.g., 第一次、第三个、第三位、第三课、第三题). But don’t use 第 with set labels like dates and |
| `gr_mei_every` 每 (měi) + measure word (every) | 我每天跑步。 (I run every day.) | Clarify: 每 + (量词) + 名词. With common time words, don’t add 个: 每天、每年、每月、每星期/每周；also fixed form 每人. Use 都 when the 每‑phrase is the subject meaning “each …” (每个学生都喜 |
| `gr_xie_some` 些 / 一些 / 这些 (some, plural) | 我们在找一些个子高的学生。 (We’re looking for some tall students.) | Say: “Don’t put a classifier right after 些 when 些 directly modifies the noun (一些苹果, 这些人). But if 个 is part of the next word (e.g., 个人, 个子), that’s fine: 我有一些个人的 |
| `gr_money_spoken` Spoken money (块 / 毛 / 分) | 我花了二十元。 — I spent 20 yuan. | Explanation: In casual speech, people usually say 块(=元), 毛(=角), 分, big unit first: 三块五, 十块二毛. 元 is also fine in speech (more neutral/formal), and 角 is less comm |
| `gr_adj_predicate_hen` Adjective predicate takes 很, not 是 | 今天天气好。 (The weather is good today.) | Revise to: “For neutral statements with adjective predicates, we usually add 很 and not 是: 他很高. But bare adjectives are also correct in common patterns like topi |
| `gr_dou_all` 都 (dōu) all/both — before the verb, scope to its left | （A：你要茶还是咖啡？）B：都可以。  “Either is fine.” | Change to: “都 is placed before the predicate (verb/adj) and quantifies something already given (usually to its left in the sentence or understood from context). |
| `gr_zai_you_again` 再 vs 又 (again: future vs past) | 明天又要下雨了。 (It’s going to rain again tomorrow.) | Revise explanation: 再 = again for a planned/intended future action (often a request/suggestion): 再说一次。又 = again for something that has happened before and is ha |
| `gr_zhi_only` 只 (zhǐ) only — before the verb | 我就一个问题。 (I only have one question.) | Keep: “只放在动词前：我只有十块钱 / 他只喜欢你。不要把‘只’放在动词后。” Replace the ‘common mistake’ with: “注意：就也可以表示‘只有’，常见于数量/时间前或‘一个…’：我就一个问题 / 我就两块钱。这些用法是对的，本课只讲‘只’放在动词前。” |
| `gr_tai_le` 太……了 (too / so) | 这个不太贵。 (This isn’t too expensive.) | Only require 了 when 太 + Adjective is a standalone exclamation/comment (e.g., 这个太贵了). Do not add 了 in 不太 + Adjective (这个不太贵) or when 太 + Adjective modifies a nou |
| `gr_verb_reduplication` Verb reduplication (看看 / 休息休息) | 我们聊聊天吧。 (Let's chat a bit.) | Clarify patterns: Monosyllabic verbs: AA / A一A (also A了A, e.g., 看了看). Two-syllable simple verbs: ABAB (休息休息). For verb–object verbs like 聊天/唱歌/跳舞, reduplicate t |
| `gr_lai_qu_purpose` 来/去 + verb phrase (come/go to do) | 我去商店是为了买东西。 (I'm going to the shop in order to buy things.) | Common mistake: Putting 为了 right after 来/去 in this pattern. Usually you don’t need any extra marker: 来/去 + (place) + VP → 我去商店买东西。 If you want to use 为了, put it |

## Detail

### `gr_ba_disposal` — 把 (bǎ) disposal construction
- **common_mistake (current):** English speakers use 把 with a bare verb and no result (把书看), or use it with intransitive/stative verbs, or combine it with 被 in the same clause.
- **would wrongly reject:** 请把书给我。 (Please give me the book.)
- **fix:** Clarify that the verb just can’t be bare; it must be followed by something — a result/directional/state complement, 了/着, a duration/measure or location phrase, OR a second object/recipient (e.g., 把书给我/把钱还给他/把书放在桌子上).

### `gr_bei_passive` — 被 (bèi) passive construction
- **common_mistake (current):** Combining 被 with 把 in one clause, or leaving the verb bare with no complement.
- **would wrongly reject:** 我没被邀请。 (I wasn’t invited.)
- **fix:** Edit the line to: “In 被-sentences the verb phrase is usually not bare — it often has 了, a result, an object, or other info. But after 没/没有 don’t use 了 (我没被邀请), and some verbs (e.g., 取消/邀请/允许) are fine without 了 (比赛被取消).” Keep the ‘don’t mix 被 and 把’ note.

### `gr_le_change` — 了 (le) as change of state (sentence-final)
- **common_mistake (current):** Omitting sentence-final 了 when reporting a new state, or confusing it with the verbal completion 了.
- **would wrongly reject:** 我饿。 (I’m hungry.)
- **fix:** Add: “Sentence-final 了 highlights a new/changed situation; it’s not required if you’re simply stating a current fact.” Update Common mistake: “Thinking you must always add 了—use 我饿了 to stress the change (‘I’m hungry now/already’), but 我饿 is also correct as a plain statement.” Update example: “If you mean ‘I’ve just turned twenty,’ say 我今年二十岁了; if you’re just stating age, 我今年二十岁 is fine.”

### `gr_shi_de` — 是……的 (shì...de) emphasis construction
- **common_mistake (current):** Using 了 instead of 是……的 to highlight the time/place/manner of a known past event.
- **would wrongly reject:** 你怎么来的？ (How did you get here/by what means?)
- **fix:** Common mistake: Thinking you must use 是……的. Plain past with 了 is also correct; 是……的 just adds focus to the time/place/manner. For example, 你怎么来的？ and 你是怎么来的？ are both correct (the latter is more emphatic). Note: 是 is often optional in this pattern: 我是昨天来的 / 我昨天来的。

### `gr_measure_words` — Measure words (量词)
- **common_mistake (current):** Dropping the measure word (三书) or defaulting to 个 for everything (三个书).
- **would wrongly reject:** 我们两人都去。 (The two of us are going.)
- **fix:** Change to: “Chinese usually requires a measure word between a number/demonstrative and a noun: Number + Measure Word + Noun. Common beginner exceptions: with ordinals 第 + number, some nouns don’t take a measure word (e.g., 第一课, 第三章); with 人, forms like 一人/两人/三人 are common (我们两人), though 两个人 is also fine.”

### `gr_zai_progressive` — 在/正在 (zài/zhèngzài) progressive aspect
- **common_mistake (current):** Applying 在……呢 to stative verbs (在知道), or confusing progressive 在 with the locational 在 (to be at).
- **would wrongly reject:** 我看书呢。 (I'm reading.)
- **fix:** Clarify that 呢 can also directly mark an action in progress by itself after the verb: 我看书呢。 You can also combine it with 在/正在 for extra emphasis: 我在看书呢。 (Still avoid stative verbs: not 在知道.)

### `gr_de_complement` — 得 (de) degree/manner complement
- **common_mistake (current):** Omitting the repeated verb when there is an object (他说汉语得很好), or confusing 得 with 的/地.
- **would wrongly reject:** 他把字写得很漂亮。 (He writes characters very beautifully.)
- **fix:** Say: Use V + O + V + 得 + complement when the object comes directly after the verb (他说汉语说得很好). If the object is moved before the verb (topic or in 把/被), don’t repeat the verb: 汉语他说得很好；他把字写得很漂亮。 It’s also fine to drop the object if it’s clear: 他说得很好。

### `gr_de_di_de` — 的 / 得 / 地 (de) distinction
- **common_mistake (current):** Writing 的 for all three because they sound the same.
- **would wrongly reject:** 他认真学习汉语。 (He studies Chinese diligently.)
- **fix:** Add: “地 usually marks an adverbial before a verb, but in modern usage it’s often omitted with common short adverbials/adjectives: 慢慢走、认真学习 are also correct. Don’t mark these as wrong.”

### `gr_time_before_place` — Word order: time and place before the verb
- **common_mistake (current):** Following English order and putting time/place after the verb or object.
- **would wrongly reject:** 我住在北京。 (I live in Beijing.)
- **fix:** Edit the explanation to: “Time-when goes before the verb. Place is often set with 在 + place before the verb (我明天在家看书), but with many verbs it naturally comes after the verb: 我明年去中国, 我住在北京, 把书放在桌子上. Don’t put a time word at the very end (✗ 我去中国明年).”

### `gr_duration_complement` — Duration complement (time how long)
- **common_mistake (current):** Placing the duration before the verb like a time-when phrase (我两年学汉语).
- **would wrongly reject:** 我三天没吃饭。 (I haven’t eaten for three days.)
- **fix:** Clarify: In affirmative sentences, duration goes after the verb. With an object, you can use (a) V 了 Duration O (我学了两年汉语), (b) V O V 了 Duration (我学汉语学了两年), or (c) V 了 O Duration when the object is short/specific (e.g., pronouns): 我等了你三个小时。 Note: In negative “how long not” sentences, put duration before 没/不: 我三天没吃饭。

### `gr_liang_er` — 两 (liǎng) vs 二 (èr)
- **common_mistake (current):** Using 二 before a measure word (二个人).
- **would wrongly reject:** 你是第二个人。 (You are the second person.)
- **fix:** Revise the common-mistake note: “不要在量词前用‘二’来表示‘两个’（×二个人 → ✓两个人；×二杯 → ✓两杯）。但在这些情况下用‘二’没问题：第二个、二十个；以及和百/千/万/亿连用时（如二百/两百都可以）。”

### `gr_youdianr_yidianr` — 有点儿 (yǒudiǎnr) vs 一点儿 (yìdiǎnr)
- **common_mistake (current):** Swapping them: 一点儿贵 or 有点儿便宜 in the wrong slot.
- **would wrongly reject:** 这个有点儿便宜。 (This is a bit too cheap.)
- **fix:** 有点儿 + 形容词多表示轻微抱怨/不理想（有点儿贵）。当“便宜”被视为不理想时，也可以说“有点儿便宜”。形容词 + 一点儿用于比较，表示“再/更……一点儿”（便宜一点儿）。不要把“一点儿”放在形容词前（不用：一点儿贵）。

### `gr_hui_neng_keyi` — 会 / 能 / 可以 (huì/néng/kěyǐ) modals
- **common_mistake (current):** Using 能 for learned skills or 会 for permission.
- **would wrongly reject:** 我能说三种语言。 (I can speak three languages.)
- **fix:** Change the “Common mistake” to: “For learned skills, 会 is more natural; 能 is also used and not wrong. Use 可以 (not 会) for permission.” Update the example label to: “Less natural: 我能说三种语言。 → More natural: 我会说三种语言。”

### `gr_jiu_cai` — 就 (jiù) vs 才 (cái)
- **common_mistake (current):** Adding 了 after 才, or reversing the earlier/later nuance.
- **would wrongly reject:** 他九点才来了。 (He didn’t come until nine.)
- **fix:** Revise the note to: “With 才, don’t put 了 right after the verb in simple past statements (他九点才来). Sentence-final 了 is OK to show a new situation: 他九点才来了。”

### `gr_resultative` — Resultative complements (看完, 听懂)
- **common_mistake (current):** Expressing the result separately in English style, or negating with 不 (不看完).
- **would wrongly reject:** 我听不懂老师的话。 (I can’t understand what the teacher says.)
- **fix:** Negate a result that didn’t happen with 没(有): 我没看完。/ 我没听懂。 To express inability or predicted non-completion, put 不 between the verb and the result: 我看不完、听不懂、找不到。Don’t use 不 before the whole verb-result chunk (×我不听懂).

### `gr_directional` — Directional complements (进来, 出去)
- **common_mistake (current):** Wrong order of the place object and 来/去, or omitting the direction.
- **would wrongly reject:** 我回家。 — I’m going home.
- **fix:** Edit the explanation to: “If there is a place noun, put it before 来/去, but 来/去 is optional and only used to show toward/away from the speaker: 他跑进教室(来); 我回家。” Edit the common-mistake line to remove “or omitting the direction,” leaving: “Wrong order of the place object and 来/去 (don’t put 来/去 before the place).”

### `gr_yinwei_suoyi` — 因为……所以…… (yīnwèi...suǒyǐ) cause and result
- **common_mistake (current):** Assuming that using both 'because' and 'so' is wrong, as it would be in English, and dropping 所以.
- **would wrongly reject:** 因为下雨，我没去。 (Because it rained, I didn’t go.)
- **fix:** Explanation: 因为…所以… is a common and natural pairing, but in everyday Chinese 所以 is often optional after 因为; you can also use only 所以 (…，所以…). Common mistake: Thinking you must not use both, or that you must always use both—actually both 因为……所以…… and 因为……(结果) are correct. Examples: 因为下雨，所以我没去。/ 因为下雨，我没去。/ 下雨了，所以我没去。

### `gr_suiran_danshi` — 虽然……但是…… (suīrán...dànshì) although
- **common_mistake (current):** Dropping 但是 because English uses only 'although'.
- **would wrongly reject:** 虽然很累，我很开心。 (Although I’m tired, I’m happy.)
- **fix:** Revise explanation: “虽然 (although) often pairs with 但是/可是 (but), but 但是/可是 is optional when the contrast is clear. Both 虽然很累，但是我很开心 and 虽然很累，我很开心 are correct.” Update common mistake: “Not a mistake to drop 但是—just ensure the second clause shows the contrast.”

### `gr_haishi_huozhe` — 还是 (háishì) vs 或者 (huòzhě) — 'or'
- **common_mistake (current):** Using 或者 in a choice question or 还是 in a statement.
- **would wrongly reject:** 我不知道他是学生还是老师。 (I don’t know whether he is a student or a teacher.)
- **fix:** Edit Common mistake to: “Using 或者 in a choice question.” Add a note to the Explanation: “Use 还是 for ‘or’ in direct questions. In normal statements, use 或者. But if the ‘or’ part is inside a clause (after 我不知道/问/告诉/看看 etc.), still use 还是: 我不知道他是学生还是老师；请告诉我你要茶还是咖啡。”

### `gr_double_le` — Verb + 了 + object + 了 (ongoing up to now)
- **common_mistake (current):** Using one 了 and losing the 'and still continuing' meaning.
- **would wrongly reject:** 我学汉语两年了。 (I have been studying Chinese for two years.)
- **fix:** Teach: To express “started before and still true now,” include sentence‑final 了. A common pattern is V + 了 + Duration + 了 (e.g., 我在这儿住了三年了), but the first 了 is optional in many sentences (e.g., 我学汉语两年了／我已经学汉语两年了／他们结婚三年了). Common mistake: leaving off the sentence‑final 了 when you mean it’s still true (我在这儿住了三年 → sounds finished).

### `gr_zhe_durative` — 着 (zhe) durative / accompanying state
- **common_mistake (current):** Using 着 for a plain ongoing action where 在 is needed, or dropping 着 for an accompanying manner.
- **would wrongly reject:** 我正吃着饭呢。 (I'm eating right now.)
- **fix:** Revise the explanation to: “Verb + 着 usually marks a continuing state or a manner accompanying another action (V1着 + V2): 门开着, 他笑着说. For actions in progress, use 在/正在/呢; note that in colloquial speech V + 着 + 呢 also shows an action in progress (e.g., 我正吃着饭呢).” Revise the common mistake to: “Using 着 alone for a plain ongoing action — say 我在/正在看电视呢; V + 着 + 呢 is also acceptable (我正打着电话呢). Dropping 着 in the V1着 + V2 pattern can be wrong (他站着看书).”

### `gr_yao_le_imminent` — (快)要……了 imminent action
- **common_mistake (current):** Omitting the final 了, or using 会 for an imminent event.
- **would wrongly reject:** 一会儿会下雨。 (It will rain soon.)
- **fix:** Change “The final 了 is required.” to “In this pattern, 了 is normally used to show ‘about to’; without 了 it often just means a plan/general future, not ‘about to’.” Change the mistake note to: “For the ‘about to’ meaning, don’t forget 了. 会 can also talk about future likelihood (e.g., 一会儿会下雨), but it doesn’t give the strong ‘about to’ sense.”

### `gr_le_negation_drop` — 没 negates a completed action and drops 了
- **common_mistake (current):** Keeping 了 after 没 (没……了).
- **would wrongly reject:** 他没来了。 (He isn’t coming anymore / He didn’t come after all.)
- **fix:** Say: “To negate a completed action, use 没(有) + V and do not use the perfective 了 right after the verb: 我没去 (not 我没去‘了’ for simple negation). Note: sentence‑final 了 (change of situation) can appear: 他没来了 (= 他不来了); 糟了，我没带手机了。”

### `gr_ma_question` — 吗 (ma) yes/no question particle
- **common_mistake (current):** Adding 吗 to a question that already has a question word (哪儿 / 什么 / 谁).
- **would wrongly reject:** 你有什么问题吗？ — Do you have any questions?
- **fix:** Revise to: “Add 吗 at the end of a statement to make a yes/no question (你是学生吗？). Do not add 吗 when a question word is asking for specific information (谁、什么、哪儿、什么时候…): 你去哪儿？ Not 你去哪儿吗？ But when words like 什么/谁/哪儿 don’t ask for specifics and mean ‘any/some/every’—often after 有/没有 or with 都/也—you can use 吗: 你有什么问题吗？ 哪儿都可以吗？”

### `gr_ba_suggestion` — 吧 (ba) suggestion / supposition
- **common_mistake (current):** Using 吗 for a suggestion or a 'right?' supposition where 吧 is natural.
- **would wrongly reject:** 你是老师吗？ (Are you a teacher?)
- **fix:** Tweak the “Common mistake” to: Use 吧 when you want to make a suggestion or a tentative “I think…” guess; use 吗 for a neutral yes/no question. For example: 我们走吗？= “Are we leaving?” (neutral question); 我们走吧。= “Let’s go.” 你是老师吗？= “Are you a teacher?”; 你是老师吧？= “You’re a teacher, right?” Also relabel the example as “Different meaning (a real question): 我们走吗？现在很晚了。 To make a suggestion, say: 我们走吧，现在很晚了。”

### `gr_hui_de_certainty` — 会……的 future certainty
- **common_mistake (current):** Dropping 会 or the framing 的; using 要 for a confident prediction.
- **would wrongly reject:** 别担心，他会来。 (Don't worry, he will come.)
- **fix:** Explain: “会 + Verb (+ 的) expresses a confident prediction; 的 adds reassurance/emphasis and is optional.” Common mistake: “Dropping 会 (changes the meaning). 要 is usually for plans/arrangements or something imminent; for a neutral prediction use 会.”

### `gr_xiang_yao_want` — 想 vs 要 (to want)
- **common_mistake (current):** Using 要 for a polite wish where 想 is more appropriate.
- **would wrongly reject:** 我要一杯咖啡，谢谢。 (I'd like a cup of coffee, thanks.)
- **fix:** Clarify tone vs. correctness and limit the warning to deferential requests: “想 + 动词 = 较委婉；要 + 动词 = 更坚定/打算（语气更强）。在需要表示客气的请求（如对老师/陌生人求助）里，用 想/想要 或 加上 能/可以…吗 来委婉；在点单、说明计划等场合，用 要 很自然：我要一杯咖啡；明天我要去北京。” Also change the example label from “incorrect” to “less polite → more polite.”

### `gr_yinggai_should` — 应该 (yīnggāi) should / ought to
- **common_mistake (current):** Placing 应该 at the end like an English tag, or omitting it.
- **would wrongly reject:** 你去看医生吧。 (A polite suggestion: You should/why don’t you go see a doctor.)
- **fix:** Change the note to: “Don’t put 应该 at the end; it normally comes before the verb. Note: You can also give advice with other patterns (…吧, 最好, 得/要…), which don’t use 应该.”

### `gr_dei_must` — 得 (děi) must / have to
- **common_mistake (current):** Negating with 不得 to mean 'don't have to'.
- **would wrongly reject:** 你不必来。(You don’t need to come.)
- **fix:** To express “don’t have to/need not,” use 不用 or 不必 (also 不需要), not 不得 (which means “must not,” formal). Note: 不得不 + Verb means “have to.”

### `gr_ji_duoshao` — 几 vs 多少 (how many)
- **common_mistake (current):** Using 几 for large amounts, or inserting a measure word that is not needed after 多少.
- **would wrongly reject:** 你们班有多少个人？ (How many people are in your class?)
- **fix:** Change to: “几” asks about small numbers and usually takes a measure word (几个苹果、几点、几岁). “多少” can be used for any/unknown amount and often takes a measure word with countable nouns: 多少本书、多少个人. For money, both 多少钱 and 多少块(钱) are correct. Common mistake: omitting the measure word after 几, or after 多少 when the noun requires one.

### `gr_meiyou_comparison` — A 没有 B (那么) + adj — not as ... as
- **common_mistake (current):** Using 不比 (which means 'not necessarily more than') to mean 'not as ... as'.
- **would wrongly reject:** 我不比他高。 — I'm not taller than him (could be the same height or shorter).
- **fix:** Explain: 用 “A 没有 B (那么/这么) + Adj” 表示 A 比 B 程度低/“not as … as”(A < B)。Add to note: “不比”表示“not more … than”(A ≤ B)，句子如“我不比他高”是对的，但如果要表达“我比他矮/不如他高”，用“我没有他高”。Remove the label ‘incorrect: 我不比他高’.

### `gr_yuelaiyue` — 越来越 (yuèláiyuè) more and more
- **common_mistake (current):** Calquing English with 更来更 or repeated 比.
- **would wrongly reject:** 我越学越喜欢中文。 (The more I study, the more I like Chinese.)
- **fix:** Keep the core pattern, but add: Related alternatives (also correct): 越 + X + 越 + Y (我越学越喜欢中文) and 一天比一天 + 形容词 (天气一天比一天冷)。不要把这些当错。

### `gr_yue_yue` — 越 A 越 B — the more ... the more
- **common_mistake (current):** Using 更 twice, or English 'the more ... the more' word order.
- **would wrongly reject:** 他越忙越累。 (The busier he is, the more tired he gets.)
- **fix:** Change the pattern to: 越 + A + 越 + B (A/B can be verbs, adjectives, or quantity words/phrases). Add an example like: 他越忙越累；越多越好。

### `gr_bi_degree_diff` — 比 + adj + amount of difference
- **common_mistake (current):** Placing the amount before the adjective, or using 很/非常.
- **would wrongly reject:** 他比我更高。 — He is even taller than me.
- **fix:** With 比, amounts like 一点儿/得多/多了/两公分 go AFTER the adjective: 他比我高一点儿/高得多/高两公分. You can also use 更 before the adjective: 他比我更高. Do not use 很/非常.

### `gr_ruguo_jiu` — 如果……就…… (if ... then)
- **common_mistake (current):** Dropping 就 in the result clause.
- **would wrongly reject:** 如果你有时间，来我家。 — If you have time, come to my place.
- **fix:** Explanation: Use the pattern 如果……，(就)…… — 就 is common but optional. Common mistake: Thinking 就 is required. Both are correct: 如果你有时间，就来我家 / 如果你有时间，来我家。

### `gr_zhiyao_jiu` — 只要……就…… (as long as)
- **common_mistake (current):** Pairing 只要 with 才 (that belongs to 只有).
- **would wrongly reject:** 只要你是学生，门票才五十块。 (As long as you’re a student, the ticket is only 50 RMB.)
- **fix:** Common mistake: After 只要, link the result with 就 (只要…就…). Don’t use 才 to mean “only then” (that pattern is 只有…才…). Note: 才 can still appear with other meanings like “only (amount)” or “just now”: 只要你是学生，门票才五十块。

### `gr_zhiyou_cai` — 只有……才…… (only if)
- **common_mistake (current):** Pairing 只有 with 就 (that belongs to 只要).
- **would wrongly reject:** 我只有三十块钱，就买不了这个包。 (I only have 30 yuan, so I can’t buy this bag.)
- **fix:** Clarify scope: In the ‘only if’ conditional meaning, use 只有…才…, not 只有…就…. But 只有 can also mean ‘only/only have’ (e.g., 我只有三十块钱), and in that use 才 is not needed and 就 may appear in the next clause as ‘then/so’.

### `gr_yi_jiu` — 一……就…… (as soon as)
- **common_mistake (current):** Using 然后 for the immediate second event, or dropping 就.
- **would wrongly reject:** 你一到家给我打电话。 — As soon as you get home, call me.
- **fix:** Revise the note to: “不要用‘一……然后……’。一般用‘一……就……’。口语里，尤其在要求/提醒时，可以省略‘就’（如：你一到家给我打电话），但用‘就’更保险：你一到家就给我打电话。”

### `gr_chule_yiwai` — 除了……以外 (besides / except)
- **common_mistake (current):** Dropping the paired 都/还/也 in the main clause.
- **would wrongly reject:** 除了他以外，没人去。 (Except for him, nobody went.)
- **fix:** 通常“除了……(以外)”要配“都”（表示“除了A，其余都……”）或“还/也”（表示“除了A，还……”）。但如果主句是否定或疑问，或已用到“没人/没有/其他/只有”等限定词，就可以不再用“都/还/也”。

### `gr_xian_ranhou` — 先……然后…… (first ... then)
- **common_mistake (current):** Reversing 先/然后 or omitting 先.
- **would wrongly reject:** 我们吃饭，然后看电影。 (We eat, then watch a movie.)
- **fix:** Change the common-mistake line to: “把‘然后’放在第一件事前面是错的。‘先’可省略：A，然后/再 B 也对。” And tweak the explanation to: “先 marks the first action; 然后或再 the next.”

### `gr_bushi_ershi` — 不是……而是…… (not A but B)
- **common_mistake (current):** Using 但是 instead of 而是 for a correction.
- **would wrongly reject:** 这不是茶，是咖啡。 (It’s not tea; it’s coffee.)
- **fix:** Teach: 不是A，而是B 用来纠正；口语里也常说：不是A，是B（可以省略“而”）。不要用“但是”直接连接A和B。

### `gr_wulun_dou` — 无论/不管……都…… (no matter)
- **common_mistake (current):** Dropping 都/也, or using 虽然.
- **would wrongly reject:** 不管天气怎么样，我去。 (No matter what the weather is like, I’m going.)
- **fix:** Edit to: “无论/不管 + … usually takes 都/也 in the main clause. Use 都/也 to sound clear and natural (especially in writing), but in casual speech it can be omitted: 不管天气怎么样，我（都）去。” Update the mistake note to: “Don’t replace 无论/不管 with 虽然.”

### `gr_deshihou` — ……的时候 (when / while)
- **common_mistake (current):** Using an English-style front 'when' without 的时候.
- **would wrongly reject:** 我小时候住在北京。 (When I was young, I lived in Beijing.)
- **fix:** Use 的时候 after a verb/adjective clause to mean “when”: 我小的时候… / 我吃饭的时候…. But some fixed time expressions don’t need 的时候 and can stand alone before the main clause: 小时候，我住在北京。Both 我小的时候 and 我小时候 are correct.

### `gr_yiqian_yihou` — 以前 / 以后 clause order
- **common_mistake (current):** Following English order and putting 以前/以后 first.
- **would wrongly reject:** 以前我不喝咖啡。 (In the past, I didn’t drink coffee.)
- **fix:** Keep 以前/以后 after the specific event they modify (下课以后, 睡觉以前). But when 以前/以后 mean “in the past” / “from now on” as a general time word, they can go at the start: 以前我不喝咖啡；以后我早点睡；以后下课就回家。 For the example, say: 下课以后我回家 (after class I go home). If you mean “from now on,” use: 以后下课就回家。

### `gr_dao_resultative` — 到 as a resultative (找到 / 看到)
- **common_mistake (current):** Omitting 到, so successful attainment is not expressed.
- **would wrongly reject:** 我看见他了。 (I saw him.)
- **fix:** Change the note to: “Common mistake: Using just 找/看/买 when you mean ‘successfully’ — add a resultative complement to show the result. 到 is one common choice (找到/看到/买到), but alternatives like 看见、找着 are also correct.”

### `gr_jian_perception` — 见 for involuntary perception (看见 / 听见)
- **common_mistake (current):** Using bare 看/听 when the perceptual result is meant.
- **would wrongly reject:** 我听到一个奇怪的声音。 (I heard a strange sound.)
- **fix:** 见或到都可以作结果补语来表示确实感知到：看见/看到、听见/听到 都常用。表达“无意中感知到”时，不要用单独的 看/听；用 看见/看到、听见/听到。表达有意的活动时，用 看/听 + 宾语：我看了新闻、我听了音乐。例：更自然（表示听到）→ 我听见/听到一个奇怪的声音。

### `gr_gei_resultative` — Verb + 给 + recipient (送给 / 还给)
- **common_mistake (current):** Omitting 给 or misordering the recipient.
- **would wrongly reject:** 我送他一本书。 (I give him a book.)
- **fix:** With 送/还 you can use either pattern: 送给/还给 + recipient + object, or 送/还 + recipient + object. Both are common: 我送给他一本书 = 我送他一本书；把书还给我 = 还我书。Don’t put 给 at the end (✗我送他一本书给).

### `gr_qilai_inchoative` — 起来 — inception / 'seem' / recall
- **common_mistake (current):** Reading 起来 only literally as 'up' and omitting it for these senses.
- **would wrongly reject:** 我突然想起那个词了。(I suddenly remembered that word.)
- **fix:** Change the note to: “Don’t read 起来 only as ‘up’, but also don’t force it. For ‘recall/start/seem’, 起来 is common, but other correct options exist: 想起/想到, 看上去, 下雨了/开始下雨了. For example: 我突然想起/想到那个词了 都可以。”

### `gr_xiaqu_continue` — 下去 — continue an action
- **common_mistake (current):** Using 下来 for 'continue', or 继续 awkwardly without the complement.
- **would wrongly reject:** 老师让我们继续读。 (The teacher told us to continue reading.)
- **fix:** Update the Common mistake note to: “不要把‘继续’和‘下来’连用。可以说 ‘继续+动词’（老师让我们继续读），也可以说 ‘动词+下去’（老师让我们读下去）。‘继续读下来’不自然。”

### `gr_cong_dao` — 从……到…… (from ... to)
- **common_mistake (current):** Using 到 alone, or following English word order with the times after the verb.
- **would wrongly reject:** 我九点到五点上班。 (I work from 9 to 5.)
- **fix:** Change the note to: “Don’t put the time range after the verb (e.g., 我工作九点到五点 is unnatural). Note: A 到 B without 从 is also common and correct when the range is clear, especially with times/places: 我九点到五点上班 / 星期一到星期五 / 北京到上海。”

### `gr_li_distance` — 离 (lí) distance from
- **common_mistake (current):** Using 从 for a static distance.
- **would wrongly reject:** 从我家到学校不远。 (From my home to the school is not far.)
- **fix:** Change the note to: “Don’t use 从 by itself for static distance (我家从学校很近 ✗). Use 离: 我家离学校很近 ✓. You can also use 从A到B with distance/time or 远/不远: 从我家到学校不远 / 走十分钟 ✓.”

### `gr_gei_coverb` — 给 (gěi) + recipient + verb (for / to)
- **common_mistake (current):** Omitting 给, or following English order (verb before recipient) where the coverb is expected.
- **would wrongly reject:** 我打电话给你。 (I’ll call you.)
- **fix:** Teach both common orders and note verbs that don’t use 给: 给 + recipient + 动词, and also 动词 + 给 + recipient are both common with many verbs (e.g., 我给你打电话 / 我打电话给你; 给他写信 / 写信给他). Don’t add 给 with verbs that take a person directly (e.g., 我告诉你, 我问他, 我帮你).

### `gr_weile_purpose` — 为了 (wèile) in order to
- **common_mistake (current):** Placing the purpose at the end, or using 因为 (because) for a purpose.
- **would wrongly reject:** 我学中文是为了找到好工作。 (I study Chinese in order to find a good job.)
- **fix:** Allow more positions: 为了+目的 can go at the start (为了找到好工作，我在学中文) or after the subject (我为了找到好工作在学中文); it can also follow the main clause with 是 (我学中文是为了找到好工作). The real mistake is using 因为 to express purpose.

### `gr_yong_instrument` — 用 (yòng) + tool + verb (by means of)
- **common_mistake (current):** Following English 'with ...' order and putting the tool after the verb.
- **would wrongly reject:** 我吃饭用筷子。 (I eat with chopsticks.)
- **fix:** Update the common-mistake note to: “不要把‘用’省略。工具短语可以放在动词前，也可以放在动词（或动宾结构）后：我用筷子吃饭／我吃饭用筷子。‘我吃饭筷子’（没有‘用’）是不对的。”

### `gr_zai_location_verb` — 在 + place + verb (do at a location)
- **common_mistake (current):** Following English order and putting the place after the verb.
- **would wrongly reject:** 我住在北京。 (I live in Beijing.)
- **fix:** Explanation: For most activities, put 在 + place before the verb: 我在图书馆学习. But with location verbs like 住/坐/站/放, 在 follows the verb: 我住在北京, 他坐在椅子上. Common mistake: For activity verbs (学习/工作/吃/玩 etc.), don’t say 我学习在图书馆 → use 我在图书馆学习. Sentences like 我住在北京 are correct.

### `gr_shi_identity` — 是 (shì) identity — no 是 before an adjective
- **common_mistake (current):** Inserting 是 before an adjective (他是高 / 他是很忙).
- **would wrongly reject:** 这是对的。 (This is correct.)
- **fix:** Edit to: “Don’t use 是 before a bare adjective predicate — use 很/不 instead: 他很忙/他不高. But when the adjective is turned into a noun with 的, 是 is fine: 这是对的/这个菜是辣的/这件衣服是新的.” Update the mistake note: “Wrong: 他是高、他是很忙. (But 是 + 形容词 + 的 is OK: 他是对的.)”

### `gr_zai_location` — 在 (zài) to be located at
- **common_mistake (current):** Using 有 or 是 for the location of a specific known thing.
- **would wrongly reject:** 桌子上有我的手机。 (On the table there is my phone.)
- **fix:** Common mistake: Don’t put 有 or 是 after the thing as the subject to express its location (e.g., 我的手机有/是桌子上✗). Use 在: 我的手机在桌子上✓. Note: Use 有 when the place is the subject to say what is there: 桌子上有一部手机/有我的手机.

### `gr_duo_approx` — Number + 多 approximation
- **common_mistake (current):** Putting 多 before the number, or omitting it for 'more than'.
- **would wrongly reject:** 一百块多。 — a bit over 100 RMB.
- **fix:** Teach both orders: 多 can go after the number or after the measure word: 三十多岁 / 三十岁多；一百多块 / 一百块多。Don’t put 多 before the number (×他多三十岁). Note: “more than” can also be expressed with 超过/以上/多于, which are also correct.

### `gr_di_ordinal` — 第 (dì) ordinal numbers
- **common_mistake (current):** Omitting 第 for an ordinal (using a bare cardinal).
- **would wrongly reject:** 今天三号。 — Today is the 3rd (of the month).
- **fix:** Common mistake: Omitting 第 when it’s needed before many ordered nouns like 次/个/位/课/题 (e.g., 第一次、第三个、第三位、第三课、第三题). But don’t use 第 with set labels like dates and floors: 今天三号, 我住在三楼。

### `gr_mei_every` — 每 (měi) + measure word (every)
- **common_mistake (current):** Omitting the measure word after 每, or dropping 都.
- **would wrongly reject:** 我每天跑步。 (I run every day.)
- **fix:** Clarify: 每 + (量词) + 名词. With common time words, don’t add 个: 每天、每年、每月、每星期/每周；also fixed form 每人. Use 都 when the 每‑phrase is the subject meaning “each …” (每个学生都喜欢老师). With time/frequency phrases, 都 is optional: 我每天(都)跑步；我每个星期三(都)上中文课。

### `gr_xie_some` — 些 / 一些 / 这些 (some, plural)
- **common_mistake (current):** Adding a measure word after 些 (一些个) or a number before it.
- **would wrongly reject:** 我们在找一些个子高的学生。 (We’re looking for some tall students.)
- **fix:** Say: “Don’t put a classifier right after 些 when 些 directly modifies the noun (一些苹果, 这些人). But if 个 is part of the next word (e.g., 个人, 个子), that’s fine: 我有一些个人的想法; 我们在找一些个子高的学生.”

### `gr_money_spoken` — Spoken money (块 / 毛 / 分)
- **common_mistake (current):** Using written 元/角 in speech, or reversing the unit order.
- **would wrongly reject:** 我花了二十元。 — I spent 20 yuan.
- **fix:** Explanation: In casual speech, people usually say 块(=元), 毛(=角), 分, big unit first: 三块五, 十块二毛. 元 is also fine in speech (more neutral/formal), and 角 is less common than 毛.
Common mistake: Reversing the unit order (e.g., 这个五毛三块). In casual chat, prefer 块/毛, but 元 isn’t wrong.

### `gr_adj_predicate_hen` — Adjective predicate takes 很, not 是
- **common_mistake (current):** Using 是 before the adjective, or leaving a neutral statement with a bare adjective.
- **would wrongly reject:** 今天天气好。 (The weather is good today.)
- **fix:** Revise to: “For neutral statements with adjective predicates, we usually add 很 and not 是: 他很高. But bare adjectives are also correct in common patterns like topic–comment (今天天气好), change-of-state with 了 (我饿了/天气好了), and short answers (高). Don’t mark these as wrong; 很 just gives a neutral tone.”

### `gr_dou_all` — 都 (dōu) all/both — before the verb, scope to its left
- **common_mistake (current):** Placing 都 before the subject it quantifies, or after the verb.
- **would wrongly reject:** （A：你要茶还是咖啡？）B：都可以。  “Either is fine.”
- **fix:** Change to: “都 is placed before the predicate (verb/adj) and quantifies something already given (usually to its left in the sentence or understood from context). In full sentences use S + 都 + V: 我们都喜欢…; but in short answers or commands with an omitted subject, sentence-initial 都 is natural: 都可以。都别说话。” Update the mistake note to: “Don’t put 都 after the main predicate.”

### `gr_zai_you_again` — 再 vs 又 (again: future vs past)
- **common_mistake (current):** Swapping them — 再 for a completed repetition or 又 for a future one.
- **would wrongly reject:** 明天又要下雨了。 (It’s going to rain again tomorrow.)
- **fix:** Revise explanation: 再 = again for a planned/intended future action (often a request/suggestion): 再说一次。又 = again for something that has happened before and is happening now or is expected to happen again (often with 要/会/了): 他又迟到了；明天又要下雨了。 Update common mistake: Using 又 to make a request/plan is wrong (我们再见一次吧, not 我们又见一次吧), but using 又 with 要/会 for a predicted recurrence is correct.

### `gr_zhi_only` — 只 (zhǐ) only — before the verb
- **common_mistake (current):** Placing 只 after the verb, or using 就 for 'only'.
- **would wrongly reject:** 我就一个问题。 (I only have one question.)
- **fix:** Keep: “只放在动词前：我只有十块钱 / 他只喜欢你。不要把‘只’放在动词后。” Replace the ‘common mistake’ with: “注意：就也可以表示‘只有’，常见于数量/时间前或‘一个…’：我就一个问题 / 我就两块钱。这些用法是对的，本课只讲‘只’放在动词前。”

### `gr_tai_le` — 太……了 (too / so)
- **common_mistake (current):** Omitting 了 after 太, or replacing 太 with 很.
- **would wrongly reject:** 这个不太贵。 (This isn’t too expensive.)
- **fix:** Only require 了 when 太 + Adjective is a standalone exclamation/comment (e.g., 这个太贵了). Do not add 了 in 不太 + Adjective (这个不太贵) or when 太 + Adjective modifies a noun (太贵的手机). 很 is fine if you mean “very,” not “too.”

### `gr_verb_reduplication` — Verb reduplication (看看 / 休息休息)
- **common_mistake (current):** Reduplicating a two-syllable verb as AABB (休休息息).
- **would wrongly reject:** 我们聊聊天吧。 (Let's chat a bit.)
- **fix:** Clarify patterns: Monosyllabic verbs: AA / A一A (also A了A, e.g., 看了看). Two-syllable simple verbs: ABAB (休息休息). For verb–object verbs like 聊天/唱歌/跳舞, reduplicate the verb only: V V O (聊聊天、唱唱歌、跳跳舞). AABB isn’t used for verbs here (it’s common with adjectives like 高高兴兴).

### `gr_lai_qu_purpose` — 来/去 + verb phrase (come/go to do)
- **common_mistake (current):** Inserting 为了 / an English 'to' marker between the motion and the purpose verb.
- **would wrongly reject:** 我去商店是为了买东西。 (I'm going to the shop in order to buy things.)
- **fix:** Common mistake: Putting 为了 right after 来/去 in this pattern. Usually you don’t need any extra marker: 来/去 + (place) + VP → 我去商店买东西。 If you want to use 为了, put it before the whole clause (我为了买东西去商店) or use 是为了 after the motion clause (我去商店是为了买东西).

## Merely incomplete (not editing for a beginner tool — verify)

`gr_ye_also`, `gr_frequency_adverb`

## Caveats

- Still a judge's triage — confirm each to-do before editing `data/grammar_rules.json`, then re-seed the corpus so grounded replies pick up the fix.
- The `level-appropriate` cut is a judgement; a rule parked as 'incomplete' may still be worth a note if your learners are advanced.
