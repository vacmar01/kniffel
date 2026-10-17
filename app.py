"""FastHTML application initialization."""
from fasthtml.common import *
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles
from config import ADMIN_PASSWORD, ANALYTICS_DB

# Use an explicit /static mount instead of fast_app's project-root file route.
# That catch-all would intercept robots.txt/sitemap.xml and expose other files.
app = FastHTML(
    canonical=False,
    htmlkw={"lang": "de"},
    hdrs=(
        Link(rel="stylesheet", href="/static/bundle.css"),
        Script(src="/static/bundle.js", defer=""),
        Script(
            **{
                "src": "https://plausible.io/js/pa-18b2DkMlaQkIpNDpUM7Rm.js",
                "async": "",
            }
        ),
        Script(
            "window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};\n  plausible.init()"
        ),
    ),
    cls="bg-gray-50 flex flex-col min-h-screen",
)
rt = app.route

# Explicitly mount static files for Railway compatibility
app.mount("/static", StaticFiles(directory="static"), name="static")

setup_toasts(app)


async def exclude_utility_pages_from_search(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path in {"/score-table", "/admin"} or path.startswith("/admin/"):
        response.headers["X-Robots-Tag"] = "noindex"
    return response


app.add_middleware(BaseHTTPMiddleware, dispatch=exclude_utility_pages_from_search)

# Import all route modules to register their handlers
from routes import main as main_routes
from routes import game as game_routes
from routes import admin as admin_routes
from routes import seo as seo_routes
from routes import statistics as statistics_routes
