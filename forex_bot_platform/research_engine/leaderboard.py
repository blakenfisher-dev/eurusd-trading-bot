"""Leaderboard IO utilities (safe file handling)."""
import os
import json
import tempfile

def save_leaderboard(entries, path: str = None):
    if path is None:
        fd, path = tempfile.mkstemp(prefix="leaderboard_", suffix=".json")
        os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    return path
