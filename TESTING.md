# Testing

This project has both unit tests and browser-based integration tests.

## Unit Tests (test_main.py)

Run with pytest:

```bash
source .venv/bin/activate
python -m pytest test_main.py -v
```

### Current Coverage (14 tests)

**Core Logic (7 tests):**
- `calculate_scores()` - Empty, upper section only, with bonus, combined upper+lower
- Data structures - categories, fixed_scores, upper_section definitions

**Route Handlers (6 tests):**
- `GET /` - Homepage loads
- `POST /add-user` - Add player
- `POST /add-user` (duplicate) - Prevents duplicates
- `POST /update-score` - Update scores
- `POST /delete-user` - Remove player
- `POST /reset-scores` - Reset all scores

**Integration (1 test):**
- `test_full_game_flow` - Multi-step workflow testing state persistence across requests

## Browser Integration Tests (test_playwright.py)

These test the actual HTMX interactions and UI behavior that route tests can't verify.
Uses **Playwright** with pytest for proper test isolation and debugging.

### Prerequisites

```bash
# Install playwright and browsers
uv pip install playwright pytest-playwright
playwright install chromium
```

### Running Browser Tests

**Tests use port 5002** (isolated from your dev server on port 5001):

```bash
# Run browser tests (auto-starts fresh server on port 5002)
pytest test_playwright.py -v

# Or run with visible browser (for debugging)
pytest test_playwright.py -v --headed

# Run with trace viewer (great for debugging)
pytest test_playwright.py -v --tracing=retain-on-failure
```

**Port isolation:**
- Your manual dev server: `http://localhost:5001` (unchanged)
- Browser tests: `http://localhost:5002` (isolated, clean state)

This means you can keep your dev server running with any data while tests run independently.

### What Browser Tests Cover

1. **test_homepage_loads** - Verify title and form presence
2. **test_add_player** - HTMX adds player to table without page reload
3. **test_enter_variable_score** - Number inputs update on blur
4. **test_enter_fixed_score** - Dropdowns for categories like Full House
5. **test_totals_calculated** - Verify scores sum correctly (15 + 25 = 40)
6. **test_reset_scores** - Button clears all scores
7. **test_delete_player** - Remove player from game

### Why Both?

**Route tests (fast, ~1s):**
- ✓ Business logic validation
- ✓ HTTP responses
- ✓ Session management
- ✗ Can't test HTMX behavior
- ✗ Can't test JavaScript interactions

**Playwright tests (slower, ~10s):**
- ✓ Tests actual user flows
- ✓ Verifies HTMX partial updates work
- ✓ Catches JavaScript/AlpineJS issues
- ✓ Proper test isolation (fresh browser per test)
- ✓ Auto-screenshots on failure
- ✗ Slower (browser startup)
- ✗ More brittle (UI changes break tests)

## CI/CD Recommendations

For CI, run unit tests always:
```bash
pytest test_main.py
```

Run browser tests before releases or on schedule:
```bash
pytest test_main.py && ./test_browser.py
```

## Adding New Tests

### Unit Test Example

```python
def test_new_feature():
    """Test description"""
    client.post("/add-user", data={"username": "Test"})
    response = client.post("/some-endpoint", data={"value": "123"})
    assert response.status_code == 200
    assert b"expected" in response.content
```

### Browser Test Example

```python
def test_new_ui_feature(self, page: Page, base_url: str):
    """Test description"""
    page.goto(base_url)
    
    # Interact with elements
    page.fill("input[name='field']", "value")
    page.click("button:has-text('Submit')")
    
    # Wait for HTMX update
    page.wait_for_timeout(500)
    
    # Assert with expect()
    expect(page.locator("text=Expected Result")).to_be_visible()
```

## Debugging Failed Tests

**Unit tests:**
```bash
pytest test_main.py::test_name -v --tb=short
```

**Playwright tests:**
```bash
# Run with visible browser
pytest test_playwright.py -v --headed

# Run with trace (creates trace.zip for debugging)
pytest test_playwright.py -v --tracing=on

# View trace
playwright show-trace test-results/trace.zip

# Screenshot on failure (automatic with pytest-playwright)
# Check test-results/ directory after failed run
```
