"""Task 6 retrieval sweep — Axis 1 (embedding) × Axis 2 (technique) over the grammar
corpus, scored on FRESH non-circular queries (evals/datagen/retrieval_queries.json).

Configurations (see README Task 3 "Retrieval Strategies"):
  - baseline          OpenAI text-embedding-3-small, dense (the production default)
  - bge_m3            BAAI/bge-m3 (local, Chinese-native), dense              [Axis 1]
  - hybrid            BM25 (jieba CJK tokens) + OpenAI dense, RRF fusion      [Axis 2]

Qwen3-Embedding-8B (the other Axis-1 candidate) is NOT run here: at ~8B params it
needs a dedicated GPU endpoint and will not run on the build machine. It is reported
as an infra constraint, not a result.

Metrics are DETERMINISTIC (exact gold rule-id match) — no LLM judge, so the sweep is
cheap and fully reproducible:
  recall@1 / @3 / @5, MRR, plus per-query retrieval LATENCY (mean / p50 / p95).

Why deterministic-only: retrieval quality has an objective ground truth here (which
rule the query is about), so an LLM judge would only add noise. Latency is wall-clock
per query and includes each backend's real per-query cost — OpenAI includes the
embedding API round-trip; BGE-M3 is local CPU compute with no per-call fee — which is
exactly the trade the choice comes down to once quality is close.

Run (needs the task6 extra — `uv sync --extra task6`):
  uv run python evals/surfaces/retrieval_sweep.py
  uv run python evals/surfaces/retrieval_sweep.py --configs baseline,hybrid
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # evals/ on path
from lib import _env  # noqa: E402,F401  — bootstrap: .env, app path, chroma, ragas shim

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

import memory  # noqa: E402  (app module — same _grammar_text used in production)

CORPUS = _env.APP_DATA / "grammar_rules.json"
QUERIES = _env.DATAGEN / "retrieval_queries.json"
RESULTS = _env.RESULTS
RRF_K = 60          # standard reciprocal-rank-fusion constant
KS = (1, 3, 5)      # recall@k depths reported


# --------------------------------------------------------------------------- #
# Corpus + queries
# --------------------------------------------------------------------------- #
def load_corpus():
    rules = json.loads(CORPUS.read_text(encoding="utf-8"))
    ids = [r["id"] for r in rules]
    docs = [memory._grammar_text(r) for r in rules]  # identical text to production embedding
    return ids, docs


def load_queries():
    return json.loads(QUERIES.read_text(encoding="utf-8"))["queries"]


# --------------------------------------------------------------------------- #
# Embedding backends (each returns L2-normalised row vectors)
# --------------------------------------------------------------------------- #
class OpenAIEmbedder:
    name = "openai/text-embedding-3-small"

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = "text-embedding-3-small"

    def encode(self, texts):
        resp = self._client.embeddings.create(model=self._model, input=list(texts))
        return _normalise(np.array([d.embedding for d in resp.data], dtype=np.float32))


class BGEEmbedder:
    name = "BAAI/bge-m3"

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("BAAI/bge-m3")

    def encode(self, texts):
        v = self._model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(v, dtype=np.float32)


def _normalise(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return m / n


# --------------------------------------------------------------------------- #
# Rankers — each returns a full ranked list of doc-ids for a query
# --------------------------------------------------------------------------- #
class DenseRanker:
    def __init__(self, embedder, ids, docs):
        self.embedder, self.ids = embedder, ids
        self.doc_mat = embedder.encode(docs)  # setup cost, not timed

    def rank(self, query: str):
        qv = self.embedder.encode([query])[0]
        sims = self.doc_mat @ qv
        order = np.argsort(-sims)
        return [self.ids[i] for i in order]


class BM25Ranker:
    def __init__(self, ids, docs):
        import jieba
        from rank_bm25 import BM25Okapi
        self.ids = ids
        self._tok = lambda s: [t for t in jieba.cut(s) if t.strip()]
        self._bm25 = BM25Okapi([self._tok(d) for d in docs])

    def rank(self, query: str):
        scores = self._bm25.get_scores(self._tok(query))
        order = np.argsort(-scores)
        return [self.ids[i] for i in order]


class HybridRRFRanker:
    """Reciprocal-rank fusion of a dense and a sparse ranker (rank-only, so the two
    incompatible score scales never have to be reconciled)."""
    def __init__(self, dense: DenseRanker, sparse: BM25Ranker):
        self.dense, self.sparse = dense, sparse

    def rank(self, query: str):
        fused = {}
        for r in (self.dense.rank(query), self.sparse.rank(query)):
            for pos, doc_id in enumerate(r):
                fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (RRF_K + pos + 1)
        return sorted(fused, key=lambda d: -fused[d])


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def gold_rank(ranked_ids, gold):
    return ranked_ids.index(gold) + 1 if gold in ranked_ids else None


def run_config(name: str, ranker, queries: list[dict]) -> dict:
    rows, latencies = [], []
    for q in queries:
        t0 = time.perf_counter()
        ranked = ranker.rank(q["query"])
        dt_ms = (time.perf_counter() - t0) * 1000
        latencies.append(dt_ms)
        rank = gold_rank(ranked, q["expected_rule_id"])
        rows.append({"id": q["id"], "cluster": q["cluster"], "query": q["query"],
                     "expected_rule_id": q["expected_rule_id"], "rank": rank,
                     "top3": ranked[:3], "latency_ms": round(dt_ms, 1)})
        print(f"  [{name}] {q['id']} {q['cluster']:11} rank={rank} {round(dt_ms)}ms")
    n = len(rows)
    ranks = [r["rank"] for r in rows]
    recall = {f"recall@{k}": sum(1 for r in ranks if r and r <= k) / n for k in KS}
    mrr = sum((1.0 / r if r else 0.0) for r in ranks) / n
    lat_sorted = sorted(latencies)
    summary = {
        "config": name, "n": n, **{k: round(v, 3) for k, v in recall.items()},
        "mrr": round(mrr, 3),
        "latency_ms": {
            "mean": round(sum(latencies) / n, 1),
            "p50": round(lat_sorted[n // 2], 1),
            "p95": round(lat_sorted[min(int(n * 0.95), n - 1)], 1),
        },
    }
    return {"summary": summary, "rows": rows}


# --------------------------------------------------------------------------- #
# Build configs (skips a config with a clear note if its backend is unavailable)
# --------------------------------------------------------------------------- #
def build_rankers(wanted: list[str], ids, docs):
    built, skipped = {}, {}
    openai_dense = None
    if "baseline" in wanted or "hybrid" in wanted:
        try:
            openai_dense = DenseRanker(OpenAIEmbedder(), ids, docs)
            if "baseline" in wanted:
                built["baseline"] = openai_dense
        except Exception as e:  # noqa: BLE001
            skipped["baseline"] = f"{type(e).__name__}: {e}"
    if "bge_m3" in wanted:
        try:
            built["bge_m3"] = DenseRanker(BGEEmbedder(), ids, docs)
        except Exception as e:  # noqa: BLE001
            skipped["bge_m3"] = f"{type(e).__name__}: {e} (install: uv sync --extra task6)"
    if "hybrid" in wanted:
        try:
            bm25 = BM25Ranker(ids, docs)
            if openai_dense is None:
                openai_dense = DenseRanker(OpenAIEmbedder(), ids, docs)
            built["hybrid"] = HybridRRFRanker(openai_dense, bm25)
        except Exception as e:  # noqa: BLE001
            skipped["hybrid"] = f"{type(e).__name__}: {e} (install: uv sync --extra task6)"
    return built, skipped


def render_md(results: list[dict], skipped: dict, n_queries: int) -> str:
    def fmt(v): return f"{v:.3f}"
    lines = [
        "# Task 6.1 — Retrieval sweep",
        f"\n{n_queries} fresh non-circular queries over the 98-rule grammar corpus. "
        "Deterministic exact gold rule-id match (no LLM judge). Higher recall/MRR is better; "
        "lower latency is better.\n",
        "| Config | recall@1 | recall@3 | recall@5 | MRR | latency p50 (ms) | latency p95 (ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        s = r["summary"]
        lines.append(
            f"| {s['config']} | {fmt(s['recall@1'])} | {fmt(s['recall@3'])} | {fmt(s['recall@5'])} "
            f"| {fmt(s['mrr'])} | {s['latency_ms']['p50']} | {s['latency_ms']['p95']} |"
        )
    lines.append(
        "\n> **baseline** = OpenAI text-embedding-3-small, dense (production default). "
        "**bge_m3** = BAAI/bge-m3 local dense (Axis 1). **hybrid** = BM25 (jieba) + OpenAI dense, "
        "RRF (Axis 2). **Qwen3-Embedding-8B** (Axis 1) was not run — ~8B params needs a dedicated "
        "GPU endpoint, out of scope for the build machine."
    )
    lines.append(
        "\n> Latency note: OpenAI figures include the embedding-API round-trip (network); BGE-M3 is "
        "local CPU encode with no per-call fee. That is the real per-query trade once quality is close."
    )
    if skipped:
        lines.append("\n### Skipped configs")
        for k, v in skipped.items():
            lines.append(f"- **{k}**: {v}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="baseline,bge_m3,hybrid",
                    help="comma list of: baseline, bge_m3, hybrid")
    ap.add_argument("--limit", type=int, default=None, help="only first N queries")
    args = ap.parse_args()

    wanted = [c.strip() for c in args.configs.split(",") if c.strip()]
    ids, docs = load_corpus()
    queries = load_queries()
    if args.limit:
        queries = queries[: args.limit]
    print(f"Retrieval sweep: {len(queries)} queries, {len(ids)} rules, configs={wanted}\n")

    rankers, skipped = build_rankers(wanted, ids, docs)
    results = []
    for name in wanted:
        if name in rankers:
            print(f"--- {name} ---")
            results.append(run_config(name, rankers[name], queries))
    if skipped:
        print(f"\n! skipped: {skipped}")

    RESULTS.mkdir(exist_ok=True)
    out = {"queries": len(queries), "configs": [r["summary"] for r in results],
           "skipped": skipped, "detail": {r["summary"]["config"]: r["rows"] for r in results}}
    (RESULTS / "retrieval_sweep.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    md = render_md(results, skipped, len(queries))
    (RESULTS / "retrieval_sweep.md").write_text(md + "\n")
    print("\n" + md)
    print(f"\nWrote {RESULTS/'retrieval_sweep.md'} and .json")


if __name__ == "__main__":
    main()
