"""C_scale thesis preflight — the ONE check that decides the whole head-to-head.

Seeds ~60 mixed-category error records for an isolated eval user, then asks a hard
aggregation question two ways:

  1. Through the real LangGraph agent — and verifies the error_pattern_analyser
     (deterministic error_stats) tool actually FIRES. If it doesn't, the agent
     degrades to the same free-form reasoning as the naked LLM => false parity.
  2. Through a naked-LLM control arm given ALL 60 records in context plus a strong
     counting prompt (the fair baseline).

Prints ground truth vs both answers so we can see, on day one, whether C_scale
discriminates. Run:  uv run python evals/surfaces/preflight_typec.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import asyncio  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

import memory  # noqa: E402
from agent import answer_text, build_agent  # noqa: E402
from config import DEFAULT_MODEL, get_llm  # noqa: E402
from datagen.seed_data import TYPEC_EXPECTED, build_typec_corpus  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

USER = "eval_typec_preflight"

QUERY = (
    "Look over my entire error history and give me a precise summary. "
    "How many mistakes have I logged in total? Break it down by category with the "
    "exact count for each. Which category is my single most frequent? And for each "
    "category, tell me whether it is increasing or decreasing recently."
)

NAKED_SYSTEM = (
    "You are a meticulous Mandarin learning analyst. You will be given a learner's "
    "COMPLETE error log. Answer counting and trend questions with exact numbers — "
    "count carefully, do not estimate or round. For trends, compare the more recent "
    "half of the log against the earlier half."
)


def reset_user():
    """Drop any collection from a previous run so seeding is idempotent."""
    name = f"{memory._safe_ns(USER)}_personal_errors"
    try:
        memory.get_client().delete_collection(name)
    except Exception:
        pass


def seed(records: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc)
    stamped = []
    for r in records:
        ts = (now - timedelta(days=r["days_ago"])).isoformat()
        memory.add_personal_error(
            USER, r["original"], r["correction"], r["category"], r["explanation"], ts
        )
        stamped.append({**r, "date": (now - timedelta(days=r["days_ago"])).date().isoformat()})
    return stamped


def naked_log(stamped: list[dict]) -> str:
    lines = [
        f"{i+1}. [{r['date']}] category={r['category']}: "
        f"\"{r['original']}\" -> \"{r['correction']}\""
        for i, r in enumerate(stamped)
    ]
    return "\n".join(lines)


async def run_agent_capturing(user_input: str):
    """Invoke the agent directly so we can inspect which tools fired."""
    graph = build_agent(USER)
    config = {"configurable": {"thread_id": "preflight"}}
    result = await graph.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    msgs = result["messages"]
    tools_fired = [
        tc["name"]
        for m in msgs
        for tc in (getattr(m, "tool_calls", None) or [])
    ]
    return answer_text(msgs[-1].content), tools_fired


def run_naked(user_input: str, stamped: list[dict]) -> str:
    llm = get_llm(streaming=False)
    prompt = f"Here is my complete error log:\n\n{naked_log(stamped)}\n\nQuestion: {user_input}"
    resp = llm.invoke([SystemMessage(content=NAKED_SYSTEM), HumanMessage(content=prompt)])
    return answer_text(resp.content)


async def main():
    print(f"Model under test: {DEFAULT_MODEL}   embeddings: {memory.embedding_name()}\n")

    reset_user()
    stamped = seed(build_typec_corpus())

    stats = memory.error_stats(USER)
    print("=" * 70)
    print("GROUND TRUTH (deterministic error_stats over the seeded corpus)")
    print("=" * 70)
    print(f"total = {stats['total']}   (expected {TYPEC_EXPECTED['total']})")
    print(f"by_category = {stats['by_category']}")
    print(f"trend       = {stats['trend']}")
    assert stats["by_category"] == TYPEC_EXPECTED["by_category"], "seed corpus drifted!"
    assert stats["trend"] == TYPEC_EXPECTED["trend"], "trend drifted!"
    print("(seed matches expected ground truth ✓)\n")

    print("=" * 70)
    print("AGENT ARM (LangGraph + tools)")
    print("=" * 70)
    agent_answer, tools_fired = await run_agent_capturing(QUERY)
    print(f"tools fired: {tools_fired}")
    fired = "error_pattern_analyser" in tools_fired
    print(f"error_pattern_analyser fired: {'YES ✓' if fired else 'NO ✗  <-- FALSE PARITY RISK'}\n")
    print(agent_answer)

    print("\n" + "=" * 70)
    print("NAKED-LLM CONTROL ARM (all 60 records in context, strong counting prompt)")
    print("=" * 70)
    naked_answer = run_naked(QUERY, stamped)
    print(naked_answer)


if __name__ == "__main__":
    asyncio.run(main())
