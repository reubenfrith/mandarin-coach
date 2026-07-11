"""ChromaDB memory layer.

Four collection types:
  - grammar_rules      (shared reference, loaded from data/grammar_rules.json)
  - error_patterns     (shared reference, loaded from data/error_patterns.json)
  - hsk_vocabulary     (shared reference, loaded from data/hsk_vocab.json)
  - {user_id}_personal_errors  (per-user, grows as the learner is corrected)

Reference collections make the app useful on day one; the per-user personal-error
collection is what compounds over time. error_stats() does the deterministic
count/trend aggregation that a naked LLM cannot do reliably at scale — the core
differentiator of this application.

Embeddings default to OpenAI text-embedding-3-small (the documented baseline)
when OPENAI_API_KEY is set, otherwise fall back to ChromaDB's local model so the
app runs without an OpenAI key. Override with EMBEDDING_MODEL=openai|default.
"""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _ROOT / "data"
CHROMA_PATH = os.environ.get("CHROMA_PATH", str(_ROOT / "chroma_db"))

_client = None
_embedding_fn = None


# --------------------------------------------------------------------------- #
# Client + embeddings
# --------------------------------------------------------------------------- #
def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def _valid_key(value: str | None) -> bool:
    """A usable API key: non-empty, not a stray inline comment or placeholder."""
    v = (value or "").strip()
    return bool(v) and not v.startswith("#") and " " not in v


def embedding_name() -> str:
    override = os.environ.get("EMBEDDING_MODEL")
    if override:
        return override
    return "openai" if _valid_key(os.environ.get("OPENAI_API_KEY")) else "default"


def get_embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        if embedding_name() == "openai":
            _embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ["OPENAI_API_KEY"],
                model_name="text-embedding-3-small",
            )
        else:
            _embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    return _embedding_fn


def _collection(name: str):
    return get_client().get_or_create_collection(
        name=name, embedding_function=get_embedding_function()
    )


# --------------------------------------------------------------------------- #
# Reference data: text + metadata builders
# --------------------------------------------------------------------------- #
def _grammar_text(r: dict) -> str:
    return (
        f"{r['name']}. {r['explanation']} "
        f"Common English-speaker mistake: {r['common_mistake']} "
        f"Incorrect: {r['incorrect_example']} Correct: {r['correct_example']}"
    )


def _grammar_meta(r: dict) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "category": r["category"],
        "hsk_level": r["hsk_level"],
        "correct_example": r["correct_example"],
        "keywords": " ".join(r.get("keywords", [])),
    }


def _error_pattern_text(r: dict) -> str:
    return (
        f"{r['error_type']}. {r['why_english_speakers']} "
        f"Incorrect: {r['incorrect']} Correct: {r['correct']} {r['note']}"
    )


def _error_pattern_meta(r: dict) -> dict:
    return {
        "id": r["id"],
        "error_type": r["error_type"],
        "category": r["category"],
        "correct": r["correct"],
        "keywords": " ".join(r.get("keywords", [])),
    }


def _vocab_text(r: dict) -> str:
    return f"{r['word']} ({r['pinyin']}): {r['meaning']}. Example: {r['example']}"


def _vocab_meta(r: dict) -> dict:
    return {
        "id": r["id"],
        "word": r["word"],
        "pinyin": r["pinyin"],
        "meaning": r["meaning"],
        "hsk_level": r["hsk_level"],
        "pos": r["pos"],
    }


REFERENCE_SPECS = {
    "grammar_rules": ("grammar_rules.json", _grammar_text, _grammar_meta),
    "error_patterns": ("error_patterns.json", _error_pattern_text, _error_pattern_meta),
    "hsk_vocabulary": ("hsk_vocab.json", _vocab_text, _vocab_meta),
}


def load_reference_data(force: bool = False) -> dict:
    """Embed and load the three reference collections. Idempotent unless force."""
    summary = {}
    for coll_name, (filename, text_fn, meta_fn) in REFERENCE_SPECS.items():
        col = _collection(coll_name)
        if force and col.count() > 0:
            get_client().delete_collection(coll_name)
            col = _collection(coll_name)
        if col.count() == 0:
            records = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
            col.add(
                ids=[r["id"] for r in records],
                documents=[text_fn(r) for r in records],
                metadatas=[meta_fn(r) for r in records],
            )
        summary[coll_name] = col.count()
    return summary


# --------------------------------------------------------------------------- #
# Query helpers
# --------------------------------------------------------------------------- #
def _format(res: dict) -> list:
    if not res or not res.get("ids") or not res["ids"][0]:
        return []
    out = []
    for i in range(len(res["ids"][0])):
        out.append(
            {
                "id": res["ids"][0][i],
                "document": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i] if res.get("distances") else None,
            }
        )
    return out


def _query(coll_name: str, text: str, n: int, where: dict | None = None) -> list:
    col = _collection(coll_name)
    if col.count() == 0:
        return []
    res = col.query(
        query_texts=[text], n_results=min(n, col.count()), where=where or None
    )
    return _format(res)


def query_grammar_rules(text: str, n: int = 3, where: dict | None = None) -> list:
    return _query("grammar_rules", text, n, where)


def query_error_patterns(text: str, n: int = 3, where: dict | None = None) -> list:
    return _query("error_patterns", text, n, where)


def query_hsk_vocabulary(text: str, n: int = 3, where: dict | None = None) -> list:
    return _query("hsk_vocabulary", text, n, where)


# --------------------------------------------------------------------------- #
# Personal errors: per-user, growing corpus
# --------------------------------------------------------------------------- #
def personal_errors_collection(user_id: str):
    return _collection(f"{user_id}_personal_errors")


def add_personal_error(
    user_id: str,
    original: str,
    correction: str,
    category: str,
    explanation: str = "",
    timestamp: str | None = None,
) -> str:
    col = personal_errors_collection(user_id)
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    doc_id = f"{user_id}_err_{col.count() + 1}"
    text = f"Error ({category}): {original} -> {correction}. {explanation}".strip()
    col.add(
        ids=[doc_id],
        documents=[text],
        metadatas=[
            {
                "user_id": user_id,
                "category": category,
                "original": original,
                "correction": correction,
                "explanation": explanation,
                "timestamp": ts,
            }
        ],
    )
    return doc_id


def query_personal_errors(user_id: str, text: str, n: int = 5) -> list:
    return _query(f"{user_id}_personal_errors", text, n, {"user_id": user_id})


def error_stats(user_id: str) -> dict:
    """Deterministic aggregation over the full personal-error corpus.

    Returns exact totals and per-category counts, plus a simple recent-vs-earlier
    trend per category. This is the database operation a naked LLM approximates
    and fails at scale — the capability the whole app is built around.
    """
    col = personal_errors_collection(user_id)
    if col.count() == 0:
        return {"total": 0, "by_category": {}, "trend": {}}

    data = col.get(include=["metadatas"])
    metas = data["metadatas"]
    metas.sort(key=lambda m: m.get("timestamp", ""))

    counts = Counter(m["category"] for m in metas)
    half = len(metas) // 2
    earlier = Counter(m["category"] for m in metas[:half])
    recent = Counter(m["category"] for m in metas[half:])

    trend = {}
    for cat in counts:
        delta = recent[cat] - earlier[cat]
        trend[cat] = "increasing" if delta > 0 else "decreasing" if delta < 0 else "steady"

    return {
        "total": len(metas),
        "by_category": dict(counts.most_common()),
        "trend": trend,
    }
