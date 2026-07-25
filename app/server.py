"""Top-level FastAPI entrypoint: the unified web app (text coach + voice partner).

Replaces the Chainlit interface entirely with one custom UI, one auth system, and
one backend process — so there is a single ChromaDB writer and a single user-DB
owner. BARE imports + `sys.path.insert` keep one shared module graph (memory's
client/embedding singletons must be one object process-wide).

Run:  uvicorn app.server:app --host 0.0.0.0 --port 8000
  - UI (login + text coach + voice):  /
  - APIs:  /api/*  (see web_api.py and voice_api.py)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))  # BEFORE bare imports — shared module graph

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import memory  # noqa: E402
import users  # noqa: E402
from pronounce_api import router as pronounce_router  # noqa: E402
from voice_api import router as voice_router  # noqa: E402
from web_api import router as web_router  # noqa: E402

load_dotenv()

_UI_DIR = os.path.join(os.path.dirname(__file__), "web_ui")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    users.init_db()
    memory.load_reference_data()  # idempotent: only embeds if the collections are empty
    yield


app = FastAPI(title="Mandarin Coach — text + voice", lifespan=lifespan)

# API routes first, so they win over the catch-all static mount below.
app.include_router(web_router)
app.include_router(voice_router)
app.include_router(pronounce_router)

# The single-page UI at "/" (login, text coach, voice partner). Mounted LAST.
app.mount("/", StaticFiles(directory=_UI_DIR, html=True), name="ui")
