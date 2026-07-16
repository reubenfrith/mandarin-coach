# Task 6.2 — Grammar coverage check

After unioning the 217-point Chinese Grammar Wiki `grammar_patterns` collection into `grammar_rule_fetcher`. Deterministic exact rule-id match over the production union retriever.

## Part A — Coverage (15 CGW-only topics, no curated twin)
- Union recall@1 = **0.60**, recall@3 = **0.87**
- Curated-only recall = **0/15** — these ids are not in `grammar_rules`, so the pre-ingest app could not surface these topics at all. This is the coverage the +217 adds.

## Part B — Precision retention (43 curated sweep queries, curated gold)
- Union recall@3 of the curated gold = **0.744** vs frozen curated-only sweep **0.767** — essentially unchanged.
- Curated gold left top-3 on 11 query(ies); **10 were already misses on the curated-only sweep**, so only **1 is a NEW drop caused by adding the CGW set** (R38). Adding 217 rules moved almost nothing — coverage did not cost precision.

| query id | curated gold | union top-3 |
|---|---|---|
| R01 | gr_le_completion | gr_frequency_adverb, gr_wulun_dou, gr_ye_also |
| R02 | gr_le_change | gr_chule_yiwai, gr_ba_suggestion, gr_yixia |
| R12 | gr_yinggai_should | gr_verb_reduplication, cgw_zuihao, cgw_haiyou |
| R15 | gr_gen_yiyang | cgw_expressingAgeDifferenceWithDaAndXiao, gr_bi_degree_diff, gr_bi_comparison |
| R28 | gr_jian_perception | cgw_leYidianr, gr_tai_le, gr_potential_complement |
| R29 | gr_hao_completion | gr_chule_yiwai, gr_le_negation_drop, cgw_meiBanfa |
| R30 | gr_directional | gr_yao_le_imminent, gr_le_change, gr_le_negation_drop |
| R37 | gr_zai_location | gr_dao_resultative, gr_ma_question, gr_ne_question |
| R38 | gr_shi_identity | cgw_expressingDifficultWithNan, gr_adj_predicate_hen, gr_tai_le |
| R39 | gr_adj_predicate_hen | gr_wulun_dou, gr_hao_completion, gr_yuelaiyue |
| R41 | gr_dou_all | gr_gen_yiyang, gr_bi_comparison, gr_chule_yiwai |
