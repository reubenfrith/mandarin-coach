"""Guards the voice-router eval's scoring math (evals/surfaces/voice_intent_eval.py).

The metric definitions are the kind of thing that silently rots — 'coach = positive', so a
CONVERSE turn routed to COACH is a FALSE POSITIVE (the jarring failure) and drives coach
PRECISION. These pure functions have no model calls, so they're cheap to pin. Run: pytest -q.
"""
import importlib.util
import pathlib

# The eval lives under evals/surfaces (not a package on the default path); load it by path.
_SURFACE = pathlib.Path(__file__).resolve().parents[1] / "evals" / "surfaces" / "voice_intent_eval.py"
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
    # Han-only and Latin-only and empty are resolved by the zero-latency heuristic;
    # only a mixed-script turn reaches the classifier.
    assert vie.code_path("我昨天去了公园") == "heuristic"      # Han only
    assert vie.code_path("why was that wrong") == "heuristic"  # Latin only
    assert vie.code_path("。。。") == "heuristic"               # empty
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
