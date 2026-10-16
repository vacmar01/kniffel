"""Homepage content and crawlable HTML contracts."""
from html.parser import HTMLParser

from models import categories


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def find(self, tag, **attrs):
        return [
            attributes for name, attributes in self.elements
            if name == tag and all(attributes.get(k) == v for k, v in attrs.items())
        ]


def test_homepage_targets_scorecard_searches(client):
    response = client.get("/")
    document = Document(response.text)

    assert response.status_code == 200
    assert len(document.find("h1")) == 1
    assert len(document.find("title")) == 1
    assert "Kniffelblock online – Punkte einfach eintragen" in response.text
    assert "Kniffelblock online – kostenlos Punkte eintragen" in response.text
    descriptions = document.find("meta", name="description")
    assert len(descriptions) == 1
    assert "Punkte für mehrere Spieler" in descriptions[0]["content"]


def test_homepage_explains_real_dice_and_browser_storage(client):
    html = client.get("/").text
    assert "Mit fünf echten Würfeln spielen" in html
    assert "kein Computerspiel mit virtuellen Würfeln" in html
    assert "Browser-Cookie" in html
    assert "Eine synchronisierte Partie auf mehreren Geräten gibt es nicht" in html
    assert "63 Punkte" in html
    assert "35 Bonuspunkte" in html


def test_example_scorecard_is_server_rendered_and_read_only(client):
    html = client.get("/").text
    document = Document(html)
    assert len(document.find("table", id="scorecard-preview")) == 1
    assert len(document.find("div", id="score-table-container")) == 1
    assert len(document.find("div", id="score-table")) == 1
    assert "Beispielrunde mit erfundenen Punkten" in html
    assert all(category in html for category in categories)
    assert not document.find("input", type="number")
    assert not document.find("select")
    assert 'hx-get="/score-table"' not in html


def test_example_never_becomes_a_player_or_a_score(client):
    client.get("/")
    html = client.post("/add-user", data={"username": "Alice"}).text
    document = Document(html)
    assert not document.find("table", id="scorecard-preview")
    assert len(document.find("input", type="number")) == 9
    assert all(not field.get("value") for field in document.find("input", type="number"))
    assert len(document.find("select")) == 4
    assert "Beispielpunkte" not in html


def test_existing_scorecard_is_server_rendered_after_reload(client):
    client.post("/add-user", data={"username": "Alice"})
    client.post("/update-score/Alice/Einser", data={"value": "3"})
    html = client.get("/").text
    document = Document(html)
    assert not document.find("table", id="scorecard-preview")
    assert len(document.find("table", id="score-table")) == 1
    assert len(document.find("div", id="score-table-container")) == 1
    assert document.find("input", type="number", value="3")
    assert document.find("input", **{"aria-label": "Punkte für Alice: Einser"})


def test_removing_last_player_returns_preview(client):
    client.post("/add-user", data={"username": "Alice"})
    html = client.post("/delete-user/Alice").text
    assert Document(html).find("table", id="scorecard-preview")
    assert "Punktestand zurücksetzen" not in html
