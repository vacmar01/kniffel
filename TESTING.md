# Testing

Always use `uv` for Python commands.

## Unit and route tests

```bash
uv run pytest test_main.py test_analytics.py test_homepage.py -v
```

Route tests use the shared `client` fixture in `conftest.py`. Each test gets a
fresh client/session and a real SQLite database in a temporary working directory.
The development database in `data/analytics.db` is never used. Analytics tests
inject a temporary database path directly, without mocking SQLite.

Core coverage includes scoring, category definitions, player management, score
entry, reset, and a complete multi-player workflow. Homepage tests check semantic
headings, the empty-state placeholder and real scorecards, metadata, structured data,
canonical URLs, crawler discovery files, and utility-page indexing directives.

## Browser integration tests

Install browser dependencies if needed:

```bash
uv pip install playwright pytest-playwright
uv run playwright install chromium
npm run build
```

Run the tests:

```bash
uv run pytest test_playwright.py -v
uv run pytest test_playwright.py -v --headed
uv run pytest test_playwright.py -v --tracing=retain-on-failure
```

The fixture starts its own server on **port 5002** with a temporary working
directory and database. It fails rather than reusing an already occupied port.
The development server on **port 5001** is left untouched. The test server's log
is in its pytest temporary directory (`browser-server*/server.log`).

Browser tests cover the actual HTMX flow: adding and removing players, entering
variable/fixed scores, calculating totals, and confirming resets. They also check
the placeholder without JavaScript, its replacement when adding the first player,
its return after removing the last player, and mobile entry/reload with several
players. Build frontend assets
before testing changes that introduce Tailwind classes.

## All tests

```bash
uv run pytest -v
```

Run unit/route tests for each backend change and browser tests before releasing
changes to the scorecard or homepage.

## Adding tests

Use dependency injection and temporary real databases instead of mocking.

```python
def test_new_route(client):
    response = client.get("/")
    assert response.status_code == 200
```

For browser tests, prefer Playwright's retrying assertions over fixed sleeps:

```python
def test_player_added(page, base_url):
    page.goto(base_url)
    page.get_by_placeholder("Spielername").fill("Test")
    page.get_by_role("button", name="Hinzufügen").click()
    expect(page.get_by_role("columnheader", name="Test")).to_be_visible()
```

## Debugging

```bash
uv run pytest test_main.py::test_full_game_flow -v --tb=short
uv run pytest test_playwright.py -v --headed
uv run playwright show-trace test-results/trace.zip
```
