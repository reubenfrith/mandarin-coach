"""Generate the labeled tone-assessment dataset (recipe form) → datagen/tone_dataset.json.

Each case is a SYNTHESIS RECIPE — a Chao pitch-level sequence + synth params + a gold
label — NOT audio bytes. The eval (surfaces/pronunciation/tone_assessment_eval.py) renders every recipe
to a WAV and runs it through the real pYIN pipeline, so the dataset stays light (a few KB
of JSON, not MB of audio) and is fully reproducible: synthesis is deterministic in the
stored seed.

WHAT THIS CALIBRATES.  The production coach auto-logs a tone error whenever the DSP's
predicted tone differs from the KNOWN target tone (pronounce_api.py — `if not v["ok"]`).
A FALSE POSITIVE there logs a syllable the learner said acceptably as a mistake and
poisons the per-user corpus — the same "false positives are the dangerous class" concern
as the structured-extraction surface. This dataset exists to measure that predicate's
precision and set a confidence gate, before the writes are trusted.

GOLD LABELS ARE PERTURBATION-DEFINED, not human-validated: we choose both the distortion
and whether it counts as a wrong tone. That makes this an UPPER BOUND on real-L2 precision
(clean synthetic voicing, no creak), not a human-accuracy figure — stated plainly in the
eval's report. Cases split into two bands so the eval reports them separately:

  * clean       — the target tone reproduced faithfully (gold: correct) vs a different
                  tone's template (gold: wrong). Wide, separable by construction: a sanity
                  FLOOR, not a calibration. If precision dips even here, the DSP is broken.
  * borderline  — near-miss productions that risk FLIPPING the classifier's label. A
                  same-category imperfect attempt that must NOT be logged (gold: correct),
                  vs one that crosses into a NEIGHBOURING tone and SHOULD be logged (gold:
                  wrong). This band — especially T2<->T3 — is where the logging predicate's
                  precision is actually decided and where a margin gate earns its keep.

Run:  uv run python evals/datagen/generate_tone_dataset.py
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent / "tone_dataset.json"

# The four lexical tones as Chao level sequences — must match tone_analysis.TONE_LEVELS.
TONE_LEVELS = {1: [5, 5], 2: [3, 5], 3: [2, 1, 4], 4: [5, 1]}
TONE_NAMES = {1: "T1 high-level", 2: "T2 rising", 3: "T3 dipping", 4: "T4 falling"}


def _case(cid, target, levels, gold_wrong, band, note, *, jitter, noise, seed):
    return {
        "id": cid, "target_tone": target, "produced_levels": levels,
        "gold_wrong": gold_wrong, "band": band, "note": note,
        "jitter": jitter, "noise": noise, "seed": seed,
    }


def build() -> dict:
    cases: list[dict] = []
    seed = 100  # deterministic, monotonic across cases so every recipe synthesises distinctly

    # ----------------------------------------------------------------- clean band
    # Correct: the target tone reproduced faithfully, several takes. Must NOT log.
    for t in (1, 2, 3, 4):
        for k in range(4):
            seed += 1
            cases.append(_case(
                f"clean_ok_t{t}_{k}", t, TONE_LEVELS[t], False, "clean",
                f"faithful {TONE_NAMES[t]}", jitter=0.035, noise=0.005, seed=seed))
    # Wrong: a DIFFERENT tone's template against this target — a gross, unambiguous error.
    for t in (1, 2, 3, 4):
        for o in (1, 2, 3, 4):
            if o == t:
                continue
            for k in range(2):
                seed += 1
                cases.append(_case(
                    f"clean_wrong_t{t}_as{o}_{k}", t, TONE_LEVELS[o], True, "clean",
                    f"target {TONE_NAMES[t]} produced as {TONE_NAMES[o]}",
                    jitter=0.035, noise=0.005, seed=seed))

    # ------------------------------------------------------------- borderline band
    # CORRECT-but-imperfect (gold: correct — must NOT log): a recognisable rendition of the
    # target that stays inside its category. These are the false-positive risks: an honest
    # attempt the classifier might flip to a neighbour. Heavier jitter/noise = more realistic.
    borderline_ok = {
        1: [[5, 4.3], [4.8, 4.4], [5, 4.1]],          # mild sag, still high-level
        2: [[3, 4.3], [2.8, 4.4], [3.2, 4.6]],        # shallow but real rise
        3: [[2.6, 1.6, 3.2], [2.8, 2.0, 3.4], [2.4, 1.5, 3.0]],  # shallow dip-rise
        4: [[5, 2.2], [4.8, 2.4], [5, 2.6]],          # shallow but clear fall
    }
    for t, variants in borderline_ok.items():
        for j, lv in enumerate(variants):
            for k in range(2):
                seed += 1
                cases.append(_case(
                    f"bord_ok_t{t}_{j}_{k}", t, lv, False, "borderline",
                    f"imperfect-but-acceptable {TONE_NAMES[t]}",
                    jitter=0.05, noise=0.007, seed=seed))

    # WRONG-crossing (gold: wrong — SHOULD log): the attempt leaves the target's category and
    # lands in a neighbour's. Milder than the clean-wrong cases (near the boundary), so the
    # classifier's margin here is the real test of recall.
    borderline_wrong = {
        1: [([3.3, 5], "→T2 rising"), ([3.6, 4.8], "→T2 shallow-rise")],
        2: [([3.9, 3.9], "→T1 flat, no rise"), ([2.3, 1.3, 4.0], "→T3 dip")],
        3: [([4.4, 1.4], "→T4 falling"), ([2.3, 4.7], "→T2 rising, no dip")],
        4: [([4.5, 4.5], "→T1 flat, no fall"), ([3.1, 4.7], "→T2 rising")],
    }
    for t, variants in borderline_wrong.items():
        for j, (lv, why) in enumerate(variants):
            for k in range(2):
                seed += 1
                cases.append(_case(
                    f"bord_wrong_t{t}_{j}_{k}", t, lv, True, "borderline",
                    f"{TONE_NAMES[t]} produced {why}",
                    jitter=0.05, noise=0.007, seed=seed))

    return {
        "meta": {
            "description": "Perturbation-defined labeled tones for the auto-logging precision gate.",
            "tone_levels": TONE_LEVELS,
            "bands": {
                "clean": "faithful target vs a different tone template — separable sanity floor",
                "borderline": "near-miss same-category (correct) vs neighbour-crossing (wrong)",
            },
            "gold_semantics": "gold_wrong=True → a teacher would mark the wrong tone and it SHOULD be logged.",
            "caveat": "Clean synthetic voicing; an upper bound on real-L2 precision (no creak). CREPE/L2 = Phase 2.",
        },
        "cases": cases,
    }


def main():
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    cases = data["cases"]
    n_ok = sum(1 for c in cases if not c["gold_wrong"])
    n_wrong = sum(1 for c in cases if c["gold_wrong"])
    for band in ("clean", "borderline"):
        b = [c for c in cases if c["band"] == band]
        print(f"  {band:11s}: {len(b):3d}  ("
              f"{sum(1 for c in b if not c['gold_wrong'])} correct / "
              f"{sum(1 for c in b if c['gold_wrong'])} wrong)")
    print(f"  total      : {len(cases):3d}  ({n_ok} correct / {n_wrong} wrong)")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
