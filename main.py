from fasthtml.common import *

app, rt = fast_app(
    pico=False,
    hdrs=(
        Script(src="https://cdn.tailwindcss.com?plugins=typography"),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src="https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js", defer=True),
        MarkdownJS()
    ),
    bodykw={"class": "bg-gray-50 flex flex-col min-h-screen"}
)

categories = {
    "Einser": "Zähle nur die Einser", "Zweier": "Zähle nur die Zweier", "Dreier": "Zähle nur die Dreier",
    "Vierer": "Zähle nur die Vierer", "Fünfer": "Zähle nur die Fünfer", "Sechser": "Zähle nur die Sechser",
    "Dreierpasch": "Drei gleiche Augen, Summe aller Augen zählen", "Viererpasch": "Vier gleiche Augen, Summe aller Augen zählen", "Full House": "3 gleiche Augen und 2 gleiche Augen, 25 Punkte",
    "Kleine Straße": "4 aufeinanderfolgende Augen, 30 Punkte", "Große Straße": "5 aufeinanderfolgende Augen, 40 Punkte", "Kniffel": "5 gleiche Augen, 50 Punkte", "Chance": "Summe aller Augen"
}
fixed_scores = {"Full House": 25, "Kleine Straße": 30, "Große Straße": 40, "Kniffel": 50}
upper_section = ["Einser", "Zweier", "Dreier", "Vierer", "Fünfer", "Sechser"]

def calculate_scores(user_scores):
    """
    Calculate the scores for the game and return the upper total, bonus, and total as a tuple.
    """
    upper_total = sum(user_scores.get(cat, 0) or 0 for cat in upper_section)
    bonus = 35 if upper_total >= 63 else 0
    total = upper_total + bonus + sum(user_scores.get(cat, 0) or 0 for cat in categories if cat not in upper_section)
    return upper_total, bonus, total

def get_score_input(user, category, value):
    """
    Get the score HTML input element for each category.
    """
    common_attrs = {
        "name": "value",
        "hx_post": f"/update-score/{user}/{category}",
        "hx_target": "#score-table-container",
        "hx_swap": "outerHTML",
        "cls": "w-full p-1 border rounded"
    }
    if category in fixed_scores:
        return Select(
            Option("", value="", selected=value is None),
            Option("Gewürfelt", value=str(fixed_scores[category]), selected=value == fixed_scores[category]),
            Option("Gestrichen", value="0", selected=value == 0),
            hx_trigger="change",
            **common_attrs
        )
    return Input(type="number", value=value if value is not None else "", hx_trigger="blur", **common_attrs)

def get_score_table(session):
    """
    Get the score table HTML element for the game.
    """
    users, scores = session.get("users", []), session.get("scores", {})
    if not users:
        return Div("Füge Spieler hinzu, um das Spiel zu beginnen.", cls="italic text-gray-500", id="score-table")
    
    def get_missing_categories(user_scores):
        """
        Get the missing categories for a user to display in the score table.
        """
        return [cat for cat in categories if user_scores.get(cat) is None]
    
    return Table(
        Thead(Tr(Th("Kategorie", cls="border p-2"), *[Th(
            Div(user, Button("×", hx_post=f"/delete-user/{user}", hx_target="#score-table-container", hx_swap="outerHTML",
                             hx_confirm=f"Bist du sicher, dass du {user} entfernen möchtest?", cls="ml-2 text-red-500 font-bold"),
                cls="flex justify-between items-center"),
            cls="border p-2"
        ) for user in users])),
        Tbody(
            Tr(
                Td("Fehlende Kategorien", cls="border p-2 text-gray-500 text-sm"),
                *[Td(
                    Div(
                        *[Div(cat, cls="bg-gray-100 text-gray-600 text-xs font-normal mr-1 px-2 py-0.5 rounded") 
                          for cat in get_missing_categories(scores.get(user, {}))],
                        cls="flex flex-wrap gap-1"
                    ),
                    cls="border p-2"
                ) for user in users],
                cls="border-t border-b border-gray-200"
            ),
            *[Tr(
                Td(Div(Span(category, cls="mr-2"), Span("ⓘ", cls="cursor-pointer", **{"@mouseenter": "tooltip = true", "@mouseleave": "tooltip = false"}),
                        Div(description, cls="absolute bg-gray-800 text-white p-2 rounded shadow-md z-10 mt-1", x_show="tooltip"),
                        cls="relative"), cls="border p-2", x_data="{ tooltip: false }"),
                *[Td(get_score_input(user, category, scores.get(user, {}).get(category)), cls="border p-2") for user in users]
            ) for category, description in categories.items()],
            *[Tr(Td(label, cls="border p-2 font-bold"),
                 *[Td(str(value), cls="border p-2 font-bold") for value in [calculate_scores(scores.get(user, {}))[i] for user in users]])
              for i, label in enumerate(["Oberer Teil Summe", "Bonus (bei 63 oder mehr)", "Gesamtsumme"])],
        ),
        cls="w-full border-collapse", id="score-table"
    )

def get_score_table_container(session):
    """
    Get the score table container HTML element for the game. 
    It contains the score table, a reset button, and a container for the score table.
    """
    has_players = bool(session.get("users"))
    return Div(
        get_score_table(session),
        Button("Punktestand zurücksetzen", hx_post="/reset-scores", hx_target="#score-table-container", hx_swap="outerHTML",
               hx_confirm="Sind Sie sicher, dass Sie alle Punkte zurücksetzen möchten?",
               cls="mt-4 bg-red-500 hover:bg-red-600 text-white p-2 rounded transition duration-300 ease-in-out") if has_players else None,
        cls="bg-white rounded-lg p-6", id="score-table-container"
    )

@rt("/")
def get(session):
    """
    Get the main page HTML element for the game.
    It contains the title, description, and a form to add players.
    """
    with open('content.md', 'r', encoding='utf-8') as file:
        md_content = file.read()
    
    return Title('Kniffel Online'), Div(
        Div(
            Div(Span("🎲", cls="text-6xl mb-2"), H1("Kniffel Online", cls="text-4xl font-bold text-blue-600 mb-2"), cls="flex flex-col items-center"),
            P("Spiele Kniffel mit deinen Freunden", cls="text-xl text-gray-600 mb-6"),
            cls="container mx-auto"
        ),
        cls="bg-gradient-to-r from-blue-100 to-blue-200 p-10 text-center mb-8 w-full"
    ), Div(
        Div(
            Div(
                H2("Spieler hinzufügen", cls="text-xl font-semibold mb-4 text-center"),
                Form(
                    Div(
                        Input(type="text", name="username", placeholder="Spielername", cls="w-full border border-gray-300 rounded-l p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"),
                        Button("Hinzufügen", type="submit", cls="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-r transition duration-300 ease-in-out"),
                        cls="flex"
                    ),
                    hx_post="/add-user", hx_target="#score-table-container", hx_swap="outerHTML", **{'hx-on::after-request': "this.reset()"},
                    cls="max-w-md mx-auto mb-6"
                ),
                Div(
                    Div(id="score-table", cls="mt-4", hx_get="/score-table", hx_trigger="load"),
                    id="score-table-container"
                ),
                cls="bg-white p-6 rounded-lg mx-auto shadow-md"
            ),
            # Div(
            #     Div(md_content, cls="marked prose prose-lg mx-auto"),
            #     cls="bg-white p-6 rounded-lg shadow-md mt-8"
            # ),
            Footer(
                P("Created by ", A("@rasmus1610", href="https://twitter.com/rasmus1610", target="_blank", cls="text-blue-500 hover:text-blue-700"),
                  " | ", A("GitHub", href="https://github.com/vacmar01/kniffel", target="_blank", cls="text-blue-500 hover:text-blue-700"),
                  cls="text-center text-gray-600"),
                cls="mt-8 pb-4"
            ),
            cls="container mx-auto -mt-16"
        ),
        cls="mx-auto w-full"
    )

@rt("/add-user")
def post(session, username: str):
    """
    Add a user to the game.
    """
    users = session.get("users", [])
    if username and username not in users:
        users.append(username)
        session["users"] = users
    return get_score_table_container(session)

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
    return get_score_table_container(session)

@rt("/score-table")
def get(session):
    """
    Get the score table container HTML element for the game.
    """
    return get_score_table_container(session)

@rt("/update-score/{user}/{category}")
def post(session, user: str, category: str, value: str):
    """
    Update the score for a user and category.
    """
    scores = session.get("scores", {})
    scores.setdefault(user, {})
    
    if value == "":
        scores[user][category] = None
    elif category in fixed_scores:
        if value == "0":  # "Gestrichen"
            scores[user][category] = 0
        else:  # "Gewürfelt"
            scores[user][category] = fixed_scores[category]
    else:
        scores[user][category] = int(value) if value else None
    
    session["scores"] = scores
    return get_score_table_container(session)

@rt("/reset-scores")
def post(session):
    """
    Reset the scores for all users.
    """
    session["scores"] = {user: {} for user in session.get("users", [])}
    return get_score_table_container(session)

serve()