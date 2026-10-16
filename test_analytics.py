"""Analytics tests using isolated, temporary databases."""
import sqlite3
from datetime import datetime, timedelta

import pytest

from services.analytics import init_analytics_db, log_event


@pytest.mark.parametrize("age_days", [29, 365])
def test_logging_preserves_historical_events(tmp_path, age_days):
    db_path = tmp_path / "analytics.db"
    init_analytics_db(db_path=db_path)
    old_timestamp = (datetime.now() - timedelta(days=age_days)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO events (session_hash, event_type, timestamp)
               VALUES (?, ?, ?)""",
            ("historical-session", "player_added", old_timestamp),
        )

    session = {"users": ["Player"], "scores": {"Player": {"Einser": 3}}}
    log_event(
        session, "score_entered", category="Einser", value=3, db_path=db_path
    )

    with sqlite3.connect(db_path) as conn:
        events = conn.execute(
            "SELECT event_type, timestamp, category, value FROM events ORDER BY id"
        ).fetchall()

    assert len(events) == 2
    assert events[0] == ("player_added", old_timestamp, None, None)
    assert events[1][0] == "score_entered"
    assert events[1][2:] == ("Einser", 3)
