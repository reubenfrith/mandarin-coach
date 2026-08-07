"""LLM-as-judge scorers + deterministic extractors for the head-to-head.

Two kinds of scoring, kept deliberately separate:

* JUDGE (subjective, LLM decides): Correction Accuracy and Personalisation — the
  judge returns a structured verdict at temperature 0 for repeatability.
* EXTRACT-then-CHECK (objective, code decides): for Factual Grounding the LLM only
  *extracts* the claims an answer makes into structured fields; the pass/fail is then
  computed in Python against the reference corpus (CC-CEDICT / HSK). Aggregation
  Accuracy is scored the same way but with a deterministic parser (lib/agg_parse.py)
  in place of the LLM extractor, checked against frozen truth (seeded counts).
  Applied symmetrically to both arms so neither is scored more leniently.

The judge model is configurable via JUDGE_MODEL. Because both arms use the same
model under test, a same-model judge cannot systematically favour one arm over the
other on identity grounds — the comparison stays fair.
"""
from lib import _env  # noqa: F401

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
# 1. Correction Accuracy (A_stateless/B_small/C_scale) — subjective judge
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
# 2. Personalisation (B_small/C_scale) — subjective judge
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
# 3. Aggregation — EXTRACT claims, then check in Python (C_scale)
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
# 4. Factual grounding — extract pinyin/HSK claims, check vs corpus (A_stateless/B_small/C_scale)
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


# --------------------------------------------------------------------------- #
# 5. Voice-coach reply quality — subjective judge (voice_coach surface)
# --------------------------------------------------------------------------- #
# The voice coach explains grammar aloud to an English speaker mid-practice. Unlike the
# text coach it has hard behavioural rules the reference-based correction judge doesn't
# capture: explain in ENGLISH (Chinese only for examples), and — on a garbled/mis-heard
# turn — ask to repeat rather than inventing a correction. One judge covers all case types
# by scoring the reply against a per-case EXPECTATION (the case author's rubric), plus two
# intrinsic booleans (English-ness, asks-to-repeat) that don't need a rubric.
class VoiceQualityVerdict(BaseModel):
    # No field defaults: gpt-4o-mini (this surface's judge) uses OpenAI strict JSON-schema
    # mode, which requires EVERY property in `required` — a default makes it optional and the
    # schema is rejected. Required + strict also guarantees the model fills each field (which
    # is exactly what glm failed to do here).
    meets_expectation: bool = Field(description="Does the reply do what the EXPECTATION describes for this turn (answer the question / correctly break down the sentence / ask to repeat)?")
    misleading: bool = Field(description="Does the reply make a materially wrong or misleading claim about Mandarin?")
    explanation_in_english: bool = Field(description="Is the EXPLANATION prose written in English? Chinese used only for the example words/sentences themselves is fine and expected — judge the explanation, not the examples.")
    asks_to_repeat: bool = Field(description="Does the reply ask the learner to repeat or clarify (rather than answering / correcting)?")
    reason: str = Field(description="One sentence justification.")


_VOICE_SYS = (
    "You judge a spoken Mandarin COACH's reply. The coach breaks down grammar for an "
    "English-speaking learner in the middle of a spoken practice session. You are given the "
    "recent spoken context, the learner's current turn, an EXPECTATION describing what a correct "
    "reply must do, and the coach's reply. Decide four things: (1) meets_expectation — does the "
    "reply actually do what the EXPECTATION describes? (2) misleading — does it state anything "
    "materially wrong about Mandarin? (3) explanation_in_english — is the EXPLANATION written in "
    "English? (Chinese used only for the example words/sentences is correct and expected; judge "
    "the explanatory prose, not the examples.) (4) asks_to_repeat — does it ask the learner to "
    "repeat or clarify instead of answering? Be strict but fair; reward a reply that meets the "
    "expectation even if its wording differs from any example."
)


async def judge_voice_answer(context: str, question: str, expectation: str, answer: str) -> VoiceQualityVerdict:
    msg = (
        f"Recent spoken context:\n{context or '(none)'}\n\n"
        f"Learner's turn: {question}\n\n"
        f"EXPECTATION (what a correct reply must do):\n{expectation}\n\n"
        f"Coach's reply:\n{answer}"
    )
    return await _judge(VoiceQualityVerdict).ainvoke(
        [SystemMessage(content=_VOICE_SYS), HumanMessage(content=msg)]
    )


# --------------------------------------------------------------------------- #
# 6. Teaching quality — subjective judge (text_coach surface; calibrated vs human)
# --------------------------------------------------------------------------- #
# The correction judges above ask "is the coach RIGHT?" (identifies_error / correct_fix /
# misleading). This one asks the orthogonal question the learner actually feels: does the
# reply TEACH? Two booleans, deliberately not a 1–5 score (the same OpenRouter constrained-int
# problem the module header documents):
#   * explains_why — does it convey the underlying rule/principle (WHY the error is an error),
#     not merely hand back the corrected sentence? A fix-only or padded-but-empty reply is False.
#   * explanation_in_english — is the EXPLANATION prose in English (these are English-speaker
#     learners)? An explanation written entirely in Chinese is a real teaching defect — the
#     learner may not be able to read it. Chinese used only for the example words/sentences is
#     fine and expected (mirrors the voice surface's explanation_in_english).
# This surface's whole point is that the judge is CALIBRATED against human labels (Cohen's κ)
# before its verdicts are trusted — so use a strong, independent judge (gpt-4o, not the coach).
class TeachingVerdict(BaseModel):
    # No field defaults — gpt-4o's strict JSON-schema mode requires every property in
    # `required`; a default makes it optional and the schema is rejected (see VoiceQualityVerdict).
    explains_why: bool = Field(description="Does the reply explain the underlying RULE or PRINCIPLE — WHY the learner's version is wrong / why the fix is right — rather than only giving the corrected sentence or generic encouragement? A reply that just shows the fix, or that is long but never states the actual rule, is False.")
    explanation_in_english: bool = Field(description="Is the EXPLANATION prose written in English (the learner's first language)? Chinese used only for the example words/sentences themselves is fine and expected — judge the explanatory prose, not the examples. An explanation written substantially in Chinese is False.")
    reason: str = Field(description="One sentence justification.")


_TEACHING_SYS = (
    "You judge the TEACHING QUALITY of a Mandarin coach's reply to an English-speaking learner "
    "who made an error. Assume the correction itself is already known to be correct — do NOT "
    "re-grade correctness. Judge only two things about how well it teaches: (1) explains_why — "
    "does the reply convey the underlying grammar RULE or PRINCIPLE (why the learner's version is "
    "wrong and the fix is right), rather than merely handing back the corrected sentence or "
    "offering generic praise/encouragement with no rule? A reply can be long and friendly yet "
    "still fail this if it never states the actual rule. (2) explanation_in_english — is the "
    "EXPLANATORY PROSE in English? These learners are English speakers; an explanation written "
    "substantially in Chinese is a teaching defect. Chinese used only for the example words and "
    "sentences is correct and expected — judge the prose, not the examples. Be strict but fair."
)


async def judge_teaching(learner_input: str, rule_why: str, answer: str) -> TeachingVerdict:
    msg = (
        f"Learner's erroneous sentence: {learner_input}\n\n"
        f"The grammar point at issue (reference — what a good explanation would convey):\n{rule_why}\n\n"
        f"Coach's reply:\n{answer}"
    )
    return await _judge(TeachingVerdict).ainvoke(
        [SystemMessage(content=_TEACHING_SYS), HumanMessage(content=msg)]
    )


# --------------------------------------------------------------------------- #
# 7. Misleading SECONDARY content — subjective judge (the axis a human found)
# --------------------------------------------------------------------------- #
# The head-to-head correction judge only checks the HEADLINE fix. But the reply also carries
# hints, drill answers, example tables, measure-word assignments, exception lists, side-claims —
# and an expert blind-labeller found real errors in exactly that auxiliary content (cats take 只
# not 个; 想 CAN take 在; 被…把… co-occurrence is not forbidden; a summary table mislabelled a
# sentence) that NO other surface in the suite inspects. This judge targets that class alone:
#   * has_error   — does the SUPPORTING content contain a claim that is factually wrong or
#                   materially overstated in standard Mandarin?  (The main correction is assumed
#                   correct and is out of scope — do not re-grade it.)
#   * errors      — each specific wrong claim (quote it + say why wrong), so the flag can be
#                   checked for the RIGHT reason, not just a coincidental trip.
# This is open-ended grammar correctness — genuinely hard for a judge — so the eval scores it
# against the expert's independent gold (precision/recall on the known errors), not on trust.
class SecondaryVerdict(BaseModel):
    # No defaults — gpt-4o strict JSON-schema requires every field (see VoiceQualityVerdict).
    has_error: bool = Field(description="Does the reply's SUPPORTING content (hints, drill answers/prompts, example tables, measure-word assignments, exception lists, parenthetical side-claims — anything OTHER than the headline corrected sentence) contain a claim that is factually WRONG or materially OVERSTATED in standard Mandarin?")
    errors: list[str] = Field(description="One entry per wrong/overstated claim found: quote the claim and state why it's wrong. Empty list if none.")
    reason: str = Field(description="One sentence overall justification.")


_SECONDARY_SYS = (
    "You are a meticulous native-level Mandarin proofreader checking a coach's reply for factual "
    "errors in its SUPPORTING material — NOT the main correction. Assume the headline corrected "
    "sentence is already correct and OUT OF SCOPE. Scrutinise everything else the reply asserts: "
    "hints, drill questions AND their given answers, example sentences, measure-word choices "
    "(e.g. 只 vs 个 vs 张), lists of 'words that can/can't do X', comparative/aspect claims, and "
    "any summary table. Flag a claim ONLY if it is actually wrong or materially overstated in "
    "standard Mandarin — e.g. assigning the wrong measure word, calling a grammatical pattern "
    "impossible when it exists, mislabelling an example, or a drill answer that is incorrect. Do "
    "NOT flag stylistic preferences, simplifications that are true-enough for a beginner, or the "
    "main correction. Be precise: quote the specific claim and explain the error. If the "
    "supporting content is all correct, return has_error=false with an empty errors list."
)


async def judge_secondary_errors(learner_input: str, grammar_point: str, answer: str) -> SecondaryVerdict:
    msg = (
        f"Learner's original sentence: {learner_input}\n"
        f"Grammar point being taught: {grammar_point}\n\n"
        f"Coach's reply (check its SUPPORTING content only):\n{answer}"
    )
    return await _judge(SecondaryVerdict).ainvoke(
        [SystemMessage(content=_SECONDARY_SYS), HumanMessage(content=msg)]
    )


# --------------------------------------------------------------------------- #
# 8. Corpus-quality audit — grade the REFERENCE RULE itself (fix errors at source)
# --------------------------------------------------------------------------- #
# The secondary-error work found the coach's ONE systematic error (把/被 "never both") traces to a
# corpus `common_mistake` field that over-flattens the rule — and a corpus error propagates to every
# reply grounded on that rule. So audit the rules themselves: does a rule's explanation / common_mistake
# assert something factually WRONG or materially OVER-BROAD in standard Mandarin (an absolute
# never/always/only/cannot with real exceptions an advanced speaker would reject)? Beginner-true
# simplifications are fine. Runs best with a frontier judge (gpt-5 caught exactly this class).
class RuleAuditVerdict(BaseModel):
    has_issue: bool = Field(description="Does the rule's explanation or common_mistake contain a claim that is factually WRONG or materially OVER-BROAD in standard Mandarin (e.g. an absolute never/always/only/cannot that has real exceptions)? A beginner-appropriate simplification that is true-enough is NOT an issue.")
    severity: str = Field(description="Worst issue severity: 'none', 'minor' (pedantic edge case), or 'major' (would teach an advanced learner something false).")
    issues: list[str] = Field(description="One entry per problem: quote the offending claim, say why it is wrong/over-broad, and suggest a minimal fix. Empty if none.")
    reason: str = Field(description="One sentence overall justification.")


_AUDIT_SYS = (
    "You are a native-level Mandarin linguist auditing a single grammar rule that a tutoring app "
    "teaches to English-speaking learners. You are given the rule's name, its explanation, the "
    "'common mistake' note, and its examples. Flag ONLY claims that are factually WRONG or "
    "materially OVER-BROAD in standard Mandarin — especially absolute statements (never / always / "
    "only / cannot / must) that have real exceptions an advanced speaker would object to, or a "
    "'common mistake' that labels correct usage as an error. Do NOT flag: pedagogical "
    "simplifications that are true-enough for a beginner, stylistic preferences, register notes, or "
    "the examples unless an example is actually incorrect. For each genuine problem, quote the "
    "specific claim, explain why it is wrong or over-broad (with a counterexample if you can), and "
    "suggest a minimal fix that keeps it beginner-friendly. If the rule is sound to teach, set "
    "has_issue=false, severity='none', empty issues. Be precise and conservative — a false alarm "
    "wastes a reviewer's time."
)


async def audit_grammar_rule(name: str, explanation: str, common_mistake: str, examples: str) -> RuleAuditVerdict:
    msg = (
        f"Rule name: {name}\n\n"
        f"Explanation (taught to the learner):\n{explanation}\n\n"
        f"'Common mistake' note:\n{common_mistake or '(none)'}\n\n"
        f"Examples:\n{examples or '(none)'}"
    )
    return await _judge(RuleAuditVerdict).ainvoke(
        [SystemMessage(content=_AUDIT_SYS), HumanMessage(content=msg)]
    )


# --------------------------------------------------------------------------- #
# 9. Rule-harm re-rank — turn the over-inclusive audit into an actionable to-do list
# --------------------------------------------------------------------------- #
# The audit (§8) over-flags: gpt-5 marks any linguistically-over-broad claim "major", including
# defensible beginner simplifications. This second pass re-ranks a FLAGGED rule by the criterion
# that actually causes product harm: would a coach following this rule literally mark a CORRECT,
# LEVEL-APPROPRIATE (HSK 1-4) learner sentence as WRONG? That separates "would reject correct usage"
# (real harm — the A06 class) from "merely incomplete / omits an advanced-register exception a
# beginner won't produce" (leave it). The 'level-appropriate' filter is what screens out the
# pedantic edge cases (二两, formal 两国) that inflated the audit's major count.
class RuleHarmVerdict(BaseModel):
    would_reject_correct: bool = Field(description="Would a coach applying this rule LITERALLY mark a CORRECT sentence — one a beginner/intermediate (HSK 1-4) learner would plausibly write — as an error? True only for real harm, not for omitting an advanced/formal/edge-register exception a beginner won't produce.")
    rejected_example: str = Field(description="A concrete, correct, level-appropriate learner sentence this rule would wrongly flag as an error (in Chinese, with a short English gloss). Empty string if would_reject_correct is false.")
    fix: str = Field(description="Minimal wording change to the rule's explanation/common_mistake that removes the harm while staying beginner-friendly. Empty if no change needed.")
    reason: str = Field(description="One sentence justification.")


_HARM_SYS = (
    "You triage a grammar rule taught by a beginner/intermediate (HSK 1-4) Mandarin tutoring app, to "
    "decide whether it should be EDITED now. Apply ONE test: if the coach follows this rule literally, "
    "would it mark a CORRECT, LEVEL-APPROPRIATE learner sentence as an ERROR? Answer would_reject_correct "
    "= true ONLY when a sentence a beginner/intermediate learner would actually produce, and which is "
    "correct, gets wrongly rejected (real product harm) — e.g. an absolute 'you must use X' that condemns "
    "a correct alternative the learner would use. Answer FALSE when the rule is merely incomplete: it omits "
    "an exception that only shows up in advanced, formal, literary, or rare-register usage a beginner will "
    "not produce (those simplifications are appropriate — do NOT flag them). Give a concrete correct "
    "sentence that would be wrongly rejected (or empty if none), and a minimal beginner-friendly fix. Be "
    "strict: the goal is a short, real edit list, not a linguistics-completeness review."
)


async def judge_rule_harm(name: str, explanation: str, common_mistake: str, examples: str) -> RuleHarmVerdict:
    msg = (
        f"Rule name: {name}\n\n"
        f"Explanation (taught to the learner):\n{explanation}\n\n"
        f"'Common mistake' note:\n{common_mistake or '(none)'}\n\n"
        f"Examples:\n{examples or '(none)'}"
    )
    return await _judge(RuleHarmVerdict).ainvoke(
        [SystemMessage(content=_HARM_SYS), HumanMessage(content=msg)]
    )


# --------------------------------------------------------------------------- #
# 10. Did the coach REJECT a correct sentence? — behavioural detector (empirical harm test)
# --------------------------------------------------------------------------- #
# The audit + harm re-rank both over-flag (LLM self-triage can't calibrate itself). The rigorous
# convergent test is behavioural: feed each proposed CORRECT sentence to the real coach and see if it
# actually marks it wrong. This detector classifies ONE coach reply — did it treat the (correct)
# sentence as an error and correct it, or affirm it? Affirming while offering a stylistic tweak is
# NOT a rejection. Easy classification — a cheap judge (gpt-4o) suffices.
class RejectionVerdict(BaseModel):
    marked_wrong: bool = Field(description="Did the coach treat the learner's sentence as containing an ERROR — saying it is wrong/incorrect/unnatural, or giving a 'corrected' replacement? True = rejected. False = affirmed it as correct (offering an optional stylistic alternative while affirming correctness is still False).")
    evidence: str = Field(description="Quote the phrase showing rejection or affirmation.")


_REJECT_SYS = (
    "You are given a learner's Chinese sentence that is KNOWN TO BE CORRECT, and a Mandarin coach's "
    "reply to it. Decide only this: did the coach REJECT the sentence — i.e. treat it as containing an "
    "error, call it wrong/incorrect/unnatural, or hand back a 'corrected' version — or did it AFFIRM the "
    "sentence as correct? If the coach affirms it is correct and merely offers an optional more-natural "
    "or stylistic alternative, that is NOT a rejection (marked_wrong=false). Quote the deciding phrase."
)


async def judge_coach_rejected(sentence: str, reply: str) -> RejectionVerdict:
    msg = f"Learner's (correct) sentence: {sentence}\n\nCoach's reply:\n{reply}"
    return await _judge(RejectionVerdict).ainvoke(
        [SystemMessage(content=_REJECT_SYS), HumanMessage(content=msg)]
    )
