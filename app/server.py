"""Top-level FastAPI entrypoint: the voice Conversation Partner + the Chainlit text coach
in ONE process.

Single process on purpose: `memory.py` caches the ChromaDB client as a module-level
singleton, so one process = one writer for the corpus and the user DB. That dedup only
holds if this file and `app/main.py` resolve `import memory` to the SAME module object,
which requires `app/` on `sys.path` and BARE imports everywhere (never `app.memory`).
The `sys.path.insert` below matches what `main.py` already does, so both entrypoints
share one module graph.

Run:  uvicorn app.server:app --host 0.0.0.0 --port 8000
  - text coach:  /            (Chainlit, URL unchanged from before)
  - voice UI:    /voice
  - voice APIs:  /voice/login, /voice/log-turn, /voice/pinyin, /realtime/session
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))  # BEFORE bare imports — shared module graph

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from chainlit.utils import mount_chainlit

import users  # noqa: E402 — must follow the sys.path.insert above
from voice_api import router as voice_router  # noqa: E402

load_dotenv()
users.init_db()

_UI_DIR = os.path.join(os.path.dirname(__file__), "voice_ui")

app = FastAPI(title="Mandarin Coach — voice + text")

# Register the specific voice routes and static UI FIRST, so they win over the
# Chainlit sub-app, which is mounted at the catch-all root path below.
app.include_router(voice_router)
app.mount("/voice", StaticFiles(directory=_UI_DIR, html=True), name="voice-ui")

# Text coach stays at "/" so its URL is unchanged. Mounted LAST (catch-all).
mount_chainlit(app=app, target="app/main.py", path="/")
