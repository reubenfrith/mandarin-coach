"""Deterministic checks for the 不 tone-sandhi post-pass in app/tools.py.

`_tone_pinyin` / `pinyin_segments` render the learner-facing ruby. pypinyin `Style.TONE`
gives citation tones and applies 不-sandhi only inconsistently (不是→bú but 不去→bù); the
post-pass (`_apply_bu_sandhi`) makes 不 → bú before a 4th tone uniform. These checks pin:

  1. the fix fires on 不 + 4th tone,
  2. it stays off where it must (不 + 1/2/3; 一; grammatical/lexical 地/得; V不C complements),
  3. the two surfaces agree (ruby marks == /api/pinyin marks).

The full quantified before/after + regression guard lives in the pinyin_accuracy eval; this
is the fast unit-level guard so a pypinyin bump or a refactor can't silently break it.

Run:  uv run python tests/test_pinyin_sandhi.py   (exit 0 = all passed)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools import _tone_pinyin, pinyin_segments  # noqa: E402


def _seg(text):
    return " ".join(s["pinyin"] for s in pinyin_segments(text) if "pinyin" in s)


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


def main():
    # 1. 不 + 4th tone → bú (the fix). These are exactly the cases pypinyin missed.
    for word, want in [("不是", "bú shì"), ("不去", "bú qù"), ("不错", "bú cuò"),
                       ("不用", "bú yòng"), ("不够", "bú gòu"), ("不但", "bú dàn")]:
        check(f"{word} → {want}", _tone_pinyin(word) == want)

    # 2. 不 + 1st/2nd/3rd tone → bù, unchanged (no sandhi applies here).
    for word, want in [("不吃", "bù chī"), ("不来", "bù lái"), ("不好", "bù hǎo"),
                       ("不行", "bù xíng")]:
        check(f"{word} → {want} (no sandhi)", _tone_pinyin(word) == want)

    # 3. 一 is NOT touched — it needs context (cardinal vs ordinal), left to pypinyin.
    for word, want in [("一样", "yī yàng"), ("一个", "yí gè"), ("一天", "yī tiān"),
                       ("一月", "yí yuè"), ("第一", "dì yī")]:
        check(f"一 untouched: {word} → {want}", _tone_pinyin(word) == want)

    # 4. Grammatical/lexical 地/得 are NOT touched (needs POS; a blanket rule would regress
    #    the lexical readings). We only assert they're left as pypinyin has them.
    for word in ["高兴地", "看得见", "地方", "得到", "觉得", "阵地"]:
        check(f"地/得 untouched: {word}", _tone_pinyin(word) == _bare(word))

    # 5. V不C potential complements: the rule fires only on a full-tone 'bù', so pypinyin's
    #    already-neutral / already-bú renderings are left alone (no over-application).
    for word in ["看不见", "差不多", "买不到", "对不对"]:
        check(f"V不C left alone: {word}", _tone_pinyin(word) == _bare(word))

    # 6. The two surfaces agree on the sandhi'd marks (pure-Han inputs).
    for word in ["不是", "不去", "我不是学生", "一样不对", "看得见"]:
        check(f"seg == _tone_pinyin: {word}", _seg(word) == _tone_pinyin(word))

    # 7. Sandhi never crosses punctuation: 不 at a run end (before a comma) stays bù.
    check("不 before punctuation stays bù", _tone_pinyin("不。是") == "bù 。 shì")

    print("\nAll 不-sandhi checks passed.")


def _bare(text):
    """pypinyin Style.TONE WITHOUT the post-pass — the reference for 'left unchanged'."""
    from pypinyin import Style, pinyin as _p
    return " ".join(s[0] for s in _p(text, style=Style.TONE))


def test_pinyin_sandhi():
    """pytest entry point — runs the full check sequence (see conftest.py)."""
    main()


if __name__ == "__main__":
    main()
