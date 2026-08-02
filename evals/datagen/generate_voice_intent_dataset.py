"""Voice-router intent dataset → datagen/voice_intent_dataset.json (Task 4, voice-coach plan Phase 4).

Hand-authored, DETERMINISTIC (no LLM). The whole point of this surface is to grade an LLM
classifier + a script heuristic against ground truth, so the labels must be human-owned —
LLM-generating the labels would make the eval circular (grade the classifier against its own
kind of judgement) and re-create the retrieval-saturation trap this repo already hit once.

Each case is a single spoken turn the way `_route_intent` sees it (transcript text only — the
router classifies on the text alone, no history), tagged:

  - `gold_intent`  the TRUE intent: 'coach' (a question / explanation request / a
                   code-switch that wants a word taught) or 'converse' (ordinary chat).
  - `bucket`       the SCRIPT the heuristic sees, which decides the CODE PATH:
                     mandarin — Han only            → heuristic routes converse (no LLM)
                     english  — Latin only          → heuristic routes coach    (no LLM)
                     empty    — neither             → heuristic routes converse (no LLM)
                     mixed    — Han AND Latin        → the LLM classifier decides
  - `note`         (optional) why a case is adversarial or borderline.

The design bias is precision-first toward CONVERSE: misrouting chat→coach (an English lecture
when the learner wanted to talk) is the JARRING failure; coach→converse degrades gracefully
because the partner still does light inline correction.

CRUCIALLY, the pure buckets are NOT labelled to agree with the heuristic. Bucketing by script
and labelling by true intent means each pure bucket carries heuristic-ADVERSARIAL cases:

  - english-but-converse ("and you?", "yeah exactly") — the heuristic force-routes these to
    coach WITHOUT ever calling the classifier. This is the jarring failure, produced by the
    heuristic itself, and it is the case the English→coach bet actually costs against.
  - mandarin-but-coach ("这个词是什么意思？") — a coaching question the heuristic sends
    straight to converse (a graceful miss).

Without these, the pure buckets would score 100% by construction and only `mixed` would test
anything. With them, coach-precision and per-bucket accuracy become real numbers that measure
the heuristic's error and the classifier's error SEPARATELY (the surface reports per bucket).

Proportions are kept realistic — a lower-intermediate learner in a spoken session mostly talks
in Mandarin, occasionally asks a meta-question in English, sometimes code-switches — so the
headline reflects reality, not a stress test.

Run:  uv run python evals/datagen/generate_voice_intent_dataset.py
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent / "voice_intent_dataset.json"


# --------------------------------------------------------------------------- #
# mandarin bucket — Han only. Heuristic routes ALL of these to converse with no
# classifier call. The `coach` golds here are therefore GRACEFUL MISSES the
# heuristic cannot catch (they measure the cost of the Mandarin→converse rule).
# --------------------------------------------------------------------------- #
MANDARIN = [
    ("m01", "我昨天去了公园散步。", "converse", None),
    ("m02", "我觉得这个周末天气很好。", "converse", None),
    ("m03", "我最喜欢的菜是麻婆豆腐。", "converse", None),
    ("m04", "你呢？你周末做了什么？", "converse", "question aimed at the chat partner, not a learning question"),
    ("m05", "我们下次聊什么好呢？", "converse", None),
    ("m06", "对，我也这么觉得。", "converse", None),
    ("m07", "我早上喝了一杯咖啡。", "converse", None),
    ("m08", "昨天的电影真的很好看。", "converse", None),
    ("m09", "我想多练习一点口语。", "converse", None),
    ("m10", "我家有一只很可爱的猫。", "converse", None),
    # heuristic-adversarial: coaching questions in Mandarin → heuristic wrongly routes converse (FN)
    ("m11", "这个词是什么意思？", "coach", "mandarin-but-coach: asks a word's meaning; heuristic sends it to converse"),
    ("m12", "这样说对吗？", "coach", "mandarin-but-coach: is this correct?"),
    ("m13", "刚才那个句子为什么不对？", "coach", "mandarin-but-coach: why was that wrong?"),
    ("m14", "“把”和“被”有什么区别？", "coach", "mandarin-but-coach: grammar contrast question (quotes are full-width Han)"),
    ("m15", "再给我一个例子好吗？", "coach", "mandarin-but-coach: give me another example"),
]

# --------------------------------------------------------------------------- #
# english bucket — Latin only. Heuristic routes ALL to coach with no classifier
# call. The `converse` golds here are the JARRING FALSE POSITIVES: conversational
# English glue force-routed to an English lecture. These are the money cases.
# --------------------------------------------------------------------------- #
ENGLISH = [
    ("e01", "Why was that sentence wrong?", "coach", None),
    ("e02", "What does that word mean?", "coach", None),
    ("e03", "Can you explain the grammar there?", "coach", None),
    ("e04", "How do I say I miss you in Chinese?", "coach", None),
    ("e05", "Give me another example please.", "coach", None),
    ("e06", "What's the difference between those two words?", "coach", None),
    ("e07", "Was my tone correct on that?", "coach", None),
    # heuristic-adversarial: English conversational glue → heuristic wrongly routes coach (FP, jarring)
    ("e08", "And you?", "converse", "english-but-converse: the classifier prompt itself lists this as converse; heuristic force-routes it to coach"),
    ("e09", "Yeah, exactly.", "converse", "english-but-converse: agreement, not a question"),
    ("e10", "Haha okay.", "converse", "english-but-converse: filler"),
    ("e11", "One sec.", "converse", "english-but-converse: aside"),
    ("e12", "Me too!", "converse", "english-but-converse: agreement"),
]

# --------------------------------------------------------------------------- #
# empty bucket — neither script. Heuristic routes to converse (no real content →
# don't lecture). Trivially converse; included to cover the branch.
# --------------------------------------------------------------------------- #
EMPTY = [
    ("z01", "。。。", "converse", "no content"),
    ("z02", "？？？", "converse", "no content"),
    ("z03", "……", "converse", "no content"),
]

# --------------------------------------------------------------------------- #
# mixed bucket — Han AND Latin. THIS is what exercises the LLM classifier. Split
# between clear code-switch/quoted-Chinese coach turns and borderline proper-noun
# converse turns that test whether the English→coach instinct over-triggers.
# --------------------------------------------------------------------------- #
MIXED = [
    # code-switch: an English content word dropped in because they don't know it in Chinese → coach
    ("x01", "我想 book 一张机票。", "coach", "code-switch content word (book = 预订)"),
    ("x02", "这个 refund 怎么申请？", "coach", "code-switch content word (refund = 退款)"),
    ("x03", "他这个人很 stubborn。", "coach", "code-switch adjective (stubborn = 固执)"),
    # English meta-question quoting the Chinese it asks about → coach
    ("x04", "Why did you use 把 here?", "coach", "English question about a Chinese construction"),
    ("x05", "What does 差不多 mean?", "coach", "English question about a Chinese word"),
    ("x06", "What's the difference between 还 and 又?", "coach", "English grammar-contrast question"),
    # borderline: a proper noun kept in English inside ordinary conversation → converse (tests over-trigger)
    ("x07", "我朋友叫 David。", "converse", "proper name, not a vocabulary gap"),
    ("x08", "我周末想去 Melbourne 玩。", "converse", "borderline: place name in a conversational turn"),
    ("x09", "我在追一部 Netflix 的剧。", "converse", "borderline: brand name in a conversational turn"),
    ("x10", "我们约在 Starbucks 见面吧。", "converse", "borderline: brand name in a conversational turn"),
]


def build() -> dict:
    cases = []
    for bucket, group in (("mandarin", MANDARIN), ("english", ENGLISH), ("empty", EMPTY), ("mixed", MIXED)):
        for cid, text, gold, note in group:
            row = {"id": cid, "text": text, "gold_intent": gold, "bucket": bucket}
            if note:
                row["note"] = note
            cases.append(row)
    n_coach = sum(1 for c in cases if c["gold_intent"] == "coach")
    n_converse = len(cases) - n_coach
    by_bucket = {}
    for c in cases:
        by_bucket.setdefault(c["bucket"], {"coach": 0, "converse": 0})
        by_bucket[c["bucket"]][c["gold_intent"]] += 1
    return {
        "meta": {
            "n": len(cases),
            "n_coach": n_coach,
            "n_converse": n_converse,
            "by_bucket": by_bucket,
            "positive_class": "coach",
            "note": (
                "Bucket = script the heuristic sees (decides the code path); gold_intent = true "
                "intent. Pure buckets carry heuristic-adversarial cases on purpose. Only the "
                "`mixed` bucket calls the LLM classifier; mandarin/english/empty are resolved by "
                "the zero-latency heuristic."
            ),
        },
        "cases": cases,
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    m = data["meta"]
    print(f"Wrote {OUT} — {m['n']} cases ({m['n_coach']} coach / {m['n_converse']} converse)")
    for b, counts in m["by_bucket"].items():
        print(f"  {b:9s}: {counts['coach']} coach, {counts['converse']} converse")
