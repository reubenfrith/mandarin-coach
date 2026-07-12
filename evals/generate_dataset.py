"""Build evals/test_dataset.json — the 60-case head-to-head dataset (Task 5).

Design decision (deviates from the original "generate with Claude" plan, and is
stronger for it): Type A cases are **derived from the reference corpus**, not
LLM-generated. Every grammar rule and error pattern already ships a hand-authored
(incorrect -> correct) pair plus an id and category. Deriving from them gives:
  - ground-truth correction labels we trust (no need to hand-verify a generator), and
  - a ground-truth retrieval target (expected_rule_id) for RAGAS context recall,
    by construction, for the 24 grammar-rule cases.

Type B/C are built from seed_data (deterministic), with expected answers frozen
into the JSON so the dataset is the single source of truth and the run is reproducible.

Run:  uv run python evals/generate_dataset.py
"""
import _env  # noqa: F401  — loads .env, isolates ChromaDB, adds app/ to path

import json
from pathlib import Path

from seed_data import EXAMPLES, EXPLANATIONS, build_typec_corpus

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "evals" / "test_dataset.json"


def _load(name: str) -> list[dict]:
    return json.loads((DATA / name).read_text())


def build_type_a() -> list[dict]:
    """40 stateless correction pairs from the reference corpus.

    24 from grammar_rules (each carries expected_rule_id -> RAGAS ground truth),
    16 from error_patterns (correction/grounding cases; no single grammar-rule
    target, so expected_rule_id is null and they're excluded from context recall).
    """
    cases: list[dict] = []
    for r in _load("grammar_rules.json"):
        cases.append(
            {
                "id": f"A{len(cases)+1:02d}",
                "source": "grammar_rule",
                "input": r["incorrect_example"],
                "expected_correction": r["correct_example"],
                "category": r["category"],
                "expected_rule_id": r["id"],  # RAGAS context-recall target
                "rule_name": r["name"],
                "reference_explanation": r["explanation"],
            }
        )
    for p in _load("error_patterns.json"):
        cases.append(
            {
                "id": f"A{len(cases)+1:02d}",
                "source": "error_pattern",
                "input": p["incorrect"],
                # correct field can hold two options ("X / Y"); keep the first as canonical
                "expected_correction": p["correct"].split(" / ")[0].strip(),
                "expected_correction_alternatives": p["correct"],
                "category": p["category"],
                "expected_rule_id": None,
                "rule_name": p["error_type"],
                "reference_explanation": p["note"],
            }
        )
    assert len(cases) == 40, f"expected 40 Type A cases, got {len(cases)}"
    return cases


def build_type_b() -> list[dict]:
    """10 small-scale memory sequences: seed 4 same-category errors, probe a 5th.

    The expected output must reference the user's history (this is their Nth Xerror).
    Two sequences per category across the five categories.
    """
    cases: list[dict] = []
    categories = list(EXAMPLES)  # particle, tones, measure_word, word_order, vocabulary
    for ci, cat in enumerate(categories):
        pool = EXAMPLES[cat]
        for rep in range(2):  # two sequences per category -> 10 total
            # Seed 4 records of this category (rotate through the pool), spread over time.
            seed = []
            for k in range(4):
                orig, corr = pool[(rep + k) % len(pool)]
                seed.append(
                    {
                        "original": orig,
                        "correction": corr,
                        "category": cat,
                        "explanation": EXPLANATIONS[cat],
                        "days_ago": 40 - (rep * 20) - k * 3,
                    }
                )
            # Probe: a fresh same-category error (next item in the pool).
            probe_orig, probe_corr = pool[(rep + 4) % len(pool)]
            cases.append(
                {
                    "id": f"B{len(cases)+1:02d}",
                    "category": cat,
                    "seed": seed,
                    "input": probe_orig,
                    "expected_correction": probe_corr,
                    # Personalisation ground truth: after 4 seeded, this is the 5th.
                    "seeded_count": len(seed),
                    "expected_min_count": len(seed) + 1,
                }
            )
    assert len(cases) == 10, f"expected 10 Type B cases, got {len(cases)}"
    return cases


# Ten distinct aggregation questions over the same at-scale corpus. Testing many
# aggregation *questions* over one corpus gives broader coverage of the decisive
# metric than 10 near-identical count queries would. Expected answers are frozen
# from the deterministic corpus below.
TYPEC_QUESTIONS = [
    ("total", "How many errors have I logged in total? Give the exact number."),
    ("most_frequent", "Which single error category do I make most often, and how many times?"),
    ("count_particle", "Exactly how many particle errors have I made?"),
    ("count_tones", "Exactly how many tone errors have I made?"),
    ("count_measure_word", "Exactly how many measure-word errors have I made?"),
    ("increasing", "Which of my error categories are increasing recently?"),
    ("decreasing", "Which of my error categories are decreasing (getting better) recently?"),
    ("particle_trend", "Are my particle errors increasing or decreasing recently?"),
    ("tones_trend", "Are my tone errors increasing or decreasing recently?"),
    (
        "full_breakdown",
        "Give me a full breakdown: total, exact count per category, my most frequent "
        "category, and whether each category is increasing or decreasing.",
    ),
]


def build_type_c() -> list[dict]:
    """10 at-scale aggregation cases over one deterministic 60-record corpus.

    Every case shares the same seeded corpus (frozen here) but asks a different
    aggregation question with a frozen expected answer, so Aggregation Accuracy is
    checkable by exact match against known truth.
    """
    corpus = build_typec_corpus()
    # Derive frozen ground truth from the corpus the same way error_stats does.
    from collections import Counter

    by_cat = dict(Counter(r["category"] for r in corpus).most_common())
    ordered = sorted(corpus, key=lambda r: -r["days_ago"])  # oldest first
    half = len(ordered) // 2
    earlier = Counter(r["category"] for r in ordered[:half])
    recent = Counter(r["category"] for r in ordered[half:])
    trend = {
        c: ("increasing" if recent[c] - earlier[c] > 0 else "decreasing" if recent[c] - earlier[c] < 0 else "steady")
        for c in by_cat
    }
    most_frequent = max(by_cat, key=by_cat.get)
    truth = {
        "total": len(corpus),
        "by_category": by_cat,
        "trend": trend,
        "most_frequent": most_frequent,
        "increasing": sorted([c for c, t in trend.items() if t == "increasing"]),
        "decreasing": sorted([c for c, t in trend.items() if t == "decreasing"]),
    }

    cases: list[dict] = []
    for key, question in TYPEC_QUESTIONS:
        cases.append(
            {
                "id": f"C{len(cases)+1:02d}",
                "seed": corpus,
                "ask": key,
                "input": question,
                "truth": truth,
            }
        )
    assert len(cases) == 10, f"expected 10 Type C cases, got {len(cases)}"
    return cases


def main():
    dataset = {
        "meta": {
            "description": "Head-to-head eval set: agent vs naked-LLM control arm.",
            "counts": {"type_a": 40, "type_b": 10, "type_c": 10, "total": 60},
        },
        "type_a": build_type_a(),
        "type_b": build_type_b(),
        "type_c": build_type_c(),
    }
    OUT.write_text(json.dumps(dataset, ensure_ascii=False, indent=2))
    a, b, c = len(dataset["type_a"]), len(dataset["type_b"]), len(dataset["type_c"])
    rag = sum(1 for x in dataset["type_a"] if x["expected_rule_id"])
    print(f"Wrote {OUT}")
    print(f"  Type A: {a}  ({rag} with expected_rule_id for RAGAS context recall)")
    print(f"  Type B: {b}  (small-scale memory)")
    print(f"  Type C: {c}  (at-scale aggregation over {len(dataset['type_c'][0]['seed'])} records)")


if __name__ == "__main__":
    main()
