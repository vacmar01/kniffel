"""Admin routes for analytics dashboard."""
import os
from datetime import datetime
from fasthtml.common import *
from app import rt
from config import ADMIN_PASSWORD, ANALYTICS_DB
from services.analytics import get_analytics_summary, reset_analytics


def require_admin(session):
    """Check if user is authenticated as admin."""
    if not session.get("is_admin"):
        return Redirect("/admin/login")
    return None


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
    
    reset_analytics()
    return Redirect("/admin/dashboard")
