"""FastHTML application initialization."""
from fasthtml.common import *
from starlette.staticfiles import StaticFiles
from config import ADMIN_PASSWORD, ANALYTICS_DB

app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel="stylesheet", href="/static/bundle.css"),
        Script(src="/static/bundle.js", defer=""),
        Meta(
            name="description",
            content="Kniffelblock online - kostenlos, ohne Registrierung",
        ),
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
    bodykw={"class": "bg-gray-50 flex flex-col min-h-screen"},
)

# Explicitly mount static files for Railway compatibility
app.mount("/static", StaticFiles(directory="static"), name="static")

setup_toasts(app)

# Import all route modules to register their handlers
from routes import main as main_routes
from routes import game as game_routes
from routes import admin as admin_routes
