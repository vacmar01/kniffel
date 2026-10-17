"""Read-only, aggregate statistics suitable for the public statistics page.

These are score-entry statistics, not reconstructed scorecards or dice odds.
No session hashes, player identities, or event metadata leave this service.
"""
from contextlib import closing
from pathlib import Path
import sqlite3

from config import ANALYTICS_DB
from models import categories, fixed_scores, upper_section


def _valid_score(category, value, event_type):
    if category not in categories or type(value) is not int:
        return False
    if event_type == "score_crossed_out" and value != 0:
        return False
    if category in upper_section:
        face = upper_section.index(category) + 1
        return 0 <= value <= 5 * face and value % face == 0
    if category in fixed_scores:
        return value in (0, fixed_scores[category])
    return value == 0 or 5 <= value <= 30


def get_public_statistics(*, db_path=ANALYTICS_DB):
    """Aggregate valid score events without modifying the database.

    Corrections remain separate events: the existing schema cannot reliably
    associate entries with an individual player or completed game.
    """
    try:
        uri = Path(db_path).resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=2)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT event_type, category, value, COUNT(*) AS entries,
                          MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen
                   FROM events
                   WHERE event_type IN ('score_entered', 'score_crossed_out')
                   GROUP BY event_type, category, value"""
            ).fetchall()
    except sqlite3.Error:
        return {"available": False}

    by_category = {
        category: {"category": category, "entries": 0, "zero_entries": 0, "points": 0}
        for category in categories
    }
    excluded_entries = 0
    first_seen, last_seen = [], []
    for row in rows:
        category, value, count = row["category"], row["value"], row["entries"]
        if not _valid_score(category, value, row["event_type"]):
            excluded_entries += count
            continue
        item = by_category[category]
        item["entries"] += count
        item["zero_entries"] += count if value == 0 else 0
        item["points"] += value * count
        if row["first_seen"]:
            first_seen.append(row["first_seen"])
        if row["last_seen"]:
            last_seen.append(row["last_seen"])

    results = []
    for item in by_category.values():
        entries = item["entries"]
        results.append({
            "category": item["category"],
            "entries": entries,
            "zero_entries": item["zero_entries"],
            "zero_percent": round(100 * item["zero_entries"] / entries, 1) if entries else None,
            "mean_points": round(item["points"] / entries, 1) if entries else None,
        })

    return {
        "available": True,
        "entries": sum(item["entries"] for item in results),
        "zero_entries": sum(item["zero_entries"] for item in results),
        "excluded_entries": excluded_entries,
        "first_seen": min(first_seen) if first_seen else None,
        "last_seen": max(last_seen) if last_seen else None,
        "categories": results,
    }
