"""Realistic per-category error examples + a Type C corpus builder.

The Type C corpus is deliberately shaped so the correct answer requires genuine
cross-record computation, not eyeballing: 60 mixed-category records where one
category (particle) is clearly *increasing* in the recent half, one (tones) is
clearly *decreasing*, and the rest are steady. A model that just skims will get
the totals or the trend directions wrong; the deterministic error_stats() gets
them exactly right. Shared by the preflight slice and the full harness.
"""
from __future__ import annotations

# Pools of genuine (erroneous -> corrected) pairs per category. Cycled to fill
# the corpus; content realism matters less than the category tallies for the
# aggregation test, but these are all plausible lower-intermediate mistakes.
EXAMPLES: dict[str, list[tuple[str, str]]] = {
    "particle": [
        ("我把门关", "我把门关上了"),
        ("他跑很快", "他跑得很快"),
        ("我高兴的笑了", "我高兴地笑了"),
        ("我把作业做", "我把作业做完了"),
    ],
    "tones": [
        ("我要卖一本书（想买）", "我要买一本书"),
        ("他是我的老师（说成 lǎoshī→lāoshī）", "他是我的老师"),
        ("我problem说不清楚声调 mā/má", "我妈妈很忙"),
        ("请wèn一下（读成 wén）", "请问一下"),
    ],
    "measure_word": [
        ("三个书", "三本书"),
        ("一个茶", "一杯茶"),
        ("两个车", "两辆车"),
        ("五个纸", "五张纸"),
    ],
    "word_order": [
        ("我去商店买东西每天", "我每天去商店买东西"),
        ("我很喜欢非常这个", "我非常喜欢这个"),
        ("他昨天不去了学校", "他昨天没去学校"),
        ("我吃饭在食堂", "我在食堂吃饭"),
    ],
    "vocabulary": [
        ("我知道他很久了（应为认识）", "我认识他很久了"),
        ("我们做朋友吧（应为交）", "我们交朋友吧"),
        ("我要开我的电脑（应为打开）", "我要打开我的电脑"),
        ("我看医生（应为看病）", "我去看病"),
    ],
}

EXPLANATIONS = {
    "particle": "Particle/complement misuse (把 / 得 / 地).",
    "tones": "Tone or pinyin confusion between similar syllables.",
    "measure_word": "Wrong measure word for the noun.",
    "word_order": "Adverbial/time phrase in the wrong position.",
    "vocabulary": "Wrong word choice for the intended meaning.",
}


def _pick(category: str, i: int) -> tuple[str, str]:
    pool = EXAMPLES[category]
    return pool[i % len(pool)]


def build_typec_corpus() -> list[dict]:
    """60 records with a designed trend. Returns records ordered oldest->newest,
    each carrying `days_ago` so the caller can stamp real timestamps.

    Ground-truth by_category totals: particle 15, tones 14, measure_word 12,
    word_order 10, vocabulary 9.  Trend (recent half vs earlier half):
    particle increasing, tones decreasing, vocabulary decreasing, the rest steady.
    """
    # (category, earlier_count, recent_count) — earlier = older half, recent = newer half
    plan = [
        ("particle", 3, 12),
        ("tones", 11, 3),
        ("measure_word", 6, 6),
        ("word_order", 5, 5),
        ("vocabulary", 5, 4),
    ]
    earlier: list[str] = []
    recent: list[str] = []
    for cat, e, r in plan:
        earlier += [cat] * e
        recent += [cat] * r
    assert len(earlier) == 30 and len(recent) == 30, (len(earlier), len(recent))

    # Interleave categories within each half so the corpus looks organically mixed
    # rather than blocked by category (a blocked corpus would be trivially countable).
    earlier = _interleave(earlier)
    recent = _interleave(recent)

    records: list[dict] = []
    counters: dict[str, int] = {}
    # Oldest first: earlier half spans days_ago 60..31, recent half 30..1.
    ordered = [(cat, 60 - idx) for idx, cat in enumerate(earlier)]
    ordered += [(cat, 30 - idx) for idx, cat in enumerate(recent)]
    for cat, days_ago in ordered:
        i = counters.get(cat, 0)
        counters[cat] = i + 1
        original, correction = _pick(cat, i)
        records.append(
            {
                "category": cat,
                "original": original,
                "correction": correction,
                "explanation": EXPLANATIONS[cat],
                "days_ago": days_ago,
            }
        )
    return records


def _interleave(items: list[str]) -> list[str]:
    """Spread categories evenly (round-robin by category) for an organic mix."""
    from collections import defaultdict, deque

    buckets: dict[str, deque] = defaultdict(deque)
    for it in items:
        buckets[it].append(it)
    out: list[str] = []
    while any(buckets.values()):
        for cat in list(buckets):
            if buckets[cat]:
                out.append(buckets[cat].popleft())
    return out


# Expected ground truth for assertions / reporting.
TYPEC_EXPECTED = {
    "total": 60,
    "by_category": {"particle": 15, "tones": 14, "measure_word": 12, "word_order": 10, "vocabulary": 9},
    "trend": {
        "particle": "increasing",
        "tones": "decreasing",
        "measure_word": "steady",
        "word_order": "steady",
        "vocabulary": "decreasing",
    },
}
