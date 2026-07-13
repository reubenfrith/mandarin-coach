"""Regenerate data/hsk_vocab.json from the complete-hsk-vocabulary dataset.

Source: complete-hsk-vocabulary by Yanis Zafirópulos (drkameleon), MIT License,
https://github.com/drkameleon/complete-hsk-vocabulary (complete.json, 11,470 entries
with old-HSK-2.0 + new/newest-HSK-3.0 level tags; glosses from CC-CEDICT). We take the
**old HSK 1-6**
standard (the classic ~5,000-word list), because our schema uses an integer hsk_level
1-6, the app targets HSK 2-4 learners, and the README describes "HSK 1-6 official word
lists". Words that exist only in HSK 3.0 (no old level) are skipped.

Output schema (unchanged): {id, word, pinyin, meaning, hsk_level, pos, example}.
Example sentences aren't in the source, so we preserve the hand-curated examples from
the existing seed by word match; the rest carry "".

This mainly powers `dictionary_lookup`'s HSK grounding (memory._load_hsk_map), which
previously knew only 22 words, and re-seeds the hsk_vocabulary vector collection.

Run:  python3 data/build_hsk_vocab.py <path-to-complete.json>
"""
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "hsk_vocab.json"

POS = {
    "n": "noun", "v": "verb", "a": "adjective", "d": "adverb", "p": "preposition",
    "r": "pronoun", "m": "numeral", "q": "measure word", "c": "conjunction",
    "u": "particle", "nz": "proper noun", "t": "time word", "f": "locative",
    "s": "place word", "nr": "name", "ns": "place name", "nt": "organization",
    "an": "adjective", "vn": "verb", "vd": "verb", "i": "idiom", "l": "phrase",
    "o": "onomatopoeia", "e": "interjection", "y": "modal particle", "h": "prefix",
    "k": "suffix", "g": "morpheme", "x": "other", "w": "punctuation", "j": "abbreviation",
}


def old_level(entry) -> int | None:
    """Smallest old-HSK level tag on the entry, or None if it isn't in old HSK 1-6."""
    lvls = [int(m.group(1)) for lv in entry.get("level", [])
            if (m := re.match(r"old-(\d)$", lv))]
    return min(lvls) if lvls else None


def build(src_path: str):
    src = json.loads(Path(src_path).read_text(encoding="utf-8"))
    examples = {r["word"]: r.get("example", "") for r in json.loads(OUT.read_text(encoding="utf-8"))}

    best: dict[str, dict] = {}  # simplified -> chosen record (lowest level wins)
    for e in src:
        lvl = old_level(e)
        if lvl is None:
            continue
        word = e["simplified"]
        form = (e.get("forms") or [{}])[0]
        pinyin = form.get("transcriptions", {}).get("pinyin", "")
        meanings = [m for m in form.get("meanings", []) if m]
        meaning = "; ".join(meanings)[:200]
        pos = ", ".join(POS.get(p, p) for p in (e.get("pos") or [])) or ""
        rec = {"word": word, "pinyin": pinyin, "meaning": meaning,
               "hsk_level": lvl, "pos": pos, "example": examples.get(word, "")}
        if word not in best or lvl < best[word]["hsk_level"]:
            best[word] = rec

    # Stable order: by level then frequency-ish (source order preserved within level).
    records = sorted(best.values(), key=lambda r: (r["hsk_level"], r["word"]))
    for i, r in enumerate(records, 1):
        r_id = f"hsk_{i:04d}"
        # rebuild dict with id first to match existing field order
        records[i - 1] = {"id": r_id, "word": r["word"], "pinyin": r["pinyin"],
                          "meaning": r["meaning"], "hsk_level": r["hsk_level"],
                          "pos": r["pos"], "example": r["example"]}

    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)), "duplicate ids"
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    from collections import Counter
    by_lvl = Counter(r["hsk_level"] for r in records)
    kept_examples = sum(1 for r in records if r["example"])
    print(f"Wrote {OUT}: {len(records)} words")
    print(f"  by HSK level: {dict(sorted(by_lvl.items()))}")
    print(f"  curated examples preserved: {kept_examples}")


if __name__ == "__main__":
    build(sys.argv[1])
