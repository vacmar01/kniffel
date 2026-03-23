"""Analytics service for tracking game events."""
import sqlite3
import json
import hashlib
import random
import uuid
from datetime import datetime, timedelta
from config import ANALYTICS_DB


def init_analytics_db():
    """Initialize the analytics database with events table."""
    conn = sqlite3.connect(ANALYTICS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_hash TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            player_count INTEGER,
            categories_filled INTEGER,
            category TEXT,
            value INTEGER,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_hash ON events(session_hash)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
    """)
    conn.commit()
    conn.close()


def cleanup_old_events():
    """Remove events older than 28 days."""
    conn = sqlite3.connect(ANALYTICS_DB)
    cutoff = (datetime.now() - timedelta(days=28)).isoformat()
    conn.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()


def get_session_hash(session):
    """Generate an anonymized hash for the session."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return hashlib.sha256(session["session_id"].encode()).hexdigest()[:8]


def count_filled_categories(scores):
    """Count total filled categories across all players."""
    total = 0
    for user_scores in scores.values():
        total += sum(1 for v in user_scores.values() if v is not None)
    return total


def log_event(session, event_type, category=None, value=None, extra_metadata=None):
    """Log an analytics event to the database."""
    try:
        # Cleanup old events periodically (1% chance)
        if random.random() < 0.01:
            cleanup_old_events()

        conn = sqlite3.connect(ANALYTICS_DB)
        users = session.get("users", [])
        scores = session.get("scores", {})

        metadata = extra_metadata or {}
        if category:
            metadata["category"] = category
        if value is not None:
            metadata["value"] = value

        conn.execute(
            """
            INSERT INTO events 
            (session_hash, event_type, timestamp, player_count, categories_filled, category, value, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                get_session_hash(session),
                event_type,
                datetime.now().isoformat(),
                len(users),
                count_filled_categories(scores),
                category,
                value,
                json.dumps(metadata) if metadata else None,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        # Silently fail - analytics should not break the app
        pass


def get_analytics_summary():
    """Get summary statistics from analytics database."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        conn.row_factory = sqlite3.Row

        # Total events
        total_events = conn.execute("SELECT COUNT(*) as count FROM events").fetchone()[
            "count"
        ]

        # Unique sessions
        unique_sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_hash) as count FROM events"
        ).fetchone()["count"]

        # Events by type
        events_by_type = conn.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM events 
            GROUP BY event_type 
            ORDER BY count DESC
        """).fetchall()

        # Recent sessions (last 24h)
        recent_cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        recent_sessions = conn.execute(
            """
            SELECT COUNT(DISTINCT session_hash) as count 
            FROM events 
            WHERE timestamp > ?
        """,
            (recent_cutoff,),
        ).fetchone()["count"]

        # Player count distribution (count sessions by max players, not every event)
        player_distribution = conn.execute("""
            SELECT max_player_count, COUNT(*) as count
            FROM (
                SELECT session_hash, MAX(player_count) as max_player_count
                FROM events
                WHERE event_type = 'player_added'
                GROUP BY session_hash
            )
            GROUP BY max_player_count
            ORDER BY max_player_count
        """).fetchall()

        # Category popularity
        category_stats = conn.execute("""
            SELECT category, COUNT(*) as count,
                   SUM(CASE WHEN event_type = 'score_crossed_out' THEN 1 ELSE 0 END) as crossed_out
            FROM events 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """).fetchall()

        # Session completion stats
        session_stats = conn.execute("""
            SELECT 
                AVG(categories_filled) as avg_categories,
                MAX(categories_filled) as max_categories,
                COUNT(CASE WHEN categories_filled >= 13 THEN 1 END) as completed_sessions
            FROM (
                SELECT session_hash, MAX(categories_filled) as categories_filled
                FROM events
                GROUP BY session_hash
            )
        """).fetchone()

        conn.close()

        return {
            "total_events": total_events,
            "unique_sessions": unique_sessions,
            "recent_sessions_24h": recent_sessions,
            "events_by_type": [(r["event_type"], r["count"]) for r in events_by_type],
            "player_distribution": [
                (r["max_player_count"], r["count"]) for r in player_distribution
            ],
            "category_stats": [
                (r["category"], r["count"], r["crossed_out"]) for r in category_stats
            ],
            "avg_categories": round(session_stats["avg_categories"] or 0, 1),
            "max_categories": session_stats["max_categories"] or 0,
            "completed_sessions": session_stats["completed_sessions"] or 0,
        }
    except Exception as e:
        return {"error": str(e)}


def reset_analytics():
    """Reset all analytics data."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        conn.execute("DELETE FROM events")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
