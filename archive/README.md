# archive/

Dead code from before the **custom-UI pivot** (commit `33d9246`). The app used to be
a [Chainlit](https://chainlit.io) chat app; it now runs a hand-rolled FastAPI + static
single-page UI (`app/server.py` serving `app/web_ui/`). None of the files here are
imported or served at runtime — production boots `uvicorn app.server:app`, which has no
Chainlit dependency.

Kept for reference only; safe to delete outright.

| Archived path | Was | Why dead |
|---|---|---|
| `app-main.py` | `app/main.py` | The Chainlit entry point (`@cl.password_auth_callback`, `on_message`, …). Replaced by `app/server.py` + `app/web_api.py` + `app/web_ui/`. |
| `app-chainlit/config.toml` | `app/.chainlit/config.toml` | Chainlit UI config. Unused — no Chainlit server runs. |
| `root-chainlit/config.toml` | `.chainlit/config.toml` | Ditto (repo-root copy). |
| `app-public/` | `app/public/` | Chainlit theme assets (`theme.json`, `stylesheet.css`, `help.html`). The custom UI styles itself in `app/web_ui/style.css`. |
| `root-public/` | `public/` | Ditto (repo-root copy; was never even copied into the Docker image). |

## Loose ends

- **`chainlit` dependency removed.** Dropped from `pyproject.toml` and re-locked
  (`uv lock` also pruned ~40 transitive-only deps); nothing imported it. Its default
  `chainlit.md` welcome file and the stale `.chainlit/*` `.gitignore` rules went with it.
- `CHAINLIT_AUTH_SECRET` is **still live** — the FastAPI app reuses that env var name as its
  JWT signing secret (`app/web_api.py`). It is *not* Chainlit and must stay.
