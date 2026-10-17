"""Public, data-driven statistics from this deployment's analytics database."""
from datetime import datetime

from fasthtml.common import A, Div, H1, H2, Main, P, Strong

from app import rt
from components.layout import MyCard
from components.seo import PageMetadata
from components.statistics import (
    CategoryStatisticsTable, MIN_CATEGORY_ENTRIES, StatisticsCards, format_decimal,
)
from services.statistics import get_public_statistics

STATISTICS_TITLE = "Kniffel-Statistik: Punkte und Null-Einträge | online-kniffel.de"
STATISTICS_DESCRIPTION = (
    "Welche Kniffel-Kategorien werden mit null Punkten eingetragen? "
    "Entdecke aktuelle Statistiken aus unserem Online-Kniffelblock: "
    "Punkte-Einträge, Kategorie-Durchschnitte und Null-Punkte-Anteile."
)


def _date(value):
    try:
        return datetime.fromisoformat(value).strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return "unbekannt"


def _zero_point_summary(stats):
    eligible = [item for item in stats["categories"] if item["entries"] >= MIN_CATEGORY_ENTRIES]
    if not eligible:
        return None
    highest = max(item["zero_percent"] for item in eligible)
    if highest == 0:
        return None
    leaders = ", ".join(item["category"] for item in eligible if item["zero_percent"] == highest)
    return Div(
        H2("Am häufigsten mit 0 Punkten eingetragen", cls="text-xl font-semibold mb-3"),
        P(Strong(leaders), " – ", Strong(format_decimal(highest) + " %"), " der Einträge."),
        cls="text-gray-700 mb-6",
    )


def StatisticsResults(stats):
    if not stats["available"]:
        return MyCard(
            H2("Statistik gerade nicht verfügbar", cls="text-xl font-semibold mb-3"),
            P("Bitte versuche es später erneut."),
        )
    if not stats["entries"]:
        return MyCard(
            H2("Hier entstehen eure Kniffel-Statistiken", cls="text-xl font-semibold mb-3"),
            P("Die ersten Zahlen erscheinen, sobald Punkte eingetragen wurden."),
        )
    return Div(
        StatisticsCards(stats),
        MyCard(
            P(
                "Zeitraum: ", Strong(_date(stats["first_seen"])),
                " bis ", Strong(_date(stats["last_seen"])),
                cls="text-sm text-gray-600 mb-6",
            ),
            _zero_point_summary(stats),
            H2("Punkte nach Kategorie", cls="text-xl font-semibold mb-3"),
            CategoryStatisticsTable(stats),
        ),
        id="ergebnisse",
    )


@rt("/statistik/")
def get():
    stats = get_public_statistics()
    return (
        *PageMetadata(STATISTICS_TITLE, STATISTICS_DESCRIPTION, "/statistik/"),
        Div(
            Div(
                A("← Zum kostenlosen Kniffelblock", href="/", cls="underline text-blue-100"),
                H1("Kniffel-Statistik aus unserem Online-Block", cls="text-3xl sm:text-4xl font-bold mt-6 mb-4"),
                P(
                    "Welche Felder bekommen null Punkte? Wie hoch sind die eingetragenen "
                    "Werte je Kategorie? Entdecke die Zahlen aus unserem Kniffelblock.",
                    cls="text-lg text-blue-100 max-w-3xl",
                ),
                cls="max-w-5xl mx-auto",
            ),
            cls="bg-blue-600 text-white px-4 py-10",
        ),
        Main(
            StatisticsResults(stats),
            P(
                "Selbst eine Runde spielen? ",
                A("Kniffelblock kostenlos öffnen →", href="/", cls="text-blue-700 underline"),
                cls="text-center mt-8",
            ),
            cls="w-full min-w-0 max-w-5xl mx-auto px-4 py-8",
        ),
    )
