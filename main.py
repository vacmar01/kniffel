"""Kniffel (Yahtzee) score tracker - Main entry point.

This is a minimal entry point that imports all modules and starts the server.
All business logic is organized in:
- config.py: Configuration and constants
- models.py: Game data models
- app.py: FastHTML app initialization and route registration
- services/: Business logic (game scoring, analytics)
- components/: UI components
- routes/: HTTP route handlers
"""
import sys

# Import app (triggers route registration via app.py imports)
from app import app

# Initialize analytics database on startup
from services.analytics import init_analytics_db
init_analytics_db()

# Get port from command line, but only if it looks like a port number
port = 5001
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        pass  # Not a valid port, use default

if __name__ == "__main__":
    from fasthtml.common import serve
    serve(port=port)
