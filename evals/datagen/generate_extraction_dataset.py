"""Build evals/extraction_dataset.json — the ground-truth set for the
structured-extraction surface (Task 5 #2).

What it evaluates: `extract_and_log_error` (app/agent.py), the *post-turn* LLM
call that mines the learner's turn into a structured error record and appends it
to their corpus. It runs silently after every reply, so a wrong record poisons
the B_small/C_scale memory the other two surfaces depend on — this is the eval that
justifies trusting them.

Design (mirrors generate_dataset.py's frozen-and-inspectable philosophy):

  POSITIVES (40) — inputs that DO contain a correctable error. Reused wholesale
  from the head-to-head A_stateless set: the input, the gold category and gold
  correction come from test_dataset.json, and the **coach reply is the real
  agent answer already stored in results/head_to_head.json** (faithful, free —
  no re-running the agent). The extractor sees exactly what it sees in production
  (learner input + coach reply).

  NEGATIVES (~17) — inputs that must NOT be logged as errors:
    * correct_sentence: a grammatically correct Chinese sentence (drawn from the
      A_stateless gold corrections). had_error must be false.
    * question: a Chinese question/request with no sentence to correct.
    * non_chinese: an English-only message — the `_has_chinese` guard should
      short-circuit before the LLM is ever called (scored deterministically).
  Correct-sentence and question negatives need a *realistic* coach reply (an
  empty or grammar-discussing reply would prime the extractor to hallucinate an
  error and wreck the precision number — see DECISIONS #13), so this script runs
  the real agent (glm) once per negative and FREEZES the reply into the dataset.

Run:  uv run python evals/datagen/generate_extraction_dataset.py
Prereq: results/head_to_head.json must exist (source of positive coach replies).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

from agent import _build_graph, invoke_with_trace  # noqa: E402
from prompts import AGENT_SYSTEM_PROMPT  # noqa: E402

OUT = _env.DATAGEN / "extraction_dataset.json"
DATASET = _env.DATAGEN / "test_dataset.json"
HEAD_TO_HEAD = _env.RESULTS / "head_to_head.json"

AGENT_MODEL = os.environ.get("AGENT_MODEL", "glm")  # deepseek hangs — DECISIONS #4
SPECIFIC_CATEGORIES = {"particle", "tones", "measure_word", "word_order", "vocabulary"}

# Some reference-corpus inputs carry an English editorial parenthetical, e.g.
# "我吃了日本菜。（meaning: I have tried Japanese food）". These are INVALID inputs for
# the extractor: a real learner never types the meaning, and the "error" only exists
# relative to that leaked intent (without it the Chinese is grammatical). Exclude them
# rather than strip — stripping would relabel a genuinely-ambiguous sentence as an error.
_ANNOTATION_RE = re.compile(r"[（(][^）)]*[A-Za-z][^）)]*[）)]")


def _is_annotated(text: str) -> bool:
    return bool(_ANNOTATION_RE.search(text))

# Chinese questions/requests with nothing to correct — had_error must be false.
QUESTION_NEGATIVES = [
    "什么是把字句？可以给我举一个例子吗？",
    "请问「了」和「过」在用法上有什么区别？",
    "量词一般应该怎么用？我经常搞不清楚。",
    "你能推荐几个练习中文语法的好方法吗？",
]

# English-only messages — the _has_chinese guard should skip these before the LLM.
NON_CHINESE_NEGATIVES = [
    "How do I say 'thank you' in Mandarin?",
    "Can you explain what tones are for a beginner?",
    "Give me three tips for memorising new vocabulary.",
]


def _load(p: pathlib.Path) -> dict | list:
    return json.loads(p.read_text())


def build_positives() -> list[dict]:
    """40 A_stateless cases: labels from test_dataset.json, coach reply from head_to_head."""
    if not HEAD_TO_HEAD.exists():
        raise SystemExit(
            f"{HEAD_TO_HEAD} not found — run `uv run python evals/eval_harness.py` first "
            "(positives reuse its stored agent replies)."
        )
    type_a = _load(DATASET)["A_stateless"]
    replies = {
        r["id"]: r["agent"].get("answer", "")
        for r in _load(HEAD_TO_HEAD)["rows"]
        if r["type"] == "A_stateless"
    }
    excluded = [c["id"] for c in type_a if _is_annotated(c["input"])]
    if excluded:
        print(f"  excluding {len(excluded)} annotated (context-dependent) inputs: {excluded}")
    out = []
    for c in type_a:
        if _is_annotated(c["input"]):
            continue
        cat = c["category"]
        out.append(
            {
                "id": c["id"],
                "kind": "positive",
                "input": c["input"],
                "coach_reply": replies.get(c["id"], ""),
                "gold_had_error": True,
                "gold_category": cat,
                # "grammar" is the corpus catch-all; only specific-category golds
                # are scoreable for category accuracy (grammar is underspecified).
                "specific_gold": cat in SPECIFIC_CATEGORIES,
                "gold_correction": c["expected_correction"],
                "gold_correction_alternatives": c.get(
                    "expected_correction_alternatives", c["expected_correction"]
                ),
            }
        )
    missing = [c["id"] for c in out if not c["coach_reply"]]
    if missing:
        print(f"  ! {len(missing)} positives have no stored coach reply: {missing}")
    return out


async def _agent_reply(text: str, tid: str) -> str:
    """One real agent turn (glm) → final answer text, used as a frozen coach reply.

    Retries once on a transient OpenRouter failure/instant-timeout — an empty coach
    reply on a negative would prime the extractor to hallucinate an error and corrupt
    the precision number, so a negative MUST carry a real reply.
    """
    last = None
    for attempt in range(2):
        try:
            graph = _build_graph("gen-extraction", AGENT_SYSTEM_PROMPT, AGENT_MODEL)
            answer, _msgs = await invoke_with_trace(graph, text, tid + f"-{attempt}")
            if answer and answer != "(no response)":
                return answer
            last = "empty answer"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
    raise RuntimeError(f"agent reply failed after retry: {last}")


async def build_negatives() -> list[dict]:
    """~17 negatives. Correct-sentence + question replies are generated fresh (glm)
    and frozen; non-Chinese needs no reply (guard skips before the LLM)."""
    type_a = _load(DATASET)["A_stateless"]
    # Spread correct-sentence negatives across the corpus (every 4th gold correction).
    corrects = [c["expected_correction"] for c in type_a][::4][:10]

    neg: list[dict] = []
    # non_chinese first — no agent call needed.
    for i, txt in enumerate(NON_CHINESE_NEGATIVES, 1):
        neg.append(
            {
                "id": f"NNC{i:02d}", "kind": "non_chinese", "input": txt,
                "coach_reply": "", "gold_had_error": False, "guard_should_skip": True,
            }
        )

    # correct_sentence + question — generate a realistic coach reply, concurrently.
    to_gen: list[dict] = []
    for i, txt in enumerate(corrects, 1):
        to_gen.append({"id": f"NCS{i:02d}", "kind": "correct_sentence", "input": txt})
    for i, txt in enumerate(QUESTION_NEGATIVES, 1):
        to_gen.append({"id": f"NQ{i:02d}", "kind": "question", "input": txt})

    sem = asyncio.Semaphore(int(os.environ.get("EVAL_CONCURRENCY", "3")))

    async def one(item: dict) -> dict:
        async with sem:
            try:
                reply = await _agent_reply(item["input"], f"gen-{item['id']}")
            except Exception as e:  # noqa: BLE001
                print(f"  ! {item['id']} reply generation failed: {type(e).__name__}: {e}")
                reply = ""
            print(f"  · {item['id']} ({item['kind']}) reply generated ({len(reply)} chars)")
            return {
                **item, "coach_reply": reply,
                "gold_had_error": False, "guard_should_skip": False,
            }

    generated = await asyncio.gather(*(one(it) for it in to_gen))
    neg.extend(generated)
    return neg


async def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()
    print(f"Building extraction dataset (agent model for negatives = {AGENT_MODEL})...")
    positives = build_positives()
    print(f"  {len(positives)} positives (coach replies reused from head_to_head)")
    print("  generating realistic coach replies for negatives...")
    negatives = await build_negatives()

    n_specific = sum(1 for p in positives if p["specific_gold"])
    dataset = {
        "meta": {
            "description": "Ground truth for the structured-extraction surface "
            "(extract_and_log_error): had_error detection, category, correction validity.",
            "counts": {
                "positives": len(positives),
                "positives_specific_category": n_specific,
                "negatives": len(negatives),
                "negatives_correct_sentence": sum(1 for n in negatives if n["kind"] == "correct_sentence"),
                "negatives_question": sum(1 for n in negatives if n["kind"] == "question"),
                "negatives_non_chinese": sum(1 for n in negatives if n["kind"] == "non_chinese"),
            },
            "agent_model_for_negative_replies": AGENT_MODEL,
        },
        "positives": positives,
        "negatives": negatives,
    }
    OUT.write_text(json.dumps(dataset, ensure_ascii=False, indent=2))
    print(f"\nWrote {OUT}")
    print(f"  positives {len(positives)} ({n_specific} with a specific-category gold)")
    print(f"  negatives {len(negatives)}")


if __name__ == "__main__":
    asyncio.run(main())
