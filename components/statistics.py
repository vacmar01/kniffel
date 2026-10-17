"""Present public entry statistics with explicit sample-size limits."""
from fasthtml.common import Caption, Div, P, Span, Table, Tbody, Td, Th, Thead, Tr

MIN_CATEGORY_ENTRIES = 5


def format_count(value):
    return f"{value:,}".replace(",", ".")


def format_decimal(value):
    return f"{value:.1f}".replace(".", ",")


def StatisticsCards(stats):
    return Div(
        *[
            Div(
                P(label, cls="text-sm text-gray-600"),
                P(format_count(value), cls="text-3xl font-bold text-gray-800 mt-1"),
                cls="bg-white border border-gray-200 rounded-lg p-5",
            )
            for label, value in [
                ("Punkte-Einträge", stats["entries"]),
                ("Davon mit 0 Punkten", stats["zero_entries"]),
                ("Kategorien mit Einträgen", sum(bool(item["entries"]) for item in stats["categories"])),
            ]
        ],
        cls="grid gap-4 sm:grid-cols-3 mb-6",
    )


def _sample_value(item, key, suffix=""):
    if item["entries"] < MIN_CATEGORY_ENTRIES:
        return Span(
            "—", title=f"Noch keine {MIN_CATEGORY_ENTRIES} gültigen Einträge",
            aria_label="Zu wenige Einträge für diese Kennzahl",
        )
    return format_decimal(item[key]) + suffix


def CategoryStatisticsTable(stats):
    cell = "border-b border-gray-200 px-3 py-3 text-sm"
    return Div(
        Table(
            Caption(
                "Erfasste Punkte-Einträge je Kategorie",
                cls="text-left text-sm text-gray-600 mb-3",
            ),
            Thead(
                Tr(*[
                    Th(label, scope="col", cls=cell + (" text-left" if index == 0 else " text-right"))
                    for index, label in enumerate([
                        "Kategorie", "Einträge", "Davon 0 Punkte",
                        "0-Punkte-Anteil", "Ø Punkte je Eintrag",
                    ])
                ])
            ),
            Tbody(*[
                Tr(
                    Th(item["category"], scope="row", cls=cell + " text-left font-medium"),
                    Td(format_count(item["entries"]), cls=cell + " text-right"),
                    Td(format_count(item["zero_entries"]), cls=cell + " text-right"),
                    Td(_sample_value(item, "zero_percent", " %"), cls=cell + " text-right"),
                    Td(_sample_value(item, "mean_points"), cls=cell + " text-right"),
                )
                for item in stats["categories"]
            ]),
            cls="w-full border-collapse bg-white",
            id="category-statistics",
        ),
        cls="overflow-x-auto",
        tabindex="0",
        role="region",
        aria_label="Kategorienstatistik, bei Bedarf seitlich scrollen",
    )
