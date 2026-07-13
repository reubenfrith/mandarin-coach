"""Deterministic checks for the post-turn extraction guard in app/agent.py.

Runs the retry / field-validation / fail-safe control flow without any network
call by stubbing `_extract_record` (the single structured-extraction call) and
`memory.add_personal_error` (the corpus write). Verifies DECISIONS #13:

  * a dropped-field record is RETRIED until a complete one arrives, then logged;
  * a malformed call (raises) is RETRIED;
  * a confident had_error=False is trusted immediately (no retry, no log);
  * if no complete record is ever obtained, NOTHING is logged (fail safe);
  * non-Chinese input short-circuits before any extraction call.

Run:  uv run python tests/test_extraction_guard.py   (exit 0 = all passed)
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import agent  # noqa: E402
from agent import ErrorExtraction, EXTRACTION_MAX_ATTEMPTS  # noqa: E402

CH = "她把书被他借走了"  # contains Chinese → passes the _has_chinese gate


def _err(*, had_error=True, original="", correction="", category="", explanation=""):
    return ErrorExtraction(
        had_error=had_error, original=original, correction=correction,
        category=category, explanation=explanation,
    )


COMPLETE = _err(original=CH, correction="他把书借走了", category="particle", explanation="把/被 conflict")
DROPPED = _err(original=CH)  # had_error=True but correction/category dropped
CLEAN = _err(had_error=False)


class _Harness:
    """Installs a scripted sequence of _extract_record outcomes and records logs."""

    def __init__(self, script):
        self.script = list(script)  # each item: an ErrorExtraction OR an Exception to raise
        self.calls = 0
        self.logged = []

    async def _extract(self, user_input, agent_answer, model=None):
        outcome = self.script[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def _log(self, user_id, original, correction, category, explanation):
        self.logged.append(dict(original=original, correction=correction, category=category))

    def __enter__(self):
        self._orig_extract = agent._extract_record
        self._orig_log = agent.memory.add_personal_error
        agent._extract_record = self._extract
        agent.memory.add_personal_error = self._log
        return self

    def __exit__(self, *a):
        agent._extract_record = self._orig_extract
        agent.memory.add_personal_error = self._orig_log


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


async def main():
    assert EXTRACTION_MAX_ATTEMPTS >= 2, "test assumes >=2 attempts"

    # 1. Dropped fields on attempt 1, complete on attempt 2 → logs the complete record.
    with _Harness([DROPPED, COMPLETE]) as h:
        res = await agent.extract_and_log_error("u", CH, "coach reply")
        check("retry recovers a dropped-field record", res is not None and res["correction"] == "他把书借走了")
        check("  ...after exactly 2 calls", h.calls == 2)
        check("  ...and logs exactly one record", len(h.logged) == 1)

    # 2. Malformed (raises) on attempt 1, complete on attempt 2 → retried, then logs.
    with _Harness([ValueError("null field"), COMPLETE]) as h:
        res = await agent.extract_and_log_error("u", CH, "r")
        check("retry recovers from a malformed/raising call", res is not None)
        check("  ...after exactly 2 calls", h.calls == 2)

    # 3. Confident clean sentence → trusted immediately, no retry, no log.
    with _Harness([CLEAN, COMPLETE]) as h:
        res = await agent.extract_and_log_error("u", CH, "r")
        check("had_error=False trusted on first call", res is None)
        check("  ...no retry (exactly 1 call)", h.calls == 1)
        check("  ...nothing logged", h.logged == [])

    # 4. Never complete across all attempts → fail safe (log nothing).
    with _Harness([DROPPED] * EXTRACTION_MAX_ATTEMPTS) as h:
        res = await agent.extract_and_log_error("u", CH, "r")
        check("all-incomplete → fail safe, returns None", res is None)
        check(f"  ...exhausts all {EXTRACTION_MAX_ATTEMPTS} attempts", h.calls == EXTRACTION_MAX_ATTEMPTS)
        check("  ...corpus never written", h.logged == [])

    # 5. Every attempt raises → fail safe (log nothing).
    with _Harness([RuntimeError("hang")] * EXTRACTION_MAX_ATTEMPTS) as h:
        res = await agent.extract_and_log_error("u", CH, "r")
        check("all-raising → fail safe, returns None", res is None)
        check("  ...corpus never written", h.logged == [])

    # 6. Non-Chinese input → short-circuits before any extraction call.
    with _Harness([COMPLETE]) as h:
        res = await agent.extract_and_log_error("u", "how are you?", "r")
        check("non-Chinese input short-circuits", res is None and h.calls == 0)

    # 7. Invalid category falls back to 'grammar' (unchanged behaviour, still guarded).
    with _Harness([_err(original=CH, correction="x", category="bogus")]) as h:
        res = await agent.extract_and_log_error("u", CH, "r")
        check("invalid category normalised to 'grammar'", res is not None and res["category"] == "grammar")

    print("\nAll extraction-guard checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
