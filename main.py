from fasthtml.common import *
import mistletoe
from starlette.staticfiles import StaticFiles
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
import os
import uuid
from pathlib import Path

# Ensure data directory exists
Path("data").mkdir(exist_ok=True)

# Analytics database setup
ANALYTICS_DB = "data/analytics.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kniffel-admin-123")


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
        import random

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


# Initialize analytics on startup
init_analytics_db()

app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel="stylesheet", href="/static/bundle.css"),
        Script(src="/static/bundle.js", defer=""),
        Meta(
            name="description",
            content="Kniffelblock online - kostenlos, ohne Registrierung",
        ),
        Script(
            **{
                "src": "https://plausible.io/js/pa-18b2DkMlaQkIpNDpUM7Rm.js",
                "async": "",
            }
        ),
        Script(
            "window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};\n  plausible.init()"
        ),
    ),
    bodykw={"class": "bg-gray-50 flex flex-col min-h-screen"},
)

# Explicitly mount static files for Railway compatibility
app.mount("/static", StaticFiles(directory="static"), name="static")

setup_toasts(app)

categories = {
    "Einser": "Zähle nur die Einser",
    "Zweier": "Zähle nur die Zweier",
    "Dreier": "Zähle nur die Dreier",
    "Vierer": "Zähle nur die Vierer",
    "Fünfer": "Zähle nur die Fünfer",
    "Sechser": "Zähle nur die Sechser",
    "Dreierpasch": "Drei gleiche Augen, Summe aller Augen zählen",
    "Viererpasch": "Vier gleiche Augen, Summe aller Augen zählen",
    "Full House": "3 gleiche Augen und 2 gleiche Augen, 25 Punkte",
    "Kleine Straße": "4 aufeinanderfolgende Augen, 30 Punkte",
    "Große Straße": "5 aufeinanderfolgende Augen, 40 Punkte",
    "Kniffel": "5 gleiche Augen, 50 Punkte",
    "Chance": "Summe aller Augen",
}
fixed_scores = {
    "Full House": 25,
    "Kleine Straße": 30,
    "Große Straße": 40,
    "Kniffel": 50,
}
upper_section = ["Einser", "Zweier", "Dreier", "Vierer", "Fünfer", "Sechser"]


def calculate_scores(user_scores):
    """
    Calculate the scores for the game and return the upper total, bonus, and total as a tuple.
    """
    upper_total = sum(user_scores.get(cat, 0) or 0 for cat in upper_section)
    bonus = 35 if upper_total >= 63 else 0
    total = (
        upper_total
        + bonus
        + sum(
            user_scores.get(cat, 0) or 0
            for cat in categories
            if cat not in upper_section
        )
    )
    return upper_total, bonus, total


def ScoreInput(user, category, value):
    """
    Get the score HTML input element for each category.
    """
    common_attrs = {
        "name": "value",
        "hx_post": f"/update-score/{user}/{category}",
        "hx_target": "#score-table-container",
        "hx_swap": "outerHTML",
        "cls": "w-full p-1 text-sm border border-gray-300 min-w-0",
    }
    if category in fixed_scores:
        return Select(
            Option("", value="", selected=value is None),
            Option(
                "Gewürfelt",
                value=str(fixed_scores[category]),
                selected=value == fixed_scores[category],
            ),
            Option("Gestrichen", value="0", selected=value == 0),
            hx_trigger="change",
            **common_attrs,
        )
    return Input(
        type="number",
        value=value if value is not None else "",
        hx_trigger="blur",
        **common_attrs,
    )


def ScoreTable(session):
    """
    Get the score table HTML element for the game.
    """
    users, scores = session.get("users", []), session.get("scores", {})
    if not users:
        return Div(
            Div("🎲", cls="text-6xl mb-4"),
            Div("Noch keine Spieler", cls="text-lg font-semibold text-gray-700 mb-2"),
            Div(
                "Füge oben Spieler hinzu, um das Spiel zu beginnen", cls="text-gray-500"
            ),
            cls="flex flex-col items-center justify-center py-16 text-center",
            id="score-table",
        )

    def get_missing_categories(user_scores):
        """
        Get the missing categories for a user to display in the score table.
        """
        return [cat for cat in categories if user_scores.get(cat) is None]

    return Table(
        Thead(
            Tr(
                Th("Kategorie", cls="border border-gray-200 p-2 w-32"),
                *[
                    Th(
                        Div(
                            user,
                            Button(
                                "×",
                                hx_post=f"/delete-user/{user}",
                                hx_target="#score-table-container",
                                hx_swap="outerHTML",
                                hx_confirm=f"Bist du sicher, dass du {user} entfernen möchtest?",
                                cls="ml-2 text-red-500 font-bold text-sm",
                            ),
                            cls="flex justify-between items-center text-sm",
                        ),
                        cls="border border-gray-200 p-2 min-w-24",
                    )
                    for user in users
                ],
            )
        ),
        Tbody(
            Tr(
                Td("Fehlende", cls="border border-gray-200 p-2 text-gray-500 text-sm"),
                *[
                    Td(
                        Div(
                            *[
                                Div(
                                    cat,
                                    cls="bg-gray-100 text-gray-600 text-xs font-normal mr-1 px-2 py-0.5 rounded",
                                )
                                for cat in get_missing_categories(scores.get(user, {}))
                            ],
                            cls="flex flex-wrap gap-1",
                        ),
                        cls="border border-gray-200 p-2",
                    )
                    for user in users
                ],
            ),
            *[
                Tr(
                    Td(
                        Div(
                            Span(category, cls="mr-1 text-sm"),
                            Span(
                                "ⓘ",
                                cls="cursor-pointer text-xs",
                                **{
                                    "@mouseenter": "tooltip = true",
                                    "@mouseleave": "tooltip = false",
                                },
                            ),
                            Div(
                                description,
                                cls="absolute bg-gray-800 text-white p-2 rounded shadow-md z-10 mt-1 text-xs w-48",
                                x_show="tooltip",
                            ),
                            cls="relative",
                        ),
                        cls="border border-gray-200 p-1",
                        x_data="{ tooltip: false }",
                    ),
                    *[
                        Td(
                            ScoreInput(
                                user, category, scores.get(user, {}).get(category)
                            ),
                            cls="border border-gray-200 p-1",
                        )
                        for user in users
                    ],
                )
                for category, description in categories.items()
            ],
            *[
                Tr(
                    Td(label, cls="border border-gray-200 p-2 font-bold text-sm"),
                    *[
                        Td(
                            str(value),
                            cls="border border-gray-200 p-2 font-bold text-sm",
                        )
                        for value in [
                            calculate_scores(scores.get(user, {}))[i] for user in users
                        ]
                    ],
                )
                for i, label in enumerate(
                    ["Oberer Teil Summe", "Bonus (bei 63 oder mehr)", "Gesamtsumme"]
                )
            ],
        ),
        cls="w-full border-collapse bg-white text-sm",
        id="score-table",
    )


def ScoreTableContainer(session):
    """
    Get the score table container HTML element for the game.
    It contains the score table, a reset button, and a container for the score table.
    """
    has_players = bool(session.get("users"))
    return Div(
        Div(ScoreTable(session), cls="overflow-x-auto"),
        Button(
            "Punktestand zurücksetzen",
            hx_post="/reset-scores",
            hx_target="#score-table-container",
            hx_swap="outerHTML",
            hx_confirm="Sind Sie sicher, dass Sie alle Punkte zurücksetzen möchten?",
            cls="mt-4 bg-red-500 hover:bg-red-600 text-white p-2 rounded transition duration-300 ease-in-out",
        )
        if has_players
        else None,
        cls="bg-white rounded-lg p-6",
        id="score-table-container",
    )


def Navbar():
    return Div(
        Div(
            Span(
                "Sende Feedback",
                cls="mr-2 font-bold text-gray-100",
                x_transition="",
                x_show="showFeedback",
            ),
            A(
                "📧",
                href="mailto:mariusvach@gmail.com",
                cls="text-4xl relative",
                target="_blank",
                **{
                    "@mouseenter": "showFeedback = true",
                    "@mouseleave": "showFeedback = false",
                },
            ),
            cls="inline-flex items-center pr-4",
            x_data="{ showFeedback: false }",
        ),
        cls="w-full bg-transparent py-4 flex justify-end",
    )


def Hero():
    return Div(
        Span("🎲", cls="text-6xl mb-2"),
        H1("online-kniffel.de", cls="text-4xl font-bold text-gray-100 mb-2"),
        cls="flex flex-col items-center mt-10",
    ), P(
        "Kniffelblock online - kostenlos, ohne Registrierung",
        cls="text-xl text-gray-300 mb-6",
    )


def Header():
    style = """
    background-color: #3b82f6;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.14'%3E%3Cpath opacity='.5' d='M96 95h4v1h-4v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9zm-1 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9z'/%3E%3Cpath d='M6 5V0H5v5H0v1h5v94h1V6h94V5H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    """

    return Div(
        Div(Navbar(), Hero(), cls="container mx-auto"),
        cls="pb-32 text-center mb-8 w-full",
        style=style,
    )


def Banner():
    return Div(
        cls="w-full flex items-center justify-center py-3 text-md text-gray-800 font-semibold bg-amber-400 border-b shadow border-amber-600"
    )(
        Span(cls="mr-1")("🎲 Online-Kniffel.de gibt es bald auch als App."),
        A(
            href="#",
            onclick="plausible('More')",
            cls="text-blue-500 hover:opacity-70 transition-all",
        )("Erfahre mehr →"),
    )


def AddPlayerForm():
    return Form(
        Div(
            Input(
                type="text",
                name="username",
                placeholder="Spielername",
                cls="w-full text-lg border border-gray-300 rounded-l p-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
            ),
            Button(
                "Hinzufügen",
                type="submit",
                onclick="plausible('Add')",
                cls="bg-blue-500 hover:bg-blue-600 text-lg text-white p-2 rounded-r transition duration-300 ease-in-out disabled:bg-gray-400 disabled:cursor-not-allowed",
            ),
            cls="flex",
        ),
        hx_post="/add-user",
        hx_target="#score-table-container",
        hx_swap="outerHTML",
        **{"hx-on::after-request": "this.reset()"},
        hx_disabled_elt="find button",
        cls="max-w-md mx-auto mb-6",
    )


def MyCard(*args, **kwargs):
    cls = f"bg-white p-6 rounded-lg shadow-md {kwargs.pop('cls', '')}"
    return Div(*args, **kwargs, cls=cls)


@rt("/")
def get(session):
    """
    Get the main page HTML element for the game.
    It contains the title, description, and a form to add players.
    """

    # read in content.md with the content for the home page
    with open("content.md", "r", encoding="utf-8") as file:
        md_content = file.read()
    content_html = mistletoe.markdown(md_content)

    return (
        Title("online-kniffel.de - Kniffelblock online"),
        Header(),
        Div(
            Div(
                MyCard(
                    H2(
                        "Spieler hinzufügen",
                        cls="text-xl font-semibold mb-4 text-center",
                    ),
                    AddPlayerForm(),
                    Div(
                        Div(
                            id="score-table",
                            cls="mt-4",
                            hx_get="/score-table",
                            hx_trigger="load",
                        ),
                        id="score-table-container",
                    ),
                ),
                MyCard(
                    Div(
                        NotStr(content_html),
                        cls="prose prose-lg prose-zinc max-w-3xl mx-auto",
                    ),
                    cls="mt-8",
                ),
                Footer(
                    P(
                        "Created by ",
                        A(
                            "@rasmus1610",
                            href="https://twitter.com/rasmus1610",
                            target="_blank",
                            cls="text-blue-500 hover:text-blue-700",
                        ),
                        " | ",
                        A(
                            "GitHub",
                            href="https://github.com/vacmar01/kniffel",
                            target="_blank",
                            cls="text-blue-500 hover:text-blue-700",
                        ),
                        cls="text-center text-gray-600",
                    ),
                    cls="py-12",
                ),
                cls="container mx-auto -mt-32",
            )
        ),
    )


@rt("/add-user")
def post(session, username: str):
    """
    Add a user to the game.
    """
    users = session.get("users", [])
    if username and username not in users:
        users.append(username.strip())
        session["users"] = users
        log_event(session, "player_added")

    add_toast(session, f"{username} wurde hinzugefügt", "success")
    return ScoreTableContainer(session)


@rt("/delete-user/{username}")
def post(session, username: str):
    """
    Delete a user from the game.
    """
    users = session.get("users", [])
    if username in users:
        users.remove(username)
        session["users"] = users
        scores = session.get("scores", {})
        if username in scores:
            del scores[username]
            session["scores"] = scores
        log_event(session, "player_removed")
    return ScoreTableContainer(session)


@rt("/score-table")
def get(session):
    """
    Get the score table container HTML element for the game.
    """
    return ScoreTableContainer(session)


@rt("/update-score/{user}/{category}")
def post(session, user: str, category: str, value: str):
    """
    Update the score for a user and category.
    """
    scores = session.get("scores", {})
    scores.setdefault(user, {})

    if value == "":
        scores[user][category] = None
        log_event(session, "score_cleared", category=category)
    elif category in fixed_scores:
        if value == "0":  # "Gestrichen"
            scores[user][category] = 0
            log_event(session, "score_crossed_out", category=category, value=0)
        else:  # "Gewürfelt"
            scores[user][category] = fixed_scores[category]
            log_event(
                session,
                "score_entered",
                category=category,
                value=fixed_scores[category],
            )
    else:
        int_value = int(float(value)) if value else None
        scores[user][category] = int_value
        if int_value is not None:
            log_event(session, "score_entered", category=category, value=int_value)

    session["scores"] = scores
    return ScoreTableContainer(session)


@rt("/reset-scores")
def post(session):
    """
    Reset the scores for all users.
    """
    session["scores"] = {user: {} for user in session.get("users", [])}
    log_event(session, "scores_reset")
    return ScoreTableContainer(session)


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


@rt("/admin/login")
def get():
    """Admin login page."""
    return (
        Title("Admin Login - Kniffel Analytics"),
        Div(
            H1("Admin Login", cls="text-2xl font-bold mb-4"),
            Form(
                Input(
                    type="password",
                    name="password",
                    placeholder="Password",
                    cls="border p-2 mb-2 w-full",
                ),
                Button(
                    "Login", type="submit", cls="bg-blue-500 text-white p-2 rounded"
                ),
                action="/admin/login",
                method="post",
            ),
            cls="max-w-md mx-auto mt-20 p-6",
        ),
    )


def require_admin(session):
    """Check if user is authenticated as admin."""
    if not session.get("is_admin"):
        return Redirect("/admin/login")
    return None


@rt("/admin/login")
def post(session, password: str):
    """Handle admin login."""
    if password == ADMIN_PASSWORD:
        session["is_admin"] = True
        return Redirect("/admin/dashboard")
    return Redirect("/admin/login")


@rt("/admin/dashboard")
def get(session):
    """Analytics dashboard."""
    auth_check = require_admin(session)
    if auth_check:
        return auth_check
    
    stats = get_analytics_summary()

    if "error" in stats:
        return (
            Title("Analytics Dashboard"),
            Div(
                H1("Error loading analytics", cls="text-2xl font-bold text-red-600"),
                P(stats["error"]),
                cls="p-6",
            ),
        )

    # Build event type breakdown
    event_type_rows = [
        Tr(Td(event_type), Td(str(count), cls="text-right"))
        for event_type, count in stats["events_by_type"]
    ]

    # Build player distribution
    player_dist_rows = [
        Tr(
            Td(f"{count} Player{'s' if count != 1 else ''}"),
            Td(str(occurrences), cls="text-right"),
        )
        for count, occurrences in stats["player_distribution"]
    ]

    # Build category stats
    category_rows = [
        Tr(
            Td(category),
            Td(str(total), cls="text-right"),
            Td(str(crossed_out), cls="text-right"),
            Td(
                f"{round((int(crossed_out) / int(total)) * 100, 1)}%"
                if int(total) > 0
                else "0%",
                cls="text-right",
            ),
        )
        for category, total, crossed_out in stats["category_stats"]
    ]

    return (
        Title("Analytics Dashboard - Kniffel"),
        Div(
            H1("📊 Kniffel Analytics Dashboard", cls="text-3xl font-bold mb-6"),
            # Summary Cards
            Div(
                Div(
                    H2("Total Events", cls="text-gray-600 text-sm"),
                    P(str(stats["total_events"]), cls="text-3xl font-bold"),
                    cls="bg-white p-4 rounded shadow",
                ),
                Div(
                    H2("Unique Sessions", cls="text-gray-600 text-sm"),
                    P(str(stats["unique_sessions"]), cls="text-3xl font-bold"),
                    cls="bg-white p-4 rounded shadow",
                ),
                Div(
                    H2("Sessions (24h)", cls="text-gray-600 text-sm"),
                    P(str(stats["recent_sessions_24h"]), cls="text-3xl font-bold"),
                    cls="bg-white p-4 rounded shadow",
                ),
                Div(
                    H2("Completed Games", cls="text-gray-600 text-sm"),
                    P(str(stats["completed_sessions"]), cls="text-3xl font-bold"),
                    cls="bg-white p-4 rounded shadow",
                ),
                cls="grid grid-cols-4 gap-4 mb-8",
            ),
            # Completion Stats
            Div(
                H2("Game Completion", cls="text-xl font-bold mb-4"),
                P(f"Average categories filled per session: {stats['avg_categories']}"),
                P(f"Most categories filled in a session: {stats['max_categories']}"),
                cls="bg-white p-4 rounded shadow mb-8",
            ),
            # Two column layout
            Div(
                # Event Types
                Div(
                    H2("Events by Type", cls="text-xl font-bold mb-4"),
                    Table(
                        Thead(Tr(Th("Event"), Th("Count", cls="text-right"))),
                        Tbody(*event_type_rows),
                        cls="w-full",
                    ),
                    cls="bg-white p-4 rounded shadow",
                ),
                # Player Distribution
                Div(
                    H2("Player Count Distribution", cls="text-xl font-bold mb-4"),
                    Table(
                        Thead(Tr(Th("Players"), Th("Occurrences", cls="text-right"))),
                        Tbody(*player_dist_rows),
                        cls="w-full",
                    ),
                    cls="bg-white p-4 rounded shadow",
                ),
                cls="grid grid-cols-2 gap-4 mb-8",
            ),
            # Category Stats
            Div(
                H2("Category Usage", cls="text-xl font-bold mb-4"),
                Table(
                    Thead(
                        Tr(
                            Th("Category"),
                            Th("Total Uses", cls="text-right"),
                            Th("Crossed Out", cls="text-right"),
                            Th("Crossed Out %", cls="text-right"),
                        )
                    ),
                    Tbody(*category_rows),
                    cls="w-full",
                ),
                cls="bg-white p-4 rounded shadow mb-8",
            ),
            # Download button
            Div(
                A(
                    "Download Database",
                    href="/admin/download",
                    cls="bg-green-500 hover:bg-green-600 text-white p-3 rounded inline-block",
                ),
                Form(
                    Button(
                        "Reset Analytics",
                        type="submit",
                        onclick="return confirm('Are you sure you want to reset all analytics data? This cannot be undone.');",
                        cls="bg-red-500 hover:bg-red-600 text-white p-3 rounded ml-2",
                    ),
                    action="/admin/reset",
                    method="post",
                    cls="inline",
                ),
                cls="mt-8",
            ),
            cls="container mx-auto p-6 bg-gray-50 min-h-screen",
        ),
    )


@rt("/admin/download")
def get(session):
    """Download the analytics database."""
    auth_check = require_admin(session)
    if auth_check:
        return auth_check
    
    if not os.path.exists(ANALYTICS_DB):
        return Response("Database not found", status_code=404)

    with open(ANALYTICS_DB, "rb") as f:
        content = f.read()

    return Response(
        content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=kniffel_analytics_{datetime.now().strftime('%Y%m%d')}.db"
        },
    )


@rt("/admin/reset")
def post(session):
    """Reset the analytics database."""
    auth_check = require_admin(session)
    if auth_check:
        return auth_check
    
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        conn.execute("DELETE FROM events")
        conn.commit()
        conn.close()
    except Exception:
        pass
    
    return Redirect("/admin/dashboard")


import sys

# Get port from command line, but only if it looks like a port number
port = 5001
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        pass  # Not a valid port, use default

serve(port=port)
