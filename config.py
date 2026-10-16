"""Configuration and constants for the Kniffel application."""
import os
from pathlib import Path

# Ensure data directory exists
Path("data").mkdir(exist_ok=True)

# Public URL used in canonical links and crawler discovery files.
SITE_URL = "https://online-kniffel.de"

# Analytics database setup
ANALYTICS_DB = "data/analytics.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kniffel-admin-123")
