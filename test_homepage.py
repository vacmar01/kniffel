"""Homepage content and crawlable HTML contracts."""
from html.parser import HTMLParser


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
