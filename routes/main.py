"""Main page routes."""
import mistletoe
from fasthtml.common import *
from app import rt
from components.layout import Header, MyCard
from components.game import AddPlayerForm, ScoreTableContainer


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
        Title("Kniffelblock online – kostenlos Punkte eintragen | online-kniffel.de"),
        Header(),
        Div(
            Div(
                MyCard(
                    H2(
                        "Spieler hinzufügen und loslegen",
                        cls="text-xl font-semibold mb-4 text-center",
                    ),
                    P(
                        "Ihr braucht nur fünf Würfel. Tragt hier eure Namen ein "
                        "und führt euren gemeinsamen Kniffelblock auf einem Gerät.",
                        cls="text-center text-gray-600 max-w-2xl mx-auto mb-4",
                    ),
                    AddPlayerForm(),
                    ScoreTableContainer(session),
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
                cls="container mx-auto -mt-32 px-4",
            )
        ),
    )
