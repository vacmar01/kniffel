"""Game UI components."""
from fasthtml.common import *
from models import categories, fixed_scores
from services.game import calculate_scores


def ScoreInput(user, category, value):
    """
    Get the score HTML input element for each category.
    """
    common_attrs = {
        "name": "value",
        "aria_label": f"Punkte für {user}: {category}",
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


def ScorecardPreview():
    """A read-only example, never added to the session or analytics."""
    example_scores = {
        "Einser": 3, "Zweier": 6, "Dreier": 9, "Vierer": 12,
        "Fünfer": 15, "Sechser": 18, "Dreierpasch": 22,
        "Viererpasch": 24, "Full House": 25, "Kleine Straße": 30,
        "Große Straße": 40, "Kniffel": 0, "Chance": 23,
    }
    upper_total, bonus, total = calculate_scores(example_scores)
    cell_cls = "border border-gray-200 px-3 py-1 text-sm"
    return Div(
        H3("So sieht dein Kniffelblock aus", cls="text-lg font-semibold mb-2"),
        P(
            "Dies ist nur ein Beispiel. Füge oben den ersten Spieler hinzu, "
            "um einen leeren Block zu starten.",
            cls="text-gray-600 mb-4",
        ),
        Table(
            Caption(
                "Beispielrunde mit erfundenen Punkten – kein echter Spielstand",
                cls="text-sm text-gray-600 mb-2 text-left",
            ),
            Thead(
                Tr(
                    Th("Kategorie", scope="col", cls=cell_cls + " text-left"),
                    Th("Beispielpunkte", scope="col", cls=cell_cls + " text-right"),
                )
            ),
            Tbody(
                *[
                    Tr(
                        Th(category, scope="row", cls=cell_cls + " text-left font-normal"),
                        Td(str(example_scores[category]), cls=cell_cls + " text-right"),
                    )
                    for category in categories
                ],
            ),
            Tfoot(
                *[
                    Tr(
                        Th(label, scope="row", cls=cell_cls + " text-left"),
                        Td(str(value), cls=cell_cls + " text-right font-bold"),
                    )
                    for label, value in [
                        ("Oberer Teil Summe", upper_total),
                        ("Bonus (bei 63 oder mehr)", bonus),
                        ("Gesamtsumme", total),
                    ]
                ]
            ),
            cls="w-full border-collapse bg-white",
            id="scorecard-preview",
        ),
        cls="max-w-xl mx-auto",
        id="score-table",
    )


def ScoreTable(session):
    """
    Get the score table HTML element for the game.
    """
    users, scores = session.get("users", []), session.get("scores", {})
    if not users:
        return ScorecardPreview()

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
        cls="bg-white rounded-lg mt-4",
        id="score-table-container",
    )


def AddPlayerForm():
    return Form(
        Label("Spielername", fr="player-name", cls="sr-only"),
        Div(
            Input(
                type="text",
                id="player-name",
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
