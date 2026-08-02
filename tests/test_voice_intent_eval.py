"""Guards the voice-router eval's scoring math (evals/surfaces/voice_coach/voice_intent_eval.py).

The metric definitions are the kind of thing that silently rots — 'coach = positive', so a
CONVERSE turn routed to COACH is a FALSE POSITIVE (the jarring failure) and drives coach
PRECISION. These pure functions have no model calls, so they're cheap to pin. Run: pytest -q.
"""
import importlib.util
import pathlib

# The eval lives under evals/surfaces/voice_coach (not a package on the default path); load by path.
_SURFACE = pathlib.Path(__file__).resolve().parents[1] / "evals" / "surfaces" / "voice_coach" / "voice_intent_eval.py"
_spec = importlib.util.spec_from_file_location("voice_intent_eval", _SURFACE)
vie = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vie)


def test_outcome_coach_is_positive():
    # gold coach → TP when caught, FN (graceful) when routed to converse
    assert vie.outcome("coach", "coach") == "TP"
    assert vie.outcome("coach", "converse") == "FN"
    # gold converse → FP (JARRING) when routed to coach, TN when kept
    assert vie.outcome("converse", "coach") == "FP"
    assert vie.outcome("converse", "converse") == "TN"


def test_code_path_matches_real_heuristic():
    # The tuned router fast-paths the UNAMBIGUOUS (plain Mandarin statement, short English aside,
    # empty) and classifies the AMBIGUOUS (Mandarin question, longer English, mixed).
    assert vie.code_path("我昨天去了公园") == "heuristic"       # Mandarin statement
    assert vie.code_path("me too") == "heuristic"              # short English glue
    assert vie.code_path("。。。") == "heuristic"               # empty
    assert vie.code_path("这个词是什么意思？") == "classifier"   # Mandarin question
    assert vie.code_path("why was that wrong?") == "classifier"  # longer English
    assert vie.code_path("这个 refund 怎么申请") == "classifier"  # mixed


def test_summarise_headline_and_bucket_split():
    # One row per outcome, tagged with its resolving stage, so the aggregate is predictable:
    #   heuristic english FP (jarring), heuristic mandarin FN (graceful),
    #   classifier mixed TP, heuristic english TN.
    rows = [
        {"id": "e08", "bucket": "english", "gold_intent": "converse", "pred_intent": "coach",
         "resolved_by": "heuristic", "outcome": "FP", "note": None, "bucket_mismatch": None},
        {"id": "m11", "bucket": "mandarin", "gold_intent": "coach", "pred_intent": "converse",
         "resolved_by": "heuristic", "outcome": "FN", "note": None, "bucket_mismatch": None},
        {"id": "x02", "bucket": "mixed", "gold_intent": "coach", "pred_intent": "coach",
         "resolved_by": "classifier", "outcome": "TP", "note": None, "bucket_mismatch": None},
        {"id": "e01", "bucket": "english", "gold_intent": "coach", "pred_intent": "coach",
         "resolved_by": "heuristic", "outcome": "TP", "note": None, "bucket_mismatch": None},
    ]
    s = vie.summarise(rows)
    assert s["confusion_matrix"] == {"TP": 2, "FP": 1, "FN": 1, "TN": 0}
    # coach precision = TP/(TP+FP) = 2/3
    assert abs(s["coach_precision"] - 2 / 3) < 1e-9
    # misroute rate = FP / (converse golds) = 1/1 (the lone converse gold was misrouted)
    assert s["converse_total"] == 1
    assert s["converse_to_coach_misroute_rate"] == 1.0
    # the classifier's own slice is perfect here (its single case is a TP)
    assert s["classifier_only"]["precision"] == 1.0
    # per-bucket keeps heuristic error (english FP) separate from classifier (mixed clean)
    assert s["per_bucket"]["english"]["fp"] == 1
    assert s["per_bucket"]["mixed"]["fn"] == 0
    assert s["resolution"] == {"heuristic": 3, "classifier": 1}


def test_summarise_empty_is_safe():
    s = vie.summarise([])
    assert s["confusion_matrix"] == {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    assert s["coach_precision"] is None
    assert s["accuracy"] is None


def test_head_to_head_fixed_and_regressed():
    # coach = positive. Router: a02 misrouted (FP), b01 correct (TN). Classify-always: a02 now
    # correct (TN) = FIXED; b01 now misrouted (FP) = REGRESSED.
    router = [
        {"id": "a02", "outcome": "FP", "resolved_by": "heuristic"},
        {"id": "b01", "outcome": "TN", "resolved_by": "heuristic"},
        {"id": "c03", "outcome": "TP", "resolved_by": "classifier"},
    ]
    ca = [
        {"id": "a02", "text": "and you?", "bucket": "english", "outcome": "TN", "note": None},
        {"id": "b01", "text": "…", "bucket": "empty", "outcome": "FP", "note": "no content"},
        {"id": "c03", "text": "why 把?", "bucket": "mixed", "outcome": "TP", "note": None},
    ]
    h = vie.head_to_head(ca, router)
    assert h["fixed_n"] == 1 and h["fixed"][0]["id"] == "a02"
    assert h["regressed_n"] == 1 and h["regressed"][0]["id"] == "b01"
    assert h["both_right"] == 1  # c03
    assert h["n_compared"] == 3


def test_spread_over_runs_reports_band_and_instability():
    # Two turns, 3 votes each. t1 always coach (gold coach) → always TP. t2 votes
    # [converse, coach, converse] (gold converse) → run 1 TN, run 2 FP, run 3 TN: unstable.
    rows = [
        {"id": "t1", "bucket": "mixed", "gold_intent": "coach", "resolved_by": "classifier",
         "votes": ["coach", "coach", "coach"], "stable": True},
        {"id": "t2", "bucket": "mixed", "gold_intent": "converse", "resolved_by": "classifier",
         "votes": ["converse", "coach", "converse"], "stable": False},
    ]
    sp = vie.spread_over_runs(rows, repeats=3)
    assert sp["n_unstable"] == 1 and sp["unstable_ids"] == ["t2"]
    # run 2 has an FP (t2), so coach precision dips that run → min < max
    assert sp["coach_precision"]["min"] < sp["coach_precision"]["max"]
    # accuracy: runs 1 & 3 perfect (1.0), run 2 has the FP (0.5) → mean between
    assert sp["accuracy"]["min"] == 0.5 and sp["accuracy"]["max"] == 1.0
