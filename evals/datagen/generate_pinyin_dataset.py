"""Generate the labeled pīnyīn-accuracy dataset → datagen/pinyin_dataset.json.

WHAT THIS EVALUATES.  The learner-facing ruby (`汉字` with pīnyīn underneath) and the
`/api/pinyin` string both come from `tools.pinyin_segments` / `tools._tone_pinyin`, which
call pypinyin with `Style.TONE` — i.e. CITATION tones. Wrong pīnyīn printed under a hanzi
teaches a wrong pronunciation, so this surface asks: *is the displayed tone the one the
learner should say?*

THE FINDING THIS DATASET IS BUILT TO EXPOSE — and its gold discipline.  pypinyin's tone
output is a lexicalised lookup, not a rule engine, so it is INTERNALLY INCONSISTENT on the
exact same phenomenon: 不是→bú but 不去→bù; 一个→yí but 一样→yī; 听得懂→de but 看得见→dé.
That inconsistency is a defect under ANY convention and needs no philosophical defense — it
is the headline. The buckets separate what's unassailable from what's a defensible product
choice, so the eval never overclaims:

  * yi_bu_sandhi   — 一/不 tone sandhi. Gold = the standard sandhi form. The metric is
                     CONSISTENCY: within one sub-rule (e.g. 不+T4→bú) pypinyin applies it to
                     some words and not others. Wrong under citation OR spoken convention.
  * neutral_particle — grammatical 地 (adverbial) and 得 (V得C complement). Their reading in
                     that role is the neutral syllable `de`; pypinyin prints `dì`/`dé`.
                     Unassailably wrong (it's not sandhi — it's the wrong lexical reading).
  * t3_bisyllabic  — uncontested T3+T3→T2+T3 (你好→ní hǎo). pypinyin shows citation (nǐ hǎo).
                     This is a COVERAGE GAP under the spoken-tone product choice, NOT a
                     defect: dictionaries mark citation tones, so the harm is weak and the
                     eval surfaces citation-vs-spoken to the reader as a decision.
  * t3_multi       — 3+ stacked T3 (我很好). Realisation is prosody/grouping-dependent and
                     genuinely contested → carried but NOT scored (measuring it would measure
                     our opinion). The analog of the tone surface's "borderline, reported not
                     graded" honesty.
  * redup          — reduplication (谢谢→xièxie). SECONDARY: some dictionaries keep the full
                     tone, so it's a soft gold — reported, not headlined.
  * control        — 银行/长江/目的/觉得: lexical polyphones pypinyin gets RIGHT. The sanity
                     floor — if these fail the eval is broken, not pypinyin. (`目的`→mù dì and
                     `觉得`→jué de prove the test isn't rigged against `的`/`得`.)
  * erhua          — 花儿→huār CANNOT be expressed in pinyin_segments' one-pinyin-per-hanzi
                     contract. A structural ruby-model limitation, NOT a pypinyin miss →
                     carried, excluded from scoring, noted in the report.

Gold is authored from ground-truth probes of the real functions (not from memory). Run the
datagen, then eyeball the gold-vs-pypinyin diff it prints: for scored buckets the two must
differ ONLY on the syllable the rule targets — that's the typo guard.

Run:  uv run python evals/datagen/generate_pinyin_dataset.py
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "app"))
from pypinyin import Style, pinyin as _p  # noqa: E402
from tools import _tone_pinyin  # noqa: E402  — probe the real function for the diff guard

OUT = pathlib.Path(__file__).resolve().parent / "pinyin_dataset.json"


def _follower_tone(word: str) -> int:
    """Citation tone (1-5) of the 2nd character — pypinyin's own reading, so it's
    self-consistent with the data. 一/不 sandhi is a pure function of this."""
    p = _p(word[1], style=Style.TONE3, neutral_tone_with_five=True)[0][0]
    m = re.search(r"([1-5])", p)
    return int(m.group(1)) if m else 0


def _c(text, gold, bucket, sub_rule, harm, scored, note):
    return {"text": text, "gold": gold, "bucket": bucket, "sub_rule": sub_rule,
            "harm": harm, "scored": scored, "note": note}


def build() -> dict:
    cases: list[dict] = []

    # ------------------------------------------------------------ 一 / 不 tone sandhi
    # Gold = the standard sandhi form. Some pypinyin already applies (→ pass), most it
    # misses (→ fail); the SPREAD within each sub-rule is the inconsistency finding.
    # 不 + 4th tone → bú
    bu_T4 = {"不是": "bú shì", "不对": "bú duì", "不去": "bú qù", "不错": "bú cuò",
             "不用": "bú yòng", "不要": "bú yào", "不会": "bú huì", "不但": "bú dàn",
             "不再": "bú zài", "不像": "bú xiàng", "不到": "bú dào", "不算": "bú suàn",
             "不必": "bú bì", "不够": "bú gòu"}
    # 不 + 1/2/3 tone → bù (NO sandhi). pypinyin is right here → a fairness control that
    # shows the citation default is correct exactly when no sandhi applies.
    bu_T123 = {"不吃": "bù chī", "不来": "bù lái", "不好": "bù hǎo", "不行": "bù xíng",
               "不能": "bù néng", "不多": "bù duō", "不少": "bù shǎo", "不难": "bù nán"}
    # 一 + 4th tone → yí
    yi_T4 = {"一个": "yí gè", "一样": "yí yàng", "一件": "yí jiàn", "一定": "yí dìng",
             "一下": "yí xià", "一次": "yí cì", "一半": "yí bàn", "一块": "yí kuài",
             "一位": "yí wèi", "一句": "yí jù", "一遍": "yí biàn", "一部": "yí bù"}
    # 一 + 1/2/3 tone → yì
    yi_T123 = {"一起": "yì qǐ", "一点": "yì diǎn", "一天": "yì tiān", "一年": "yì nián",
               "一些": "yì xiē", "一直": "yì zhí", "一般": "yì bān", "一边": "yì biān",
               "一杯": "yì bēi", "一条": "yì tiáo"}
    for sub, group, note in [
        ("bu_T4", bu_T4, "不 before a 4th tone → bú (2nd tone)"),
        ("bu_T123", bu_T123, "不 before 1/2/3 tone → bù (no sandhi; pypinyin correct)"),
        ("yi_T4", yi_T4, "一 before a 4th tone → yí (2nd tone)"),
        ("yi_T123", yi_T123, "一 before 1/2/3 tone → yì (4th tone)"),
    ]:
        for text, gold in group.items():
            cases.append(_c(text, gold, "yi_bu_sandhi", sub, "real", True, note))

    # ---------------------------------------------------- grammatical neutral particles
    # 地 as an adverbial marker and 得 as a V得C complement marker are read `de` (neutral).
    # This is the wrong LEXICAL reading, not sandhi → unassailably wrong.
    di_adv = {"高兴地": "gāo xìng de", "慢慢地": "màn màn de", "认真地": "rèn zhēn de",
              "开心地": "kāi xīn de", "轻轻地": "qīng qīng de"}
    de_comp = {"看得见": "kàn de jiàn", "跑得快": "pǎo de kuài", "说得好": "shuō de hǎo",
               "走得慢": "zǒu de màn", "听得懂": "tīng de dǒng"}
    for text, gold in di_adv.items():
        cases.append(_c(text, gold, "neutral_particle", "di_adverbial", "real", True,
                        "adverbial 地 → de (neutral); pypinyin prints dì"))
    for text, gold in de_comp.items():
        cases.append(_c(text, gold, "neutral_particle", "de_complement", "real", True,
                        "V得C complement 得 → de (neutral); pypinyin prints dé"))

    # -------------------------------------------------- third-tone sandhi (bisyllabic)
    # Gold = spoken T2+T3. COVERAGE GAP under the spoken-tone choice, not a defect
    # (citation is a defensible dictionary convention). harm=weak.
    t3 = {"你好": "ní hǎo", "很好": "hén hǎo", "老虎": "láo hǔ", "小狗": "xiáo gǒu",
          "所以": "suó yǐ", "可以": "ké yǐ", "好久": "háo jiǔ", "手表": "shóu biǎo",
          "洗澡": "xí zǎo", "美好": "méi hǎo", "领导": "líng dǎo", "勇敢": "yóng gǎn",
          "雨水": "yú shuǐ", "许可": "xú kě", "土匪": "tú fěi", "摆手": "bái shǒu",
          "岛屿": "dáo yǔ", "水果": "shuí guǒ"}
    for text, gold in t3.items():
        cases.append(_c(text, gold, "t3_bisyllabic", "t3_t3", "weak", True,
                        "T3+T3 → T2+T3 in speech; pypinyin shows citation (defensible)"))

    # 3+ stacked T3 — realisation is prosody/grouping-dependent → carried, NOT scored.
    for text in ("我很好", "买手表", "请你给我", "很勇敢"):
        cases.append(_c(text, None, "t3_multi", "t3_stack", "weak", False,
                        "3+ T3 in a row; realisation is contested → reported, not graded"))

    # ---------------------------------------------------------- reduplication (secondary)
    # Gold = neutral 2nd syllable, but some dicts keep full tone → soft. harm=weak.
    redup = {"谢谢": "xiè xie", "妈妈": "mā ma", "看看": "kàn kan", "试试": "shì shi",
             "想想": "xiǎng xiang", "爸爸": "bà ba", "哥哥": "gē ge", "弟弟": "dì di",
             "星星": "xīng xing"}
    for text, gold in redup.items():
        cases.append(_c(text, gold, "redup", "redup", "weak", True,
                        "reduplicated 2nd syllable → neutral (soft: some dicts keep tone)"))

    # ------------------------------------------------------------------ control (floor)
    # Lexical polyphones pypinyin gets RIGHT — gold == pypinyin output. Must score 100%.
    control = {"银行": "yín háng", "长江": "cháng jiāng", "校长": "xiào zhǎng",
               "重要": "zhòng yào", "重复": "chóng fù", "不行": "bù xíng", "目的": "mù dì",
               "得到": "dé dào", "地方": "dì fāng", "地图": "dì tú", "的确": "dí què",
               "觉得": "jué de"}
    for text, gold in control.items():
        cases.append(_c(text, gold, "control", "polyphone", "n/a", True,
                        "lexical polyphone pypinyin resolves correctly — sanity floor"))

    # ---------------------------------------------------------------- erhua (excluded)
    # 花儿→huār is one spoken syllable; pinyin_segments is one-pinyin-per-hanzi, so it
    # CANNOT express erhua. A ruby-model limitation, not a pypinyin miss → not scored.
    for text in ("花儿", "玩儿", "一点儿", "这儿", "那儿"):
        cases.append(_c(text, None, "erhua", "erhua", "n/a", False,
                        "儿化 collapses two hanzi into one spoken syllable; unexpressible "
                        "in per-hanzi ruby → structural exclusion, not a miss"))

    return {
        "meta": {
            "description": "Labeled pīnyīn for the ruby/`/api/pinyin` accuracy surface.",
            "surface": "tools.pinyin_segments / tools._tone_pinyin (pypinyin Style.TONE)",
            "gold_semantics": {
                "yi_bu_sandhi": "standard 一/不 sandhi form; metric is CONSISTENCY (defect)",
                "neutral_particle": "地/得 grammatical particle → de; wrong lexical reading (defect)",
                "t3_bisyllabic": "spoken T2+T3; COVERAGE GAP under spoken choice, not a defect (weak harm)",
                "t3_multi": "3+ T3 contested → carried, unscored",
                "redup": "neutral 2nd syllable; SOFT gold (secondary)",
                "control": "gold == pypinyin; sanity floor, must be ~100%",
                "erhua": "unexpressible in per-hanzi ruby → excluded",
            },
        },
        "cases": cases,
    }


def main():
    data = build()
    cases = data["cases"]

    # Linguistic guard (not just a typo check): 一/不 sandhi is a pure function of the
    # FOLLOWING syllable's citation tone, so verify every case sits in the right bucket —
    # *_T4 must be followed by a 4th tone, *_T123 by a 1st/2nd/3rd. This catches a word
    # dropped in the wrong tone-bucket (e.g. 不同, 同=tóng/T2 → no sandhi), which the
    # gold-vs-pypinyin diff below CANNOT see (that only checks mechanical consistency).
    for c in cases:
        if c["bucket"] != "yi_bu_sandhi":
            continue
        t = _follower_tone(c["text"])
        want4 = c["sub_rule"] in ("bu_T4", "yi_T4")
        ok = (t == 4) if want4 else (t in (1, 2, 3))
        assert ok, (f"{c['text']} in {c['sub_rule']} but follower tone is {t} "
                    f"({'expected T4' if want4 else 'expected T1/2/3'}) — miscategorized")

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # Typo guard: for every SCORED case, show gold vs the real pypinyin output. For a
    # correctly-authored case the two differ ONLY on the rule's target syllable (or not at
    # all, for an already-applied / control case). Eyeball this table after generating.
    print("scored buckets — gold vs pypinyin (differences are the finding; verify only the "
          "target syllable differs):\n")
    for b in ("yi_bu_sandhi", "neutral_particle", "t3_bisyllabic", "redup", "control"):
        rows = [c for c in cases if c["bucket"] == b and c["scored"]]
        n_diff = sum(1 for c in rows if c["gold"] != _tone_pinyin(c["text"]))
        print(f"=== {b}  ({len(rows)} cases, {n_diff} differ from pypinyin)")
        for c in rows:
            got = _tone_pinyin(c["text"])
            mark = "  ✓ match" if got == c["gold"] else f"  ✗ pypinyin={got!r}"
            print(f"   {c['text']:6s} gold={c['gold']:14s}{mark}")
        print()
    for b in ("t3_multi", "erhua"):
        rows = [c for c in cases if c["bucket"] == b]
        print(f"=== {b}  ({len(rows)} cases, UNSCORED): {[c['text'] for c in rows]}")
    print(f"\n  total: {len(cases)} cases "
          f"({sum(1 for c in cases if c['scored'])} scored)  → wrote {OUT}")


if __name__ == "__main__":
    main()
