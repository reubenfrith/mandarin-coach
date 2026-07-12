"""Simple username/password user store with profiles.

Persistent SQLite (lives on the same durable volume as ChromaDB). Passwords are
salted + PBKDF2-hashed. First login for an unknown username auto-creates the
account, so users are self-service. Each user's username becomes their ChromaDB
namespace, so every user gets a separate error corpus.
"""
import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
USER_DB_PATH = os.environ.get("USER_DB_PATH", str(_ROOT / "user_data" / "users.db"))
_ITERS = 200_000


def _conn():
    Path(USER_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(USER_DB_PATH)


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                hsk_level     TEXT,
                created_at    TEXT NOT NULL
            )"""
        )


def _hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERS)
    return f"pbkdf2_sha256${_ITERS}${salt.hex()}${dk.hex()}"


def _verify(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return dk.hex() == hash_hex
    except Exception:
        return False


def verify_or_create(username: str, password: str) -> bool:
    """True if credentials match an existing user, or a new account was created."""
    username = (username or "").strip().lower()
    if len(username) < 2 or not password:
        return False
    with _conn() as c:
        row = c.execute(
            "SELECT password_hash FROM users WHERE username=?", (username,)
        ).fetchone()
        if row is None:
            c.execute(
                "INSERT INTO users (username, password_hash, hsk_level, created_at) "
                "VALUES (?,?,?,?)",
                (username, _hash(password), None, datetime.now(timezone.utc).isoformat()),
            )
            return True
        return _verify(password, row[0])


def get_profile(username: str) -> dict | None:
    username = (username or "").strip().lower()
    with _conn() as c:
        row = c.execute(
            "SELECT username, hsk_level, created_at FROM users WHERE username=?",
            (username,),
        ).fetchone()
    if not row:
        return None
    return {"username": row[0], "hsk_level": row[1], "created_at": row[2]}


def set_hsk_level(username: str, hsk_level: str):
    username = (username or "").strip().lower()
    with _conn() as c:
        c.execute("UPDATE users SET hsk_level=? WHERE username=?", (hsk_level, username))
