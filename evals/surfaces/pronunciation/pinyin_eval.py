"""Pīnyīn-accuracy surface → results/pinyin_accuracy.{md,json}.

WHAT PRODUCTION DOES.  The ruby a learner reads (`汉字` with pīnyīn underneath, in the text
and voice coaches) and the `/api/pinyin` string both come from `tools.pinyin_segments` /
`tools._tone_pinyin`, which call pypinyin with `Style.TONE` — CITATION tones. Wrong pīnyīn
printed under a hanzi teaches a wrong pronunciation, so this surface scores: *is the
displayed tone the one the learner should actually say?*

THE HEADLINE IS INCONSISTENCY, NOT "CITATION VS SPOKEN".  pypinyin's tone output is a
lexicalised lookup, not a rule engine, so it is internally inconsistent on the SAME
phenomenon: 不是→bú but 不去→bù; 一个→yí but 一样→yī; 听得懂→de but 看得见→dé. That is a
defect under ANY convention and needs no philosophical defense — it is what we lead with.
The buckets keep the unassailable defects apart from the defensible product choice so the
eval never overclaims (see datagen/generate_pinyin_dataset.py for the gold discipline):

  * yi_bu_sandhi     — DEFECT. Metric = CONSISTENCY: within one sub-rule (不+T4→bú) pypinyin
                       applies sandhi to some words, not others. Reported per sub-rule.
  * neutral_particle — DEFECT. Grammatical 地/得 are read `de`; pypinyin prints dì/dé. Wrong
                       lexical reading, not sandhi → unassailable. Accuracy is the metric.
  * t3_bisyllabic    — COVERAGE GAP, not a defect. Citation (nǐ hǎo) is a defensible
                       dictionary convention, so harm is weak; we report coverage of the
                       spoken form and surface citation-vs-spoken as a product decision.
  * redup            — SECONDARY (soft gold; some dicts keep full tone).
  * control          — SANITY FLOOR. Lexical polyphones pypinyin gets right; must be ~100%
                       or the eval is broken, not pypinyin.
  * t3_multi / erhua — carried, NOT scored (contested realisation / unexpressible in
                       per-hanzi ruby). Reported for honesty.

We also re-run every defect through pypinyin's own `ToneSandhiMixin` to quantify what the
built-in fix buys — "we tried the obvious fix, here's the residual" — which is what makes
the recommendation land.

Fully deterministic: no model calls, no network, no LLM judge (like the tone surface).

Run:      uv run python evals/surfaces/pronunciation/pinyin_eval.py
Re-agg:   uv run python evals/surfaces/pronunciation/pinyin_eval.py --from-rows
Prereq:   evals/datagen/pinyin_dataset.json  (build with datagen/generate_pinyin_dataset.py)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma isolation

import argparse  # noqa: E402
import json  # noqa: E402

from pypinyin import Style, pinyin as _pinyin  # noqa: E402
from pypinyin.contrib.tone_sandhi import ToneSandhiMixin  # noqa: E402
from pypinyin.converter import DefaultConverter  # noqa: E402
from pypinyin.core import Pinyin  # noqa: E402

from tools import _tone_pinyin, pinyin_segments  # noqa: E402  — the functions under test

DATASET = _env.DATAGEN / "pinyin_dataset.json"
RESULTS = _env.RESULTS

# pypinyin's own tone-sandhi converter, used ONLY to quantify what the built-in fix recovers.
_MIX = Pinyin(type("C", (ToneSandhiMixin, DefaultConverter), {})())


def _mixin_pinyin(text: str) -> str:
    return " ".join(s[0] for s in _MIX.pinyin(text, style=Style.TONE))


def _seg_pinyin(text: str) -> str:
    """Pīnyīn as derived from the production ruby segmenter — the per-hanzi marks joined.
    Must equal _tone_pinyin (both are Style.TONE); we assert it so a future divergence
    between the two surfaces is caught, not silently scored on one of them."""
    return " ".join(s["pinyin"] for s in pinyin_segments(text) if "pinyin" in s)


def analyse_case(case: dict) -> dict:
    text = case["text"]
    got = _tone_pinyin(text)
    seg = _seg_pinyin(text)
    row = {
        "text": text, "bucket": case["bucket"], "sub_rule": case["sub_rule"],
        "harm": case["harm"], "scored": case["scored"], "gold": case["gold"],
        "got": got,
        "seg_agrees": seg == got,          # ruby marks == /api/pinyin marks (structural check)
        "mixin_got": _mixin_pinyin(text),  # what pypinyin's own sandhi converter would print
    }
    if case["scored"]:
        row["match"] = got == case["gold"]                     # citation output correct?
        row["mixin_match"] = row["mixin_got"] == case["gold"]  # built-in fix correct?
    else:
        row["match"] = None
        row["mixin_match"] = None
    return row


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _rate(rows: list[dict], pred=lambda r: r["match"]) -> dict:
    """n, k, rate over scored rows where pred is True."""
    n = len(rows)
    k = sum(1 for r in rows if pred(r))
    return {"n": n, "k": k, "rate": (k / n) if n else None}


def _sub_rule_table(rows: list[dict], bucket: str) -> dict:
    """Per sub-rule pass counts within a bucket — the consistency view. `inconsistent` is
    True when a sub-rule is applied to SOME but not all of its members (0 < k < n): the
    same rule, different output, driven only by which bigram pypinyin has lexicalised."""
    subs = {}
    for sr in sorted({r["sub_rule"] for r in rows if r["bucket"] == bucket}):
        srr = [r for r in rows if r["bucket"] == bucket and r["sub_rule"] == sr]
        st = _rate(srr)
        st["inconsistent"] = 0 < st["k"] < st["n"]
        st["mixin"] = _rate(srr, pred=lambda r: r["mixin_match"])
        subs[sr] = st
    return subs


def summarise(rows: list[dict]) -> dict:
    scored = [r for r in rows if r["scored"]]

    def bucket_rows(b):
        return [r for r in scored if r["bucket"] == b]

    yb = bucket_rows("yi_bu_sandhi")
    # Sandhi that SHOULD change the citation form (exclude bu_T123, the no-sandhi control).
    yb_applies = [r for r in yb if r["sub_rule"] != "bu_T123"]

    def bucket_summary(b):
        br = bucket_rows(b)
        s = _rate(br)
        s["mixin"] = _rate(br, pred=lambda r: r["mixin_match"])
        s["sub_rules"] = _sub_rule_table(rows, b)
        return s

    return {
        "n_cases": len(rows),
        "n_scored": len(scored),
        "seg_agrees_all": all(r["seg_agrees"] for r in rows),  # ruby == /api/pinyin marks
        # --- the headline: 一/不 sandhi consistency (where sandhi should change the form) ---
        "sandhi": {
            **_rate(yb_applies),
            "mixin": _rate(yb_applies, pred=lambda r: r["mixin_match"]),
            "sub_rules": _sub_rule_table(rows, "yi_bu_sandhi"),
        },
        "neutral_particle": bucket_summary("neutral_particle"),
        "t3_bisyllabic": bucket_summary("t3_bisyllabic"),
        "redup": bucket_summary("redup"),
        "control": bucket_summary("control"),
        "unscored": {
            b: [r["text"] for r in rows if r["bucket"] == b]
            for b in ("t3_multi", "erhua")
        },
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def _pct(x):
    return "—" if x is None else f"{x:.2f}"


def _fails(rows, bucket):
    return [r for r in rows if r["bucket"] == bucket and r["scored"] and not r["match"]]


def render_md(summary: dict, rows: list[dict]) -> str:
    sd = summary["sandhi"]
    npt = summary["neutral_particle"]
    t3 = summary["t3_bisyllabic"]
    ctrl = summary["control"]
    control_ok = ctrl["rate"] == 1.0

    lines = [
        "# Pīnyīn-accuracy eval — `tools.pinyin_segments` / `_tone_pinyin`",
        "",
        "The ruby a learner reads (`汉字` with pīnyīn underneath, in both coaches) and the "
        "`/api/pinyin` string come from pypinyin `Style.TONE` — **citation tones**. Wrong "
        "pīnyīn under a hanzi teaches a wrong pronunciation, so we score whether the displayed "
        "tone is the one the learner should say. **Fully deterministic** — no model calls, no "
        "judge — over a hand-authored gold set.",
        "",
        "> **Framing (what is and isn't a defect).** Citation tones are a *defensible* "
        "dictionary convention, so we do **not** headline \"pypinyin doesn't apply sandhi.\" We "
        "headline **inconsistency**: pypinyin applies the *same* rule to some words and not "
        "others (不是→bú but 不去→bù), which is wrong under citation **or** spoken convention. "
        "The pure third-tone gap (你好→nǐ hǎo) is reported as a **coverage gap under the "
        "spoken-tone product choice** (weak harm), not a defect — that decision is surfaced to "
        "you, not pre-made.",
        "",
    ]

    # ---- Decision block ----
    sr = sd["sub_rules"]
    incon = [k for k, v in sr.items() if v["inconsistent"]]  # 一/不 sub-rules only
    lines += [
        f"**Decision — the tone marks need a rule-based post-pass; pypinyin `Style.TONE` alone "
        f"is not display-safe.** Two unassailable defect classes, independent of the "
        f"citation-vs-spoken question:",
        "",
        f"1. **一/不 sandhi is inconsistent** — where sandhi should change the citation form, "
        f"pypinyin applies it to only **{sd['k']}/{sd['n']}** ({_pct(sd['rate'])}) syllables, "
        f"scattered *within* each sub-rule (inconsistent: {', '.join(incon) or 'none'}). Same "
        f"rule, different output, decided only by which bigram is lexicalised.",
        f"2. **Grammatical 地/得 get the wrong reading** — the adverbial 地 and the V得C "
        f"complement 得 are the neutral syllable `de`, but pypinyin prints `dì`/`dé` in "
        f"**{npt['n'] - npt['k']}/{npt['n']}** cases. Not sandhi — the wrong lexical reading.",
        "",
        f"pypinyin's own `ToneSandhiMixin` is a **partial** remedy (recovers "
        f"{sd['mixin']['k']}/{sd['mixin']['n']} of the 一/不 cases and "
        f"{npt['mixin']['k']}/{npt['mixin']['n']} of the neutral-particle cases — see the "
        f"per-rule tables), so it is not a drop-in fix. **Recommendation:** add a small "
        f"rule-based sandhi/neutral-tone post-pass over the per-hanzi marks in "
        f"`pinyin_segments`, and make citation-vs-spoken for pure T3 an explicit product "
        f"choice (currently citation by default, {_pct(t3['rate'])} coverage of the spoken "
        f"form).",
        "",
        f"Sanity floor: the **control** bucket (lexical polyphones pypinyin resolves — 银行, "
        f"长江, 目的, 觉得) scores **{_pct(ctrl['rate'])}** "
        f"({ctrl['k']}/{ctrl['n']}). "
        + ("The test is not rigged against pypinyin — it passes exactly where pypinyin is right."
           if control_ok else
           "**⚠ control < 1.0 — the eval or gold is broken, not pypinyin. Fix before trusting "
           "any number above.**"),
        "",
        f"Dataset: **{summary['n_cases']}** cases ({summary['n_scored']} scored). Ruby marks "
        f"match the `/api/pinyin` marks on every case "
        f"({'✓' if summary['seg_agrees_all'] else '✗ — surfaces diverge!'}). See "
        f"`results/README.md` to re-derive any number.",
        "",
        "## 1. 一/不 sandhi — consistency (the headline)",
        "",
        "`applied` = pypinyin already prints the sandhi form. The story is the **spread inside "
        "a single sub-rule**: a rule engine would be 0/N or N/N, never scattered.",
        "",
        "| Sub-rule | applied | rate | inconsistent? | mixin recovers |",
        "|---|---|---|---|---|",
    ]
    labels = {
        "bu_T4": "不 + 4th tone → bú",
        "bu_T123": "不 + 1/2/3 → bù (no sandhi; control)",
        "yi_T4": "一 + 4th tone → yí",
        "yi_T123": "一 + 1/2/3 → yì",
    }
    for k in ("bu_T4", "yi_T4", "yi_T123", "bu_T123"):
        v = sr[k]
        inc = "**yes**" if v["inconsistent"] else ("n/a (control)" if k == "bu_T123" else "no")
        lines.append(f"| {labels[k]} | {v['k']}/{v['n']} | {_pct(v['rate'])} | {inc} | "
                     f"{v['mixin']['k']}/{v['mixin']['n']} |")
    lines += [
        "",
        "The `bu_T123` row is a **fairness control**: when no sandhi applies, citation IS "
        "correct and pypinyin scores full marks — the eval only faults it where the tone "
        "genuinely changes.",
        "",
        "## 2. Grammatical neutral particles 地 / 得 (unassailable defect)",
        "",
        "| Sub-rule | correct | rate | mixin recovers |",
        "|---|---|---|---|",
    ]
    for k in ("di_adverbial", "de_complement"):
        v = npt["sub_rules"][k]
        lbl = "地 adverbial → de" if k == "di_adverbial" else "得 (V得C complement) → de"
        lines.append(f"| {lbl} | {v['k']}/{v['n']} | {_pct(v['rate'])} | "
                     f"{v['mixin']['k']}/{v['mixin']['n']} |")
    npt_fails = _fails(rows, "neutral_particle")
    lines += [
        "",
        "Note 得 is *also* internally inconsistent — `听得懂`→`de` (right) while `看得见`→`dé` "
        "(wrong), same V得C grammar. Wrong renderings:",
        "",
    ]
    for r in npt_fails:
        lines.append(f"- `{r['text']}` → pypinyin `{r['got']}`, should be `{r['gold']}`")
    lines += [
        "",
        "## 3. Third-tone sandhi, bisyllabic (coverage gap — a product choice, not a defect)",
        "",
        f"Spoken T3+T3 → T2+T3 (你好 → ní hǎo). pypinyin shows citation on "
        f"**{t3['n'] - t3['k']}/{t3['n']}** — coverage of the spoken form is **{_pct(t3['rate'])}**. "
        f"Harm is **weak**: marking citation tones and teaching the sandhi rule separately is a "
        f"legitimate convention. This is surfaced as a decision — *do we want the ruby to show "
        f"what's written (citation) or what's said (spoken)?* — not scored as broken. "
        f"(mixin recovers {t3['mixin']['k']}/{t3['mixin']['n']}.)",
        "",
        f"## 4. Reduplication (secondary — soft gold)",
        "",
        f"Neutral 2nd syllable (谢谢 → xièxie): pypinyin keeps full tone on "
        f"**{summary['redup']['n'] - summary['redup']['k']}/{summary['redup']['n']}**. Kept "
        f"**secondary** — some dictionaries do mark the full tone, so this is a weaker claim "
        f"than 地/得.",
        "",
        "## 5. Carried but not scored (honesty)",
        "",
        f"- **3+ stacked third tones** ({', '.join(summary['unscored']['t3_multi'])}): "
        f"realisation is prosody/grouping-dependent and genuinely contested — scoring it would "
        f"measure our opinion, not a defect.",
        f"- **儿化** ({', '.join(summary['unscored']['erhua'])}): 花儿 → huār is one spoken "
        f"syllable, but `pinyin_segments` is one-pīnyīn-per-hanzi by contract, so erhua is "
        f"**unexpressible** in the ruby — a structural model limitation, not a pypinyin miss.",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-rows", action="store_true",
                    help="re-aggregate + re-render from saved rows (no recompute)")
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    if args.from_rows:
        rows = json.loads((RESULTS / "pinyin_accuracy.json").read_text())["rows"]
    else:
        cases = json.loads(DATASET.read_text())["cases"]
        print(f"Pīnyīn-accuracy surface: scoring {len(cases)} cases through the real "
              f"pinyin_segments / _tone_pinyin...")
        rows = [analyse_case(c) for c in cases]

    summary = summarise(rows)
    (RESULTS / "pinyin_accuracy.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    (RESULTS / "pinyin_accuracy.md").write_text(render_md(summary, rows))

    sd, npt, t3, ctrl = (summary["sandhi"], summary["neutral_particle"],
                         summary["t3_bisyllabic"], summary["control"])
    print(f"\nDone. {summary['n_cases']} cases ({summary['n_scored']} scored).")
    print(f"  一/不 sandhi applied: {sd['k']}/{sd['n']} ({_pct(sd['rate'])}) "
          f"— inconsistent within sub-rules")
    print(f"  地/得 neutral particle correct: {npt['k']}/{npt['n']} ({_pct(npt['rate'])})")
    print(f"  T3 bisyllabic spoken-coverage: {t3['k']}/{t3['n']} ({_pct(t3['rate'])}) "
          f"— coverage gap, weak harm")
    print(f"  control (sanity floor): {ctrl['k']}/{ctrl['n']} ({_pct(ctrl['rate'])})"
          + ("" if ctrl["rate"] == 1.0 else "  ⚠ EVAL BROKEN — control must be 1.0"))
    print(f"  built-in ToneSandhiMixin recovers: 一/不 {sd['mixin']['k']}/{sd['mixin']['n']}, "
          f"neutral {npt['mixin']['k']}/{npt['mixin']['n']}")
    print(f"  wrote {RESULTS / 'pinyin_accuracy.md'} and .json")


if __name__ == "__main__":
    main()
