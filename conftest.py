"""Shared test fixtures; never write gameplay events to the local database."""
from contextlib import chdir
from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    """Give each route test a fresh session and a real, temporary database."""
    repo = Path(__file__).resolve().parent
    (tmp_path / "static").symlink_to(repo / "static", target_is_directory=True)
    (tmp_path / "content.md").symlink_to(repo / "content.md")
    with chdir(tmp_path):
        from app import app
        from services.analytics import init_analytics_db

        (tmp_path / "data").mkdir()
        init_analytics_db()
        with TestClient(app) as test_client:
            yield test_client
