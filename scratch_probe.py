"""Throwaway: verify user store + per-user Chroma namespacing."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))
os.environ["USER_DB_PATH"] = "/tmp/mc_test_users.db"
Path("/tmp/mc_test_users.db").unlink(missing_ok=True)
from dotenv import load_dotenv

load_dotenv()
import memory
import users

users.init_db()

print("=== auth store ===")
print("new user create:", users.verify_or_create("Alice", "pw123"))   # True (created)
print("correct pw:     ", users.verify_or_create("alice", "pw123"))   # True
print("wrong pw:       ", users.verify_or_create("alice", "nope"))    # False
print("too short user: ", users.verify_or_create("a", "pw"))          # False
print("profile:        ", users.get_profile("alice"))
users.set_hsk_level("alice", "HSK 3-4")
print("after set hsk:  ", users.get_profile("alice"))

print("\n=== per-user namespacing ===")
for u in ["alice", "bob.smith", "carol"]:
    try:
        memory.get_client().delete_collection(memory._safe_ns(u) + "_personal_errors")
    except Exception:
        pass
memory.add_personal_error("alice", "我买了三书。", "我买了三本书。", "measure_word", "x")
memory.add_personal_error("bob.smith", "他比我很高。", "他比我高。", "grammar", "x")
print("alice ns  :", memory._safe_ns("alice"), "| stats:", memory.error_stats("alice"))
print("bob.smith :", memory._safe_ns("bob.smith"), "| stats:", memory.error_stats("bob.smith"))
print("carol     :", "stats:", memory.error_stats("carol"))  # empty, isolated
