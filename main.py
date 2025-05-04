from fasthtml.common import *

app, rt = fast_app(
    pico=False,
    hdrs=(
        Script(src="https://cdn.tailwindcss.com?plugins=typography"),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src="https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js", defer=True),
        MarkdownJS(),
        Meta(name="description", content="Kniffelblock online - kostenlos, ohne Registrierung"),
        Script(defer=True, data_domain='onlinekniffel.de', src='https://plausible.io/js/script.js'),
        Script("window.plausible = window.plausible || function() { (window.plausible.q = window.plausible.q || []).push(arguments) }")
    ),
    bodykw={"class": "bg-gray-50 flex flex-col min-h-screen"}
)

setup_toasts(app)

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

def ScoreInput(user, category, value):
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

def ScoreTable(session):
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
                Td("Fehlende Kombinationen", cls="border p-2 text-gray-500 text-sm"),
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
                *[Td(ScoreInput(user, category, scores.get(user, {}).get(category)), cls="border p-2") for user in users]
            ) for category, description in categories.items()],
            *[Tr(Td(label, cls="border p-2 font-bold"),
                 *[Td(str(value), cls="border p-2 font-bold") for value in [calculate_scores(scores.get(user, {}))[i] for user in users]])
              for i, label in enumerate(["Oberer Teil Summe", "Bonus (bei 63 oder mehr)", "Gesamtsumme"])],
        ),
        cls="w-full border-collapse", id="score-table"
    )

def ScoreTableContainer(session):
    """
    Get the score table container HTML element for the game.
    It contains the score table, a reset button, and a container for the score table.
    """
    has_players = bool(session.get("users"))
    return Div(
        ScoreTable(session),
        Button("Punktestand zurücksetzen", hx_post="/reset-scores", hx_target="#score-table-container", hx_swap="outerHTML",
               hx_confirm="Sind Sie sicher, dass Sie alle Punkte zurücksetzen möchten?",
               cls="mt-4 bg-red-500 hover:bg-red-600 text-white p-2 rounded transition duration-300 ease-in-out") if has_players else None,
        cls="bg-white rounded-lg p-6", id="score-table-container"
    )

def Navbar():
    return Div(
        Div(
            Span("Sende Feedback", cls="mr-2 font-bold text-gray-100", x_transition=True, x_show="showFeedback"),
            A("📧", href="mailto:mariusvach@gmail.com", cls="text-4xl relative", target="_blank", **{"@mouseenter": "showFeedback = true", "@mouseleave": "showFeedback = false"}),
            cls="inline-flex items-center", x_data="{ showFeedback: false }"
        ),
        cls="w-full bg-transparent py-4 flex justify-end"
    )

def Hero():
    return Div(
            Span("🎲", cls="text-6xl mb-2"),
            H1("onlinekniffel.de", cls="text-4xl font-bold text-gray-100 mb-2"),
            cls="flex flex-col items-center mt-10"
        ), P("Kniffelblock online - kostenlos, ohne Registrierung", cls="text-xl text-gray-300 mb-6")


def Header():
    style = """
    background-color: #3b82f6;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.14'%3E%3Cpath opacity='.5' d='M96 95h4v1h-4v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9zm-1 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9z'/%3E%3Cpath d='M6 5V0H5v5H0v1h5v94h1V6h94V5H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    """

    return Div(
        Div(
            Navbar(),
            Hero(),
            cls="container mx-auto"
        ),
        cls="pb-32 text-center mb-8 w-full",
        style=style
    )

def Banner(): return Div(cls="w-full flex items-center justify-center py-3 text-md text-gray-800 font-semibold bg-amber-400 border-b shadow border-amber-600")(Span(cls="mr-1")("🎲 Onlinekniffel.de gibt es bald auch als App."), A(href="#", onclick="plausible('More')", cls="text-blue-500 hover:opacity-70 transition-all")("Erfahre mehr →"))

def AddPlayerForm():
    return Form(
            Div(
                Input(type="text", name="username", placeholder="Spielername", cls="w-full text-lg border border-gray-300 rounded-l p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"),
                Button("Hinzufügen", type="submit", onclick="plausible('Add')", cls="bg-blue-500 hover:bg-blue-600 text-lg text-white p-2 rounded-r transition duration-300 ease-in-out disabled:bg-gray-400 disabled:cursor-not-allowed"),
                cls="flex"
            ),
            hx_post="/add-user", hx_target="#score-table-container", hx_swap="outerHTML", **{'hx-on::after-request': "this.reset()"}, hx_disabled_elt="find button",
        cls="max-w-md mx-auto mb-6"
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

    #read in content.md with the content for the home page
    with open('content.md', 'r', encoding='utf-8') as file:
        md_content = file.read()

    return Title('onlinekniffel.de - Kniffelblock online'), Header(), Div(
        Div(
            MyCard(
                H2("Spieler hinzufügen", cls="text-xl font-semibold mb-4 text-center"),
                AddPlayerForm(),
                Div(
                    Div(id="score-table", cls="mt-4", hx_get="/score-table", hx_trigger="load"),
                    id="score-table-container"
                ),
            ),
            MyCard(
                Div(md_content, cls="marked prose prose-lg mx-auto"),
                cls="mt-8"
            ),
            Footer(
                P("Created by ", A("@rasmus1610", href="https://twitter.com/rasmus1610", target="_blank", cls="text-blue-500 hover:text-blue-700"),
                  " | ", A("GitHub", href="https://github.com/vacmar01/kniffel", target="_blank", cls="text-blue-500 hover:text-blue-700"),
                  cls="text-center text-gray-600"),
                cls="py-12"
            ),
            cls="container mx-auto -mt-32"
        )
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
    elif category in fixed_scores:
        if value == "0":  # "Gestrichen"
            scores[user][category] = 0
        else:  # "Gewürfelt"
            scores[user][category] = fixed_scores[category]
    else:
        scores[user][category] = int(float(value)) if value else None

    session["scores"] = scores
    return ScoreTableContainer(session)

@rt("/reset-scores")
def post(session):
    """
    Reset the scores for all users.
    """
    session["scores"] = {user: {} for user in session.get("users", [])}
    return ScoreTableContainer(session)

serve()
