"""Public statistics use real SQLite data, not mocked query results."""
import json
import sqlite3

import pytest

from services.analytics import init_analytics_db
from services.statistics import get_public_statistics


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "analytics.db"
    init_analytics_db(db_path=path)
    return path


def insert_score(path, category, value, *, event_type="score_entered", timestamp="2026-10-01T12:00:00"):
    with sqlite3.connect(path) as conn:
        conn.execute(
            """INSERT INTO events
               (session_hash, event_type, timestamp, category, value, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("private-session", event_type, timestamp, category, value,
             '{"username": "PrivatePlayer"}'),
        )


def test_public_statistics_aggregate_entries_and_exclude_invalid_scores(database):
    insert_score(database, "Einser", 3, timestamp="2026-09-01T12:00:00")
    insert_score(database, "Einser", 5)
    insert_score(database, "Einser", 0)
    insert_score(database, "Full House", 25)
    insert_score(database, "Kniffel", 0, event_type="score_crossed_out")
    insert_score(database, "Chance", 23)
    for category, value in [
        ("Einser", 15), ("Zweier", 3), ("Große Straße", 50),
        ("Chance", 31), ("Unknown", 10), ("Einser", None), ("Einser", 1.5),
    ]:
        insert_score(database, category, value, timestamp="2020-01-01T00:00:00")
    insert_score(database, "Kniffel", 50, event_type="score_crossed_out")
    insert_score(database, "Einser", None, event_type="score_cleared")
    insert_score(database, None, None, event_type="player_added")

    stats = get_public_statistics(db_path=database)
    assert stats["available"]
    assert stats["entries"] == 6
    assert stats["zero_entries"] == 2
    assert stats["excluded_entries"] == 8
    assert stats["first_seen"] == "2026-09-01T12:00:00"
    assert stats["last_seen"] == "2026-10-01T12:00:00"
    einser = next(item for item in stats["categories"] if item["category"] == "Einser")
    assert einser == {
        "category": "Einser", "entries": 3, "zero_entries": 1,
        "zero_percent": 33.3, "mean_points": 2.7,
    }
    assert "PrivatePlayer" not in json.dumps(stats)
    assert "private-session" not in json.dumps(stats)


def test_corrections_count_as_entries_not_final_player_scores(database):
    insert_score(database, "Einser", 3)
    insert_score(database, "Einser", None, event_type="score_cleared")
    insert_score(database, "Einser", 5)
    stats = get_public_statistics(db_path=database)
    assert stats["entries"] == 2
    assert stats["categories"][0]["mean_points"] == 4


@pytest.mark.parametrize("category,value", [
    ("Einser", 5), ("Zweier", 10), ("Dreier", 15), ("Vierer", 20),
    ("Fünfer", 25), ("Sechser", 30), ("Dreierpasch", 5),
    ("Viererpasch", 30), ("Full House", 25), ("Kleine Straße", 30),
    ("Große Straße", 40), ("Kniffel", 50), ("Chance", 0),
])
def test_standard_category_scores_are_accepted(database, category, value):
    insert_score(database, category, value)
    assert get_public_statistics(db_path=database)["entries"] == 1


def test_empty_database_has_no_invented_results(database):
    stats = get_public_statistics(db_path=database)
    assert stats["available"]
    assert stats["entries"] == 0
    assert stats["first_seen"] is None
    assert all(item["mean_points"] is None for item in stats["categories"])


def test_public_statistics_does_not_modify_the_database(database):
    insert_score(database, "Kniffel", 50)
    before = database.read_bytes()
    get_public_statistics(db_path=database)
    assert database.read_bytes() == before


def test_missing_database_is_not_created(tmp_path):
    path = tmp_path / "missing.db"
    assert get_public_statistics(db_path=path) == {"available": False}
    assert not path.exists()


def test_unavailable_schema_does_not_expose_database_errors(tmp_path):
    path = tmp_path / "invalid.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE other (id INTEGER)")
    assert get_public_statistics(db_path=path) == {"available": False}
