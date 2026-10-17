"""Public statistics page contracts using the same schema as production."""
from pathlib import Path
import sqlite3

from config import SITE_URL


def seed_entries():
    rows = [("Einser", 3)] * 4 + [("Einser", 0)]
    rows += [("Kniffel", 50)] * 4 + [("Kniffel", 0)]
    rows += [("Chance", 23), ("Einser", 15)]
    with sqlite3.connect("data/analytics.db") as conn:
        conn.executemany(
            """INSERT INTO events
               (session_hash, event_type, timestamp, category, value, metadata)
               VALUES ('private-session', 'score_entered', '2026-10-01T12:00:00', ?, ?,
                       '{"username":"PrivatePlayer"}')""",
            rows,
        )


def test_statistics_is_public_and_uses_its_own_canonical(client):
    response = client.get("/statistik/", headers={"host": "alternate.example"})
    assert response.status_code == 200
    assert response.text.count("<h1") == 1
    assert response.text.count('rel="canonical"') == 1
    assert f'href="{SITE_URL}/statistik/"' in response.text
    assert "alternate.example" not in response.text
    assert 'href="/"' in response.text
    assert "noindex" not in response.headers.get("x-robots-tag", "")


def test_statistics_reads_current_database_without_exposing_identities(client):
    seed_entries()
    response = client.get("/statistik/")
    assert response.status_code == 200
    assert 'id="category-statistics"' in response.text
    assert "Punkte-Einträge" in response.text
    assert "20,0 %" in response.text
    assert "2,4" in response.text
    assert "01.10.2026" in response.text
    assert "PrivatePlayer" not in response.text
    assert "private-session" not in response.text

    with sqlite3.connect("data/analytics.db") as conn:
        conn.execute(
            """INSERT INTO events (session_hash, event_type, timestamp, category, value)
               VALUES ('private-session', 'score_entered', '2026-10-02T12:00:00', 'Einser', 3)"""
        )
    updated = client.get("/statistik/").text
    assert "16,7 %" in updated
    assert "2,5" in updated
    assert "02.10.2026" in updated


def test_statistics_has_data_not_warning_or_methodology_sections(client):
    seed_entries()
    html = client.get("/statistik/").text
    for removed_copy in [
        "Methodik", "Stichprobe", "Wichtig:", "repräsentativ",
        "score_entered", "abgeschlossenen Spiele", "#methodik",
    ]:
        assert removed_copy not in html
    assert "Punkte nach Kategorie" in html
    assert "Ø Punkte je Eintrag" in html
    assert "0-Punkte-Anteil" in html


def test_empty_statistics_shows_a_simple_empty_state(client):
    html = client.get("/statistik/").text
    assert "Hier entstehen eure Kniffel-Statistiken" in html
    assert 'id="category-statistics"' not in html
    assert "erfundenen" not in html


def test_statistics_handles_unavailable_database_without_leaking_errors(client):
    Path("data/analytics.db").unlink()
    response = client.get("/statistik/")
    assert response.status_code == 200
    assert "Statistik gerade nicht verfügbar" in response.text
    assert "sqlite" not in response.text.lower()
    assert "data/analytics.db" not in response.text
    assert not Path("data/analytics.db").exists()


def test_homepage_links_to_public_statistics(client):
    assert 'href="/statistik/"' in client.get("/").text
