"""
score_db.py — Persistent personal-best leaderboard for RhythmType.

Scores are saved to scores.json at the project root.
Each entry is keyed by  "{song_title}::{diff_name}"  and stores the
best result per (song, difficulty) pair.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any

_BASE_DIR = Path(__file__).resolve().parent.parent
_SCORES_FILE = _BASE_DIR / "scores.json"

# In-memory cache so repeated reads hit dict, not disk
_cache: Dict[str, Any] = {}
_loaded = False


def _load() -> None:
    global _cache, _loaded
    if _loaded:
        return
    if _SCORES_FILE.exists():
        try:
            with open(_SCORES_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
    _loaded = True


def _save() -> None:
    try:
        with open(_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, indent=2)
    except Exception as e:
        print(f"[ScoreDB] Warning: could not save scores: {e}")


def _key(song_title: str, diff_name: str) -> str:
    return f"{song_title}::{diff_name}"


def get_best(song_title: str, diff_name: str) -> Optional[Dict[str, Any]]:
    """Return the saved personal-best entry, or None if not set."""
    _load()
    return _cache.get(_key(song_title, diff_name))


def submit(
    song_title: str,
    diff_name: str,
    score: float,
    accuracy: float,
    grade: str,
    max_combo: int,
    mods: str,
    counts: Dict[str, int],
) -> bool:
    """
    Submit a play result.  Saves if it beats the current best score.
    Returns True if this is a new personal best.
    """
    _load()
    k = _key(song_title, diff_name)
    existing = _cache.get(k)

    if existing is None or score > existing.get("score", 0):
        _cache[k] = {
            "score":     round(score),
            "accuracy":  round(accuracy * 100, 2),
            "grade":     grade,
            "max_combo": max_combo,
            "mods":      mods,
            "counts":    counts,
        }
        _save()
        return True
    return False
