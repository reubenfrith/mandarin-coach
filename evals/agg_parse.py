"""Deterministic parser for Type C aggregation answers.

Why not an LLM extractor: on emoji-laden markdown tables the OpenRouter models
(glm/qwen/deepseek) extract inconsistently and sometimes return prose instead of
JSON — and the flakiness hits BOTH arms, collapsing the head-to-head into false
parity. A reproducible certification metric cannot depend on that. The answers are
highly structured (tables, bullet lists, or prose stating exact numbers), so a
deterministic parser is both more reliable and instantly reproducible.

parse(answer) -> AggregationClaims, so it drops straight into score_aggregation().
"""
import re

from llm_judge import AggregationClaims

# English category name is always present in these answers (Chinese appears only as
# parenthetical examples). Match on the English name; 'particle' etc. are unambiguous.
CAT_KEYWORDS = {
    "particle": ["particle"],
    "tones": ["tone"],
    "measure_word": ["measure word", "measure-word", "measure_word", "measure word", "measure"],
    "word_order": ["word order", "word-order", "word_order"],
    "vocabulary": ["vocabulary", "vocab", "word choice", "word-choice"],
}
INC_TOKENS = ["increas", "rising", "risen", "rose", "climb", "went up", "grew", "jumped",
              "getting worse", "worsen", "trending up", "⬆", "📈", "🔺"]
DEC_TOKENS = ["decreas", "falling", "fell", "fallen", "dropped", "declin", "reduced",
              "went down", "down from", "improv", "getting better", "trending down",
              "⬇", "📉", "🔻"]
STEADY_TOKENS = ["steady", "stable", "unchanged", "flat", "➡"]

_TREND_ARROW = re.compile(r"\(?\s*\d+\s*(?:→|-+>|=>|to)\s*\d+\s*\)?")  # "(3 → 12)", "3->12"
_PCT = re.compile(r"\d+\s*%")
_LEADING_RANK = re.compile(r"^\s*\|?\s*[#\d]+\s*\|")  # "| 1 |" or "1 |" rank cell
_INT = re.compile(r"\d+")


def _clean(line: str) -> str:
    line = _TREND_ARROW.sub(" ", line)
    line = _PCT.sub(" ", line)
    line = _LEADING_RANK.sub(" ", line)
    return line


def _cat_in(line_lc: str, cat: str) -> bool:
    return any(k in line_lc for k in CAT_KEYWORDS[cat])


def _count_in_line(line: str, cat: str) -> int | None:
    """The count for `cat` in a line: the integer nearest the category name after
    stripping rank/percentage/trend-arrow noise."""
    cleaned = _clean(line)
    lc = cleaned.lower()
    if not _cat_in(lc, cat):
        return None
    # position of the category keyword
    pos = min((lc.find(k) for k in CAT_KEYWORDS[cat] if k in lc), default=-1)
    if pos < 0:
        return None
    best, best_dist = None, 1e9
    for m in _INT.finditer(cleaned):
        d = abs(m.start() - pos)
        if d < best_dist:
            best, best_dist = int(m.group()), d
    return best


def _trend_in_line(line_lc: str) -> str | None:
    if any(t in line_lc for t in INC_TOKENS):
        return "increasing"
    if any(t in line_lc for t in DEC_TOKENS):
        return "decreasing"
    if any(t in line_lc for t in STEADY_TOKENS):
        return "steady"
    return None


def _dominant_int(answer: str) -> int | None:
    """The single distinct integer in an answer (after stripping trend arrows /
    percentages) — used for terse replies like a bare '12' to a 'how many X?' query."""
    cleaned = _PCT.sub(" ", _TREND_ARROW.sub(" ", answer))
    ints = {int(m.group()) for m in _INT.finditer(cleaned)}
    return ints.pop() if len(ints) == 1 else None


def parse(answer: str, ask: str | None = None) -> AggregationClaims:
    lines = [ln for ln in answer.splitlines() if ln.strip()]
    counts: dict[str, int] = {}
    trends: dict[str, str] = {}

    for cat in CAT_KEYWORDS:
        for ln in lines:
            lc = ln.lower()
            if not _cat_in(lc, cat):
                continue
            if cat not in counts:
                c = _count_in_line(ln, cat)
                if c is not None:
                    counts[cat] = c
            if cat not in trends:
                t = _trend_in_line(lc)
                if t is not None:
                    trends[cat] = t

    # total: a line mentioning "total"; else, if the whole answer is essentially one
    # number (bare "60"), use it.
    total = None
    for ln in lines:
        if "total" in ln.lower():
            ints = _INT.findall(_clean(ln))
            if ints:
                total = int(ints[0])
                break
    if total is None:
        allints = _INT.findall(answer)
        if len(allints) == 1:
            total = int(allints[0])

    # most frequent: an explicit "most frequent / #1 / 🥇" line, else argmax of counts
    most_frequent = None
    for ln in lines:
        lc = ln.lower()
        if "most frequent" in lc or "#1" in lc or "🥇" in ln or "most common" in lc:
            for cat in CAT_KEYWORDS:
                if _cat_in(lc, cat):
                    most_frequent = cat
                    break
        if most_frequent:
            break
    if most_frequent is None and counts:
        most_frequent = max(counts, key=counts.get)

    # Ask-aware fallback: a terse reply ("12") to "how many measure-word errors?" is a
    # valid category count even though it never names the category. Only trust it when
    # the answer has a single unambiguous integer.
    if ask and ask.startswith("count_"):
        cat = ask[len("count_"):]
        if counts.get(cat) is None:
            di = _dominant_int(answer)
            if di is not None:
                counts[cat] = di
    if ask == "total" and total is None:
        total = _dominant_int(answer)

    return AggregationClaims(
        total=total,
        particle_count=counts.get("particle"),
        tones_count=counts.get("tones"),
        measure_word_count=counts.get("measure_word"),
        word_order_count=counts.get("word_order"),
        vocabulary_count=counts.get("vocabulary"),
        most_frequent=most_frequent,
        increasing=[c for c, t in trends.items() if t == "increasing"],
        decreasing=[c for c, t in trends.items() if t == "decreasing"],
    )
