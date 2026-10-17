"""Public page metadata, independent of request host and session data."""
import json

from fasthtml.common import Link, Meta, Script, Title

from config import SITE_URL

HOME_TITLE = "Kniffelblock online – kostenlos Punkte eintragen | online-kniffel.de"
HOME_DESCRIPTION = (
    "Kostenloser Kniffelblock online: Punkte für mehrere Spieler "
    "eintragen, Summen und Bonus automatisch berechnen. "
    "Mit echten Würfeln spielen, ohne Anmeldung."
)


def PageMetadata(title, description, path):
    return (
        Title(title),
        Meta(name="description", content=description),
        Link(rel="canonical", href=f"{SITE_URL}{path}"),
        Meta(property="og:type", content="website"),
        Meta(property="og:locale", content="de_DE"),
        Meta(property="og:site_name", content="online-kniffel.de"),
        Meta(property="og:url", content=f"{SITE_URL}{path}"),
        Meta(property="og:title", content=title),
        Meta(property="og:description", content=description),
        Meta(name="twitter:card", content="summary"),
        Meta(name="twitter:title", content=title),
        Meta(name="twitter:description", content=description),
    )


def HomepageMetadata():
    return (
        *PageMetadata(HOME_TITLE, HOME_DESCRIPTION, "/"),
        Script(
            json.dumps({
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": "Kniffelblock online",
                "url": f"{SITE_URL}/",
                "description": HOME_DESCRIPTION,
                "inLanguage": "de",
                "applicationCategory": "GameApplication",
                "operatingSystem": "Any",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
            }, ensure_ascii=False),
            type="application/ld+json",
        ),
    )
