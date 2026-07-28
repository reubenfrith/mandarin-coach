"""Pytest bootstrap for the standalone-script tests.

Every test here is *also* runnable directly (`uv run python tests/test_x.py`); this file adds
only what pytest needs to collect them and run them SAFELY in one shared process:

  1. Isolates ChromaDB to a throwaway temp dir, so a test that logs an error (the pronounce
     surfaces write through memory.add_personal_error) never touches the real ./chroma_db
     corpus. Must be set BEFORE any `import memory`, which reads CHROMA_PATH at first client
     use — so it lives at conftest import time, which pytest runs before collecting tests.
  2. Sets the env the app modules expect: local (no-network) embeddings + a dummy secret for
     the auth-cookie signer.
  3. Puts app/ and the repo root on sys.path — app modules import each other by bare name
     (`import memory`), and `app.server` imports as a namespace package from the root.

Each test file exposes a thin `test_*` wrapper around its `main()` so pytest collects one
case per file; the hand-rolled `check()` assertions inside still do the real work. Standalone
runs skip this file entirely and set the same env for themselves.
"""
import atexit
import os
import pathlib
import shutil
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parents[1]

# 1. Isolate the corpus before any app import (memory.py reads CHROMA_PATH lazily).
_chroma = tempfile.mkdtemp(prefix="mc_test_chroma_")
os.environ["CHROMA_PATH"] = _chroma
atexit.register(lambda: shutil.rmtree(_chroma, ignore_errors=True))

# 2. App env: local embeddings (no network) + a dummy auth secret for the cookie signer.
os.environ.setdefault("EMBEDDING_MODEL", "default")
os.environ.setdefault("CHAINLIT_AUTH_SECRET", "test-secret-please-ignore-000000")

# 3. Import paths: app/ for bare-name imports, root for `import app.server`.
for _p in (str(_ROOT / "app"), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
