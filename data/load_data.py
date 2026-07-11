"""Load the reference JSON data into ChromaDB.

Usage:
    uv run python data/load_data.py          # load if empty
    uv run python data/load_data.py --force  # rebuild all reference collections

Run once before starting the app (or the app will lazy-load on first query).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from dotenv import load_dotenv

import memory

load_dotenv()

if __name__ == "__main__":
    force = "--force" in sys.argv
    print(f"Embedding model: {memory.embedding_name()}")
    print(f"Chroma path:     {memory.CHROMA_PATH}")
    print("Loading reference data..." + (" (force rebuild)" if force else ""))
    counts = memory.load_reference_data(force=force)
    for name, n in counts.items():
        print(f"  {name}: {n} documents")
    print("Done.")
