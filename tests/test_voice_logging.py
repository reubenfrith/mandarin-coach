"""Deterministic checks for the voice error-logging path in app/agent.py.

Same no-network approach as test_extraction_guard.py: stub `_extract_record` (the
structured-extraction call) and `memory.add_personal_error` (the corpus write).
Verifies the voice-specific behaviour layered on top of the shared guard:

  * a low-confidence STT turn is skipped BEFORE any extraction call (corpus stays clean);
  * a high-confidence turn runs the normal guard and logs tagged source="voice";
  * a turn with NO confidence signal still logs (tag + guard remain the protection);
  * the shared guard still applies (non-Chinese short-circuits; incomplete → nothing).

Run:  uv run python tests/test_voice_logging.py   (exit 0 = all passed)
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import agent  # noqa: E402
from agent import ErrorExtraction, VOICE_MIN_STT_CONFIDENCE  # noqa: E402

CH = "我昨天去商店买东西了的"
COMPLETE = ErrorExtraction(
    had_error=True, original=CH, correction="我昨天去商店买东西了",
    category="particle", explanation="stray 的",
)


class _Harness:
    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.logged = []  # captures the source kwarg too

    async def _extract(self, user_input, agent_answer, model=None):
        outcome = self.script[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def _log(self, user_id, original, correction, category, explanation="", timestamp=None, source="text"):
        self.logged.append(dict(original=original, category=category, source=source))

    def __enter__(self):
        self._oe, self._ol = agent._extract_record, agent.memory.add_personal_error
        agent._extract_record = self._extract
        agent.memory.add_personal_error = self._log
        return self

    def __exit__(self, *a):
        agent._extract_record, agent.memory.add_personal_error = self._oe, self._ol


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


async def main():
    low = VOICE_MIN_STT_CONFIDENCE - 0.1
    high = VOICE_MIN_STT_CONFIDENCE + 0.1

    # 1. Low confidence → skipped before any extraction, nothing logged.
    with _Harness([COMPLETE]) as h:
        res = await agent.extract_and_log_error_voice("u", CH, "reply", confidence=low)
        check("low-confidence turn skipped", res is None)
        check("  ...no extraction call", h.calls == 0)
        check("  ...corpus untouched", h.logged == [])

    # 2. High confidence → runs guard, logs tagged source="voice".
    with _Harness([COMPLETE]) as h:
        res = await agent.extract_and_log_error_voice("u", CH, "reply", confidence=high)
        check("high-confidence turn logs", res is not None and res["category"] == "particle")
        check("  ...tagged source=voice", len(h.logged) == 1 and h.logged[0]["source"] == "voice")

    # 3. No confidence signal → still logs (tag + guard are the protection).
    with _Harness([COMPLETE]) as h:
        res = await agent.extract_and_log_error_voice("u", CH, "reply", confidence=None)
        check("no-confidence turn still logs", res is not None)
        check("  ...tagged source=voice", h.logged[0]["source"] == "voice")

    # 4. Shared guard intact: non-Chinese short-circuits even at high confidence.
    with _Harness([COMPLETE]) as h:
        res = await agent.extract_and_log_error_voice("u", "hello there", "reply", confidence=high)
        check("non-Chinese short-circuits", res is None and h.calls == 0)

    # 5. Shared guard intact: clean sentence trusted, nothing logged.
    with _Harness([ErrorExtraction(had_error=False)]) as h:
        res = await agent.extract_and_log_error_voice("u", CH, "reply", confidence=high)
        check("clean sentence logs nothing", res is None and h.logged == [])

    print("\nAll voice-logging checks passed.")


def test_voice_logging():
    """pytest entry point — runs the async check sequence (see conftest.py)."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
