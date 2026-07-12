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

# app/ modules import each other by bare name (import memory, from config import ...)
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
