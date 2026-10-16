"""Homepage content and crawlable HTML contracts."""
from html.parser import HTMLParser
import json
import re
from xml.etree import ElementTree

import pytest

from config import SITE_URL
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


def test_public_metadata_uses_one_fixed_canonical_url(client):
    html = client.get("/", headers={"host": "alternate.example"}).text
    document = Document(html)
    assert document.find("html", lang="de")
    assert document.find("link", rel="canonical") == [
        {"rel": "canonical", "href": f"{SITE_URL}/"}
    ]
    assert document.find("meta", property="og:url")[0]["content"] == f"{SITE_URL}/"
    assert document.find("meta", property="og:locale")[0]["content"] == "de_DE"
    assert document.find("meta", name="twitter:card")[0]["content"] == "summary"
    assert "alternate.example" not in html
    assert "noindex" not in client.get("/").headers.get("x-robots-tag", "")


def test_structured_data_describes_the_free_tool_not_the_players(client):
    client.post("/add-user", data={"username": "PrivatePlayer"})
    html = client.get("/").text
    scripts = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    )
    assert len(scripts) == 1
    data = json.loads(scripts[0])
    assert data["@type"] == "WebApplication"
    assert data["url"] == f"{SITE_URL}/"
    assert data["inLanguage"] == "de"
    assert data["offers"]["price"] == "0"
    assert "PrivatePlayer" not in scripts[0]
    assert "aggregateRating" not in data


def test_robots_advertises_production_sitemap(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "User-agent: *\nAllow: /" in response.text
    assert f"Sitemap: {SITE_URL}/sitemap.xml" in response.text


def test_sitemap_lists_only_the_canonical_homepage(client):
    response = client.get("/sitemap.xml", headers={"host": "alternate.example"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    root = ElementTree.fromstring(response.text)
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    assert [node.text for node in root.findall("s:url/s:loc", namespace)] == [
        f"{SITE_URL}/"
    ]
    assert not root.findall("s:url/s:lastmod", namespace)


@pytest.mark.parametrize(
    "path", ["/score-table", "/admin/login", "/admin/dashboard", "/admin/download"]
)
def test_utility_pages_are_not_indexable(client, path):
    response = client.get(path, follow_redirects=False)
    assert response.headers["x-robots-tag"] == "noindex"
    assert not Document(response.text).find("link", rel="canonical")


@pytest.mark.parametrize("path", ["/content.md", "/requirements.txt", "/package.json"])
def test_project_files_are_not_public_static_content(client, path):
    assert client.get(path).status_code == 404


def test_explicit_static_mount_still_serves_styles(client):
    response = client.get("/static/bundle.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
