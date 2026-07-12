"""LLM-as-judge scorers + deterministic extractors for the head-to-head.

Two kinds of scoring, kept deliberately separate:

* JUDGE (subjective, LLM decides): Correction Accuracy and Personalisation — the
  judge returns a structured verdict at temperature 0 for repeatability.
* EXTRACT-then-CHECK (objective, code decides): for Aggregation Accuracy and
  Factual Grounding the LLM only *extracts* the claims an answer makes into
  structured fields; the pass/fail is then computed in Python against frozen truth
  (seeded counts) or the reference corpus (CC-CEDICT / HSK). Applied symmetrically
  to both arms so neither is scored more leniently.

The judge model is configurable via JUDGE_MODEL. Because both arms use the same
model under test, a same-model judge cannot systematically favour one arm over the
other on identity grounds — the comparison stays fair.
"""
import _env  # noqa: F401

import os
import re

from config import get_llm
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# Default to a non-reasoning model as the independent judge: it is faster, avoids
# any self-preference (the arms under test run deepseek), and — critically —
# reliably fills structured BOOLEAN fields. (Constrained-int score fields like
# ge=1,le=5 come back garbled to the minimum on these OpenRouter models, so every
# metric below is boolean/extractive, never a 1–5 judge score.)
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "glm")


def _judge(schema):
    """A temperature-0 structured-output judge/extractor bound to `schema`."""
    return get_llm(JUDGE_MODEL, temperature=0.0, streaming=False).with_structured_output(schema)


# --------------------------------------------------------------------------- #
# Category normalisation (answers say "particles", "助词", "Particle" ...)
# --------------------------------------------------------------------------- #
CANON = ["particle", "tones", "measure_word", "word_order", "vocabulary", "grammar"]
_ALIASES = {
    "particle": "particle", "particles": "particle", "助词": "particle", "把": "particle",
    "tone": "tones", "tones": "tones", "声调": "tones",
    "measure": "measure_word", "measure_word": "measure_word", "measure_words": "measure_word",
    "measureword": "measure_word", "量词": "measure_word",
    "word_order": "word_order", "wordorder": "word_order", "word order": "word_order", "语序": "word_order",
    "vocabulary": "vocabulary", "vocab": "vocabulary", "词汇": "vocabulary", "word_choice": "vocabulary",
    "grammar": "grammar", "语法": "grammar",
}


def canon_category(s: str | None) -> str | None:
    if not s:
        return None
    key = re.sub(r"[\s\-]+", "_", s.strip().lower())
    if key in _ALIASES:
        return _ALIASES[key]
    for raw, canon in _ALIASES.items():
        if raw in key:
            return canon
    return None


# --------------------------------------------------------------------------- #
# 1. Correction Accuracy (Type A/B/C) — subjective judge
# --------------------------------------------------------------------------- #
class CorrectionVerdict(BaseModel):
    identifies_error: bool = Field(default=False, description="Does the answer correctly identify the grammatical error in the learner's sentence?")
    correct_fix: bool = Field(default=False, description="Does the answer provide a correct fix (need not match the reference verbatim; multiple valid corrections exist)?")
    misleading: bool = Field(default=False, description="Does the answer contain a materially misleading or wrong claim about the grammar?")
    reason: str = Field(default="", description="One sentence justification.")


_CORRECTION_SYS = (
    "You are a strict but fair Mandarin grammar examiner. Given a learner's erroneous "
    "sentence, a reference correct version, and a tutoring system's answer, judge whether "
    "the system correctly identified and fixed the error. The system's wording may differ "
    "from the reference; accept any linguistically correct fix. Do not reward fluent prose "
    "that fails to actually correct the mistake."
)


async def judge_correction(learner_input: str, reference: str, answer: str) -> CorrectionVerdict:
    msg = (
        f"Learner's sentence: {learner_input}\n"
        f"Reference correct version: {reference}\n\n"
        f"System's answer:\n{answer}"
    )
    return await _judge(CorrectionVerdict).ainvoke(
        [SystemMessage(content=_CORRECTION_SYS), HumanMessage(content=msg)]
    )


# --------------------------------------------------------------------------- #
# 2. Personalisation (Type B/C) — subjective judge
# --------------------------------------------------------------------------- #
class PersonalisationVerdict(BaseModel):
    references_history: bool = Field(default=False, description="Does the answer explicitly reference the learner's PAST error history (e.g. 'you've made this mistake before', 'this is recurring')?")
    cites_number: bool = Field(default=False, description="Does it cite a specific count or ordinal from that history (e.g. 'your 5th particle error', '15 times')?")
    reason: str = Field(default="", description="One sentence justification.")


_PERSONALISATION_SYS = (
    "You judge whether a Mandarin tutoring answer is PERSONALISED to the learner's own "
    "error history, versus a generic correction any learner could receive. Personalisation "
    "means explicitly referring to the learner's past mistakes, recurrence, counts, or trend "
    "— not merely correcting the current sentence well."
)


async def judge_personalisation(answer: str) -> PersonalisationVerdict:
    return await _judge(PersonalisationVerdict).ainvoke(
        [SystemMessage(content=_PERSONALISATION_SYS), HumanMessage(content=f"System's answer:\n{answer}")]
    )


# --------------------------------------------------------------------------- #
# 3. Aggregation — EXTRACT claims, then check in Python (Type C)
# --------------------------------------------------------------------------- #
class AggregationClaims(BaseModel):
    # Explicit named scalar fields (the category set is fixed and known). This is the
    # most reliable shape for JSON-mode models — it captures a count whether the answer
    # gives a full breakdown OR just mentions one category in prose ("15 particle errors").
    total: int | None = Field(default=None, description="Total error count the answer states, or null if none stated.")
    particle_count: int | None = Field(default=None, description="Count the answer gives for PARTICLE errors (把/了/的/得/地), or null.")
    tones_count: int | None = Field(default=None, description="Count the answer gives for TONE errors, or null.")
    measure_word_count: int | None = Field(default=None, description="Count the answer gives for MEASURE-WORD errors, or null.")
    word_order_count: int | None = Field(default=None, description="Count the answer gives for WORD-ORDER errors, or null.")
    vocabulary_count: int | None = Field(default=None, description="Count the answer gives for VOCABULARY/word-choice errors, or null.")
    most_frequent: str | None = Field(default=None, description="The category the answer calls most frequent, or null.")
    increasing: list[str] = Field(default_factory=list, description="Categories the answer says are increasing/getting worse.")
    decreasing: list[str] = Field(default_factory=list, description="Categories the answer says are decreasing/improving.")

    def by_category(self) -> dict[str, int]:
        m = {
            "particle": self.particle_count, "tones": self.tones_count,
            "measure_word": self.measure_word_count, "word_order": self.word_order_count,
            "vocabulary": self.vocabulary_count,
        }
        return {k: v for k, v in m.items() if v is not None}


_AGG_SYS = (
    "You are a precise information extractor. Read a tutoring answer and extract ONLY the "
    "numerical claims it actually makes about the learner's error statistics. Capture a "
    "category's count whether it appears in a full breakdown OR is mentioned in prose "
    "(e.g. 'you've made 15 particle errors' -> particle_count=15). Map synonyms to the right "
    "field (e.g. 把/了/的/得 -> particle; word choice -> vocabulary). For increasing/decreasing, "
    "list a category only if the answer explicitly says its trend is rising or falling. "
    "Do NOT infer, correct, or add anything the answer does not state; leave unstated values null."
)


async def extract_aggregation(answer: str) -> AggregationClaims:
    return await _judge(AggregationClaims).ainvoke(
        [SystemMessage(content=_AGG_SYS), HumanMessage(content=f"Answer:\n{answer}")]
    )


def score_aggregation(ask: str, claims: AggregationClaims, truth: dict) -> tuple[bool, str]:
    """Exact-match the claim relevant to this case's question against frozen truth."""
    claimed = {canon_category(n): c for n, c in claims.by_category().items() if canon_category(n)}
    inc = {canon_category(x) for x in claims.increasing}
    dec = {canon_category(x) for x in claims.decreasing}

    # Most-frequent: prefer an explicit claim; else derive from the stated counts
    # (if the answer gave a breakdown, its #1 is implied and checkable). Symmetric
    # across both arms.
    most_freq = canon_category(claims.most_frequent)
    if most_freq is None and claimed:
        most_freq = max(claimed, key=claimed.get)

    if ask == "total":
        return claims.total == truth["total"], f"claimed {claims.total} vs {truth['total']}"
    if ask == "most_frequent":
        return most_freq == truth["most_frequent"], f"claimed {most_freq} vs {truth['most_frequent']}"
    if ask.startswith("count_"):
        cat = ask[len("count_"):]
        return claimed.get(cat) == truth["by_category"][cat], (
            f"claimed {claimed.get(cat)} vs {truth['by_category'][cat]} for {cat}"
        )
    if ask == "increasing":
        return inc == set(truth["increasing"]), f"claimed {sorted(x for x in inc if x)} vs {truth['increasing']}"
    if ask == "decreasing":
        return dec == set(truth["decreasing"]), f"claimed {sorted(x for x in dec if x)} vs {truth['decreasing']}"
    if ask.endswith("_trend"):
        cat = ask[: -len("_trend")]
        want = truth["trend"][cat]
        got = "increasing" if cat in inc else "decreasing" if cat in dec else "steady"
        return got == want, f"claimed {cat} {got} vs {want}"
    if ask == "full_breakdown":
        checks = [
            claims.total == truth["total"],
            all(claimed.get(c) == n for c, n in truth["by_category"].items()),
            most_freq == truth["most_frequent"],
            inc == set(truth["increasing"]),
            dec == set(truth["decreasing"]),
        ]
        return all(checks), f"{sum(checks)}/5 sub-checks passed"
    return False, f"unknown ask '{ask}'"


# --------------------------------------------------------------------------- #
# 4. Factual grounding — extract pinyin/HSK claims, check vs corpus (Type A/B/C)
# --------------------------------------------------------------------------- #
class GroundingClaims(BaseModel):
    # Flat parallel lists, aligned by index. Use "" / 0 when a value is not stated.
    words: list[str] = Field(default_factory=list, description="Chinese words/characters the answer makes a pinyin or HSK claim about.")
    pinyins: list[str] = Field(default_factory=list, description="Pinyin (with tone marks) for each word, SAME ORDER as words; \"\" if not stated.")
    hsk_levels: list[int] = Field(default_factory=list, description="HSK level for each word, SAME ORDER as words; 0 if not stated.")


_GROUND_SYS = (
    "Extract every factual claim the answer makes about a Chinese word's PINYIN or HSK level. "
    "Only include claims the answer explicitly states. Leave a field null if not stated."
)


async def extract_grounding(answer: str) -> GroundingClaims:
    return await _judge(GroundingClaims).ainvoke(
        [SystemMessage(content=_GROUND_SYS), HumanMessage(content=f"Answer:\n{answer}")]
    )
