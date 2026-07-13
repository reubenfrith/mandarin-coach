"""Build evals/datagen/retrieval_queries.json — the Task 6 retrieval sweep test set.

WHY THIS EXISTS (methodology): the Task 5 A_stateless cases query grammar_rule_fetcher
with each rule's own `incorrect_example`, but `memory._grammar_text` embeds that exact
string inside the target document — so retrieval partly matches verbatim text, not
meaning. That is fine for Task 5 (it tests the retriever→grounding chain end to end),
but it is circular for a *retrieval-quality sweep*: it would flatter every embedding
and make lexical (BM25) matching look artificially strong.

These queries are instead FRESH erroneous sentences a learner might actually type —
new vocabulary and context, NOT copied from any rule's document — each mapped by
construction to the single grammar rule that best explains its error. The retrieval
target is which rule the query is *about* (a label we control by authoring the query
from that rule), so the deterministic recall@k / MRR machinery carries over unchanged
while now measuring genuine semantic retrieval.

Queries deliberately concentrate on the near-neighbour clusters added in the 24→98
corpus expansion (aspect particles, the 有/是/在 trio, 再/又, 只要/只有, complements,
comparison, degree adverbs) — the only place different embeddings / techniques can
actually diverge.

Run:  uv run python evals/datagen/build_retrieval_queries.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "grammar_rules.json"
OUT = Path(__file__).resolve().parent / "retrieval_queries.json"

# (query, expected_rule_id, cluster, note). query = a fresh learner error, NOT any
# rule's incorrect_example. note records why this rule is the intended gold.
QUERIES = [
    # ---- aspect / sentence-final particles ----
    ("小时候我常常去了公园。", "gr_le_completion", "aspect", "了 wrongly attached to a habitual action"),
    ("你看，外面下雪，我们别出去了。", "gr_le_change", "aspect", "missing change-of-state 了 on 下雪(了)"),
    ("昨天我没去上班了。", "gr_le_negation_drop", "aspect", "没 + verb should drop the 了"),
    ("他站看电视。", "gr_zhe_durative", "aspect", "missing durative 着 on the accompanying posture"),
    ("电影就要开始。", "gr_yao_le_imminent", "aspect", "就要 imminent needs a final 了"),
    ("你什么时候来吗？", "gr_ma_question", "questions", "吗 added to a question that already has a question word"),
    ("你去不去图书馆吗？", "gr_a_not_a", "questions", "A-not-A question wrongly combined with 吗"),
    ("时间不早了，我们回家吗。", "gr_ba_suggestion", "questions", "a suggestion needs 吧, not 吗"),
    ("这件衣服太贵。", "gr_tai_le", "degree", "太 + adjective needs the framing 了"),
    ("我喜欢喝咖啡，你吗？", "gr_ne_question", "questions", "follow-up 'what about you' needs 呢, not 吗"),
    # ---- modals ----
    ("我姐姐能弹钢琴。", "gr_hui_neng_keyi", "modals", "能 used for a learned skill where 会 is correct"),
    ("你感冒了，多喝热水休息。", "gr_yinggai_should", "modals", "advice/obligation missing 应该"),
    # ---- comparison ----
    ("弟弟比哥哥非常高。", "gr_bi_comparison", "comparison", "非常 wrongly used with a 比 comparison"),
    ("我不比我妹妹高。", "gr_meiyou_comparison", "comparison", "不比 used for 'not as ... as' (should be 没有)"),
    ("妹妹跟姐姐高。", "gr_gen_yiyang", "comparison", "跟 comparison missing 一样"),
    ("天气更来更热。", "gr_yuelaiyue", "comparison", "calque of 'more and more' instead of 越来越"),
    ("这个箱子比那个一点儿重。", "gr_bi_degree_diff", "comparison", "amount of difference placed before the adjective"),
    # ---- conjunctions / complex sentences ----
    ("如果明天不下雨，我们去爬山。", "gr_ruguo_jiu", "conjunction", "如果 condition missing the paired 就"),
    ("只要有时间，我才会帮你。", "gr_zhiyao_jiu", "conjunction", "只要 wrongly paired with 才 (should be 就)"),
    ("只有努力学习，就能考上大学。", "gr_zhiyou_cai", "conjunction", "只有 wrongly paired with 就 (should be 才)"),
    ("我一到北京，然后给你发消息。", "gr_yi_jiu", "conjunction", "一…… should pair with 就, not 然后"),
    ("这家餐厅的菜不但便宜，好吃。", "gr_budan_erqie", "conjunction", "不但 missing the paired 而且/也"),
    ("虽然这个工作很难，我很喜欢。", "gr_suiran_danshi", "conjunction", "虽然 missing the paired 但是"),
    ("这不是我的错，但是你的错。", "gr_bushi_ershi", "conjunction", "correction needs 而是, not 但是"),
    ("当我小，我住在乡下。", "gr_deshihou", "conjunction", "time clause missing the closing 的时候"),
    # ---- complements ----
    ("字太小了，我不看清楚。", "gr_potential_complement", "complement", "should be the infixed potential 看不清楚"),
    ("我找了半天，还是没找我的护照。", "gr_dao_resultative", "complement", "attainment 到 missing (没找到)"),
    ("你说得太小声，我没听。", "gr_jian_perception", "complement", "perception result 见 missing (没听见)"),
    ("行李还没收拾，我们不能出发。", "gr_hao_completion", "complement", "'ready/done' resultative 好 missing (收拾好)"),
    ("小狗跑出去了房间。", "gr_directional", "complement", "directional 来/去 and place object in wrong order"),
    # ---- coverbs / prepositions ----
    ("我每天晚上打电话我妈妈。", "gr_gei_coverb", "coverb", "recipient needs the coverb 给 before the verb"),
    ("我昨天去看电影和我的同学。", "gr_gen_he_with", "coverb", "'with ...' placed after the verb, English order"),
    ("中国人常常吃饭筷子。", "gr_yong_instrument", "coverb", "instrument needs 用 before the verb"),
    ("我家从地铁站不远。", "gr_li_distance", "coverb", "static distance uses 离, not 从"),
    ("银行早上九点下午五点营业。", "gr_cong_dao", "coverb", "time span needs 从……到"),
    # ---- existential / 有 / 是 / 在 trio ----
    ("桌子上是一台电脑。", "gr_you_existential", "existential", "introducing existence needs 有, not 是"),
    ("我的钥匙有你那里吗？", "gr_zai_location", "existential", "location of a specific thing needs 在, not 有"),
    ("这个问题是很难。", "gr_shi_identity", "existential", "是 wrongly placed before an adjective"),
    ("今天的天气好。", "gr_adj_predicate_hen", "degree", "bare adjective predicate needs 很"),
    # ---- adverb placement ----
    ("我弟弟喜欢打篮球也。", "gr_ye_also", "adverb", "也 wrongly placed at the end"),
    ("都我的同事很友好。", "gr_dou_all", "adverb", "都 placed before the subject it quantifies"),
    ("他上个星期再来了一次。", "gr_zai_you_again", "adverb", "past repetition needs 又, not 再"),
    ("我有只五块钱。", "gr_zhi_only", "adverb", "只 placed after the verb instead of before"),
]


def main():
    corpus_ids = {r["id"] for r in json.loads(CORPUS.read_text(encoding="utf-8"))}
    rows, seen_q = [], set()
    for i, (q, rid, cluster, note) in enumerate(QUERIES, 1):
        assert rid in corpus_ids, f"R{i:02d}: unknown rule id {rid!r}"
        assert q not in seen_q, f"duplicate query: {q!r}"
        seen_q.add(q)
        rows.append({"id": f"R{i:02d}", "query": q, "expected_rule_id": rid,
                     "cluster": cluster, "note": note})
    clusters = {}
    for r in rows:
        clusters[r["cluster"]] = clusters.get(r["cluster"], 0) + 1
    out = {"meta": {"description": "Task 6 retrieval sweep — fresh non-circular queries, "
                    "each mapped to the grammar rule that best explains its error.",
                    "count": len(rows), "by_cluster": clusters},
           "queries": rows}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}: {len(rows)} queries across {len(clusters)} clusters")
    print(f"  {clusters}")


if __name__ == "__main__":
    main()
