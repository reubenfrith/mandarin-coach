"""Build teaching_slice_dataset.json — the calibration set for the teaching-quality surface.

This is a deliberately THIN vertical slice (a feasibility probe), not the full surface. Its
only job is to answer one question before we invest in a larger set: **can an LLM judge track
a HUMAN's teaching-quality labels reliably** (Cohen's κ), or is the axis too subjective to
measure? If the judge can't even separate a real explanation from a fix-only stub, the whole
idea is dead and we stop here.

The set has two kinds of case:

  * REAL (role="real"): 8 authentic coach replies, lifted verbatim from
    results/head_to_head.json (the A_stateless arm of the head-to-head), with the learner
    input + the corpus rule text they concern pulled from test_dataset.json. These are the
    honest material — real outputs of the real coach, not caricatures.
  * CONTROL (role="control"): 4 hand-authored replies at the low/edge of the quality range
    that the real set doesn't contain, so the labels have variance (the real coach is
    consistently strong, so its replies are almost all "good" — κ needs both classes):
      - fix_only        : the correction, no rule            → explains_why=False   (known-bad FLOOR)
      - padded_empty     : long, warm, encouraging, NO rule   → explains_why=False   (LENGTH-BIAS probe)
      - terse_why        : one sentence, states the rule       → explains_why=True    (probe's honest twin)
      - cn_fix_only      : correction only, in Chinese         → explains_why=False, english=False

`human_labels` on every case are MY labels, assigned by reading each reply (the reals) or by
construction (the controls). The surface scores the judge AGAINST these. See the surface's
`.md` for the honest caveats (authored controls make this an UPPER BOUND on κ, etc.).

Run:  uv run python evals/datagen/generate_teaching_slice.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
TEST_DATASET = HERE / "test_dataset.json"
HEAD_TO_HEAD = EVALS / "results" / "head_to_head.json"
OUT = HERE / "teaching_slice_dataset.json"

# The 8 real cases to lift, with MY hand labels. Chosen for a 4/4 English-vs-Chinese split on
# the explanation prose, so explanation_in_english has real variance; all 8 explain the why
# (the real coach is consistently strong there — which is itself the finding the controls exist
# to expose).
REAL = [
    # id     explains_why  english   note (why I labelled it so)
    ("A01",  True,  True,  "English prose, states the 把+complement rule + root cause."),
    ("A02",  True,  False, "Explains 把/被 clash well, but the entire explanation is in Chinese."),
    ("A05",  True,  True,  "English, clean 了-vs-过 contrast table + root cause."),
    ("A07",  True,  False, "States Number+MW+Noun rule, but explanation is Chinese prose."),
    ("A08",  True,  False, "Good stative-verb rule, but explanation is in Chinese."),
    ("A10",  True,  True,  "English, distinguishes 的/地/得 by what they link."),
    ("A11",  True,  True,  "English, explains 比 already carries the comparative (no 很)."),
    ("A14",  True,  False, "States 两-vs-二 rule clearly, but in Chinese prose."),
    ("A06",  True,  False, "BORDERLINE: the saved reply opens mid-way on a 总结 table — states the "
                           "是……的 rule but with little reasoning; Chinese prose. A second labeller "
                           "could reasonably call explains_why=False."),
]

# Hand-authored controls — (id, explains_why, english, learner_input, rule_why, note, reply).
CONTROLS = [
    (
        "C1_fix_only", False, True,
        "我把书看。",
        "The 把 construction needs a complement/result after the verb.",
        "FLOOR: correction only, no rule stated — must score explains_why=False.",
        "❌ 我把书看。\n✅ 我把书看完了。\n\nThat's the correct version. 👍",
    ),
    (
        "C2a_padded_empty", False, True,
        "今天比昨天很热。",
        "In a 比 comparison the adjective takes no 很/非常; use 更 or an amount.",
        "LENGTH-BIAS probe: long, warm, encouraging — but never states the rule. Must be "
        "explains_why=False despite the length. Compare with C2b.",
        "What a great sentence to try! 🌟 Comparisons are honestly one of the trickiest things "
        "in Mandarin, and the fact that you're already attempting them is fantastic — seriously, "
        "keep it up! This is a super common area for English speakers, so don't feel bad at all. "
        "A lot of learners struggle here for months, so you're in good company. The corrected "
        "version is 今天比昨天热。 Keep practising and you'll get the hang of it in no time — "
        "you're doing amazing and I believe in you! Want to try another one? 😊",
    ),
    (
        "C2b_terse_why", True, True,
        "今天比昨天很热。",
        "In a 比 comparison the adjective takes no 很/非常; use 更 or an amount.",
        "The probe's honest twin: one short sentence, but it DOES state the rule. explains_why=True.",
        "In a 比 comparison the adjective can't take 很 — 比 already means \"more\", so drop it: "
        "今天比昨天热。 (Use 更 or 热多了 if you want to stress the degree.)",
    ),
    (
        "C3_cn_fix_only", False, False,
        "我去中国明年。",
        "Time-when adverbials go before the verb: Subject + Time + Verb + Object.",
        "Correction only, and in Chinese — explains_why=False, explanation_in_english=False.",
        "❌ 我去中国明年。\n✅ 我明年去中国。",
    ),
]


def main():
    h2h = {r["id"]: r for r in json.loads(HEAD_TO_HEAD.read_text())["rows"]}
    cases_by_id = {c["id"]: c for c in json.loads(TEST_DATASET.read_text())["A_stateless"]}

    cases = []
    for cid, why, eng, note in REAL:
        src = cases_by_id[cid]
        cases.append({
            "id": cid,
            "role": "real",
            "learner_input": src["input"],
            "rule_name": src.get("rule_name"),
            "rule_why": src["reference_explanation"],
            "reply": h2h[cid]["agent"]["answer"],
            "human_labels": {"explains_why": why, "explanation_in_english": eng},
            "note": note,
        })

    for cid, why, eng, learner_input, rule_why, note, reply in CONTROLS:
        cases.append({
            "id": cid,
            "role": "control",
            "learner_input": learner_input,
            "rule_name": None,
            "rule_why": rule_why,
            "reply": reply,
            "human_labels": {"explains_why": why, "explanation_in_english": eng},
            "note": note,
        })

    payload = {
        "meta": {
            "purpose": "Calibration slice for the teaching-quality judge — feasibility probe.",
            "dims": ["explains_why", "explanation_in_english"],
            "n_real": len(REAL),
            "n_control": len(CONTROLS),
            "labels_by": "human (Reuben) — reals by reading, controls by construction",
        },
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    # Print the label balance so a degenerate (no-variance) set is caught immediately.
    for dim in ["explains_why", "explanation_in_english"]:
        t = sum(1 for c in cases if c["human_labels"][dim])
        print(f"{dim}: {t} True / {len(cases) - t} False  (n={len(cases)})")
    print(f"wrote {OUT}  ({len(cases)} cases: {len(REAL)} real + {len(CONTROLS)} control)")


if __name__ == "__main__":
    main()
