"""Shared eval bootstrap.

Import this FIRST in every eval script — before importing any app module —
because it (1) loads secrets from .env, (2) redirects ChromaDB to an isolated
eval directory so eval seeding never touches the real user corpus, and (3) puts
app/ on sys.path (the app modules import each other flatly, e.g. `import memory`).
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Isolate every eval ChromaDB write from the real /var/data (or local) corpus.
# Must be set before `import memory`, which reads CHROMA_PATH at module load.
EVAL_CHROMA = ROOT / "evals" / ".eval_chroma"
os.environ["CHROMA_PATH"] = str(EVAL_CHROMA)

# Send eval-run traces to their own LangSmith project so the many judge/agent calls
# from evaluation don't drown the production coaching traces in "mandarin-coach".
# Set here (before app import) so config.py's setdefault leaves it untouched.
os.environ.setdefault("LANGSMITH_PROJECT", "mandarin-coach-evals")

# app/ modules import each other by bare name (import memory, from config import ...)
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# --------------------------------------------------------------------------- #
# RAGAS import shim
# --------------------------------------------------------------------------- #
# ragas 0.4.3 hard-imports `langchain_community.chat_models.vertexai.ChatVertexAI`
# (and `langchain_community.llms.VertexAI`), but langchain-community 0.4.2 deleted
# those. We evaluate with gpt-4o-mini, never Vertex, so the classes are never
# instantiated — we only need the import to resolve. Stub the missing symbols so
# `import ragas` works WITHOUT touching the app's pinned langchain/langgraph
# versions (this app is live; a dependency bump could break the deployed agent).
# Must run before any `import ragas`.
import types as _types  # noqa: E402

try:  # add the deleted submodule + attribute so ragas' `from ... import ChatVertexAI` resolves
    import langchain_community.chat_models as _lc_cm  # noqa: E402

    if not hasattr(_lc_cm, "vertexai"):
        _vx = _types.ModuleType("langchain_community.chat_models.vertexai")
        _vx.ChatVertexAI = object
        sys.modules["langchain_community.chat_models.vertexai"] = _vx
        _lc_cm.vertexai = _vx
    import langchain_community.llms as _lc_llms  # noqa: E402

    if not hasattr(_lc_llms, "VertexAI"):
        _lc_llms.VertexAI = object
except Exception:  # langchain_community absent entirely — nothing to shim
    pass
