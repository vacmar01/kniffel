from fasthtml.common import *
import json

app, rt = fast_app(
    pico=False,  # Deactivate Pico CSS
    hdrs=(
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src="https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js", defer=True),
    ),
    bodykw={"class": "bg-gray-50 flex flex-col min-h-screen"}  # Light gray background for the entire body
)

# Kniffel categories and their descriptions
categories = {
    "Einser": "Zähle nur die Einser",
    "Zweier": "Zähle nur die Zweier",
    "Dreier": "Zähle nur die Dreier",
    "Vierer": "Zähle nur die Vierer",
    "Fünfer": "Zähle nur die Fünfer",
    "Sechser": "Zähle nur die Sechser",
    "Dreierpasch": "Summe aller Augen",
    "Viererpasch": "Summe aller Augen",
    "Full House": "25 Punkte",
    "Kleine Straße": "30 Punkte",
    "Große Straße": "40 Punkte",
    "Kniffel": "50 Punkte",
    "Chance": "Summe aller Augen"
}

# Define fixed score categories
fixed_score_categories = {
    "Full House": 25,
    "Kleine Straße": 30,
    "Große Straße": 40,
    "Kniffel": 50
}

upper_section = ["Einser", "Zweier", "Dreier", "Vierer", "Fünfer", "Sechser"]

def calculate_upper_total(user_scores):
    return sum(user_scores.get(category, 0) or 0 for category in upper_section)

def calculate_bonus(upper_total):
    return 35 if upper_total >= 63 else 0

def calculate_total(user_scores):
    upper_total = calculate_upper_total(user_scores)
    bonus = calculate_bonus(upper_total)
    lower_total = sum(user_scores.get(category, 0) or 0 for category in categories if category not in upper_section)
    return upper_total + bonus + lower_total

def get_score_input(user, category, value):
    if category in fixed_score_categories:
        return Select(
            Option("", value="", selected=value is None),
            Option("Gewürfelt", value=str(fixed_score_categories[category]), selected=value == fixed_score_categories[category]),
            Option("Gestrichen", value="0", selected=value == 0),
            name="value",
            hx_post=f"/update-score/{user}/{category}",
            hx_target="#score-table-container",
            hx_swap="outerHTML",
            hx_trigger="change",
            cls="w-full p-1 border rounded bg-white"
        )
    else:
        return Input(
            type="number",
            value=value if value is not None else "",
            name="value",
            hx_post=f"/update-score/{user}/{category}",
            hx_target="#score-table-container",
            hx_swap="outerHTML",
            hx_trigger="blur",
            cls="w-full p-1 border rounded"
        )

def get_score_table(session):
    users = session.get("users", [])
    if not users:
        return Div("Fügen Sie Spieler hinzu, um das Spiel zu beginnen.", cls="italic text-gray-500", id="score-table")
    
    scores = session.get("scores", {})
    
    return Table(
        Thead(
            Tr(
                Th("Kategorie", cls="border p-2"),
                *[Th(
                    Div(
                        user,
                        Button(
                            "×",
                            hx_post=f"/delete-user/{user}",
                            hx_target="#score-table-container",
                            hx_swap="outerHTML",
                            hx_confirm=f"Bist du sicher, dass du {user} entfernen möchtest?",
                            cls="ml-2 text-red-500 font-bold"
                        ),
                        cls="flex justify-between items-center"
                    ),
                    cls="border p-2"
                ) for user in users]
            )
        ),
        Tbody(
            *[Tr(
                Td(
                    Div(
                        Span(category, cls="mr-2"),
                        Span(
                            "ⓘ",
                            cls="cursor-pointer",
                            **{"@mouseenter": "tooltip = true", "@mouseleave": "tooltip = false"}
                        ),
                        Div(
                            description,
                            cls="absolute bg-gray-800 text-white p-2 rounded shadow-lg z-10 mt-1",
                            x_show="tooltip"
                        ),
                        cls="relative"
                    ),
                    cls="border p-2",
                    x_data="{ tooltip: false }"
                ),
                *[Td(
                    get_score_input(user, category, scores.get(user, {}).get(category)),
                    cls="border p-2"
                ) for user in users]
            ) for category, description in categories.items()],
            Tr(
                Td("Oberer Teil Summe", cls="border p-2 font-bold"),
                *[Td(str(calculate_upper_total(scores.get(user, {}))), cls="border p-2 font-bold") for user in users]
            ),
            Tr(
                Td("Bonus (bei 63 oder mehr)", cls="border p-2 font-bold"),
                *[Td(str(calculate_bonus(calculate_upper_total(scores.get(user, {})))), cls="border p-2 font-bold") for user in users]
            ),
            Tr(
                Td("Gesamtsumme", cls="border p-2 font-bold"),
                *[Td(str(calculate_total(scores.get(user, {}))), cls="border p-2 font-bold") for user in users]
            )
        ),
        cls="w-full border-collapse",
        id="score-table"
    )

def get_score_table_container(session):
    users = session.get("users", [])
    has_players = len(users) > 0
    return Div(
        get_score_table(session),
        Button(
            "Punktestand zurücksetzen",
            hx_post="/reset-scores",
            hx_target="#score-table-container",
            hx_swap="outerHTML",
            hx_confirm="Sind Sie sicher, dass Sie alle Punkte zurücksetzen möchten?",
            cls="mt-4 bg-red-500 hover:bg-red-600 text-white p-2 rounded transition duration-300 ease-in-out"
        ) if has_players else None,
        cls="bg-white rounded-lg shadow-md p-6",
        id="score-table-container"
    )

@rt("/")
def get(session):
    return Div(
        Div(
            Div(
                Span("🎲", cls="text-6xl mb-2"),
                H1("Kniffel Online", cls="text-4xl font-bold text-blue-600 mb-2"),
                cls="flex flex-col items-center"
            ),
            P("Würfelspaß für die ganze Familie", cls="text-xl text-gray-600 mb-6"),
            cls="bg-gradient-to-r from-blue-100 to-blue-200 p-10 rounded-lg shadow-lg text-center mb-8"
        ),
        Div(
            H2("Spieler hinzufügen", cls="text-xl font-semibold mb-4"),
            Form(
                Div(
                    Input(type="text", name="username", placeholder="Spielername", cls="w-full border border-gray-300 rounded-l p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"),
                    Button("Hinzufügen", type="submit", cls="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-r transition duration-300 ease-in-out"),
                    cls="flex shadow-sm"
                ),
                hx_post="/add-user",
                hx_target="#score-table-container",
                hx_swap="outerHTML",
                **{'hx-on::after-request': "this.reset()"},
                cls="max-w-md mx-auto"
            ),
            cls="bg-white p-6 rounded-lg shadow-md mb-8"
        ),
        Div(
            Div(id="score-table", cls="mt-4", hx_get="/score-table", hx_trigger="load"),
            cls="bg-white rounded-lg shadow-md p-6",
            id="score-table-container"
        ),
        Footer(
            P(
                "Created by ",
                A("@rasmus1610", href="https://twitter.com/rasmus1610", target="_blank", cls="text-blue-500 hover:text-blue-700"),
                cls="text-center text-gray-600"
            ),
            cls="mt-8 pb-4"
        ),
        cls="container mx-auto p-4"
    )

@rt("/add-user")
def post(session, username: str):
    users = session.get("users", [])
    if username and username not in users:
        users.append(username)
        session["users"] = users
    return get_score_table_container(session)

@rt("/delete-user/{username}")
def post(session, username: str):
    users = session.get("users", [])
    if username in users:
        users.remove(username)
        session["users"] = users
        # Remove the user's scores
        scores = session.get("scores", {})
        if username in scores:
            del scores[username]
            session["scores"] = scores
    return get_score_table_container(session)

@rt("/score-table")
def get(session):
    return get_score_table_container(session)

@rt("/update-score/{user}/{category}")
def post(session, user: str, category: str, value: str):
    scores = session.get("scores", {})
    if user not in scores:
        scores[user] = {}
    
    if value == "":
        scores[user][category] = None
    elif category in fixed_score_categories:
        if value == "0":  # "Gestrichen"
            scores[user][category] = 0
        else:  # "Gewürfelt"
            scores[user][category] = fixed_score_categories[category]
    else:
        scores[user][category] = int(value) if value else None
    
    session["scores"] = scores
    return get_score_table_container(session)

@rt("/reset-scores")
def post(session):
    users = session.get("users", [])
    session["scores"] = {user: {} for user in users}  # Reset scores for existing users
    return get_score_table_container(session)

serve()