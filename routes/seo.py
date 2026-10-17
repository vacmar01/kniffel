"""Crawler discovery files listing only public, indexable content."""
from starlette.responses import PlainTextResponse, Response

from app import rt
from config import SITE_URL


@rt("/robots.txt")
def get():
    # Utility pages use noindex response headers, not crawl blocks, so crawlers
    # can read those directives. Neither mechanism replaces admin authentication.
    return PlainTextResponse(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    )


@rt("/sitemap.xml")
def get():
    # No synthetic lastmod: deploy/build dates aren't content modification dates.
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}/</loc></url>\n"
        f"  <url><loc>{SITE_URL}/statistik/</loc></url>\n"
        "</urlset>\n",
        media_type="application/xml",
    )
