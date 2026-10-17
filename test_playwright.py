"""
Playwright-based browser integration tests for Kniffel.
These test the actual user interactions that HTMX route tests can't verify.
"""

import subprocess
import time
import socket
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


def wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    """Wait for server to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
    return False


TEST_PORT = 5002


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    """Start an isolated server and database, without touching the dev server."""
    url = f"http://127.0.0.1:{TEST_PORT}"
    if wait_for_server("127.0.0.1", TEST_PORT, timeout=1):
        pytest.fail(f"Port {TEST_PORT} is already in use; refusing to reuse its data")

    repo = Path(__file__).resolve().parent
    work = tmp_path_factory.mktemp("browser-server")
    (work / "static").symlink_to(repo / "static", target_is_directory=True)
    (work / "content.md").symlink_to(repo / "content.md")
    with (work / "server.log").open("w+") as log:
        proc = subprocess.Popen(
            [
                "uv", "run", "--no-project", "--python", sys.executable,
                "python", "-m", "uvicorn", "main:app", "--app-dir", str(repo),
                "--host", "127.0.0.1", "--port", str(TEST_PORT),
            ],
            cwd=work,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            if not wait_for_server("127.0.0.1", TEST_PORT, timeout=30):
                log.seek(0)
                pytest.fail(f"Test server failed to start:\n{log.read()}")
            yield url
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


class TestKniffelBrowser:
    """Browser tests for Kniffel game"""
    
    def test_homepage_loads(self, page: Page, base_url: str):
        """Test that the homepage loads with correct content"""
        page.goto(base_url)
        
        # Check title
        expect(page).to_have_title(
            "Kniffelblock online – kostenlos Punkte eintragen | online-kniffel.de"
        )
        
        # Check for add player form
        expect(page.locator("input[placeholder='Spielername']")).to_be_visible()
        expect(page.locator("button", has_text="Hinzufügen")).to_be_visible()
    
    def test_placeholder_without_javascript(self, browser, base_url: str):
        """The empty state is clear even before JavaScript runs."""
        context = browser.new_context(java_script_enabled=False)
        try:
            page = context.new_page()
            page.goto(base_url)
            expect(page.locator("h1")).to_have_count(1)
            expect(page.locator("#scorecard-placeholder")).to_be_visible()
            expect(page.get_by_role(
                "heading", name="Hier erscheint euer Kniffelblock"
            )).to_be_visible()
            expect(page.locator("#score-table input, #score-table select")).to_have_count(0)
        finally:
            context.close()

    def test_mobile_scorecard_and_reload(self, page: Page, base_url: str):
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(base_url)
        expect(page.locator("#scorecard-placeholder")).to_be_visible()
        for name in ["Anna", "Ben", "Clara", "David", "Eva"]:
            page.get_by_label("Spielername", exact=True).fill(name)
            page.get_by_role("button", name="Hinzufügen", exact=True).click()
            expect(page.get_by_role("columnheader", name=name + " ×")).to_be_visible()
        expect(page.locator("#scorecard-placeholder")).to_have_count(0)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        page.get_by_label("Punkte für Anna: Einser", exact=True).fill("3")
        page.get_by_label("Punkte für Anna: Einser", exact=True).blur()
        expect(page.locator("tr:has-text('Gesamtsumme') td").nth(1)).to_have_text("3")
        page.reload()
        expect(page.get_by_label("Punkte für Anna: Einser", exact=True)).to_have_value("3")
        expect(page.locator("#score-table-container")).to_have_count(1)

    def test_add_player(self, page: Page, base_url: str):
        """Test adding a player via HTMX"""
        page.goto(base_url)
        
        # Wait for HTMX to load the table
        page.wait_for_selector("#score-table", state="visible")
        
        # Add a player
        page.fill("input[name='username']", "TestPlayer")
        page.click("button:has-text('Hinzufügen')")
        
        # Wait for HTMX to update and verify player appears
        page.wait_for_selector("text=TestPlayer", state="visible")
        expect(page.locator("th", has_text="TestPlayer")).to_be_visible()
        expect(page.locator("#scorecard-placeholder")).to_have_count(0)
    
    def test_enter_variable_score(self, page: Page, base_url: str):
        """Test entering a variable score (Einser)"""
        page.goto(base_url)
        
        # Wait for table and add player
        page.wait_for_selector("#score-table", state="visible")
        page.fill("input[name='username']", "ScoreTester")
        page.click("button:has-text('Hinzufügen')")
        page.wait_for_selector("text=ScoreTester", state="visible")
        
        # Find the Einser input for this player and enter a score
        # The input is in the row with "Einser" text
        einser_input = page.locator("tr:has-text('Einser') >> input[type='number']").first
        einser_input.fill("15")
        einser_input.blur()  # Trigger HTMX submit on blur
        
        # Wait for the update and verify total
        page.wait_for_timeout(500)  # Give HTMX time to update
        
        # Check that 15 appears in the table
        expect(page.locator("td", has_text="15").first).to_be_visible()
    
    def test_enter_fixed_score(self, page: Page, base_url: str):
        """Test entering a fixed score (Full House)"""
        page.goto(base_url)
        
        # Setup: add player
        page.wait_for_selector("#score-table", state="visible")
        page.fill("input[name='username']", "FixedScoreTester")
        page.click("button:has-text('Hinzufügen')")
        page.wait_for_selector("text=FixedScoreTester", state="visible")
        
        # Scroll to find Full House row - look for the row with Full House followed by ⓘ icon
        full_house_row = page.get_by_role("row", name="Full Houseⓘ")
        full_house_row.scroll_into_view_if_needed()
        
        # Select "Gewürfelt" from dropdown
        select = full_house_row.locator("select").first
        select.select_option("Gewürfelt")
        
        # Wait for HTMX update
        page.wait_for_timeout(500)
        
        # Verify the score appears (25 points)
        expect(page.locator("td", has_text="25").first).to_be_visible()
    
    def test_totals_calculated(self, page: Page, base_url: str):
        """Test that totals are calculated correctly"""
        page.goto(base_url)
        
        # Setup: add player and enter scores
        page.wait_for_selector("#score-table", state="visible")
        page.fill("input[name='username']", "TotalTester")
        page.click("button:has-text('Hinzufügen')")
        page.wait_for_selector("text=TotalTester", state="visible")
        
        # Enter Einser = 15
        einser_input = page.locator("tr:has-text('Einser') >> input[type='number']").first
        einser_input.fill("15")
        einser_input.blur()
        page.wait_for_timeout(500)
        
        # Scroll to Full House and select it - look for the row with Full House followed by ⓘ icon
        full_house_row = page.get_by_role("row", name="Full Houseⓘ")
        full_house_row.scroll_into_view_if_needed()
        select = full_house_row.locator("select").first
        select.select_option("Gewürfelt")
        page.wait_for_timeout(500)
        
        # Scroll to see totals
        totals_row = page.locator("tr:has-text('Gesamtsumme')")
        totals_row.scroll_into_view_if_needed()
        
        # Verify total shows 40 (15 + 25)
        expect(page.locator("td", has_text="40").first).to_be_visible()
    
    def test_reset_scores(self, page: Page, base_url: str):
        """Test resetting all scores"""
        page.goto(base_url)
        
        # Setup: add player and enter a score
        page.wait_for_selector("#score-table", state="visible")
        page.fill("input[name='username']", "ResetTester")
        page.click("button:has-text('Hinzufügen')")
        page.wait_for_selector("text=ResetTester", state="visible")
        
        # Enter a score
        einser_input = page.locator("tr:has-text('Einser') >> input[type='number']").first
        einser_input.fill("10")
        einser_input.blur()
        page.wait_for_timeout(500)
        
        # Set up dialog handler BEFORE clicking reset
        page.on("dialog", lambda dialog: dialog.accept())
        
        # Click reset button
        reset_btn = page.locator("button:has-text('zurücksetzen')")
        reset_btn.scroll_into_view_if_needed()
        reset_btn.click()
        
        # Wait for reset - HTMX replaces the element, so we need to find it again
        page.wait_for_timeout(1000)
        
        # After reset, find the input again (old reference is stale) and check it's empty
        einser_input_after = page.locator("tr:has-text('Einser') >> input[type='number']").first
        expect(einser_input_after).to_have_value("")
    
    def test_statistics_link_and_mobile_layout(self, page: Page, browser, base_url: str):
        page.goto(base_url)
        page.get_by_label("Spielername", exact=True).fill("StatistikTest")
        page.get_by_role("button", name="Hinzufügen", exact=True).click()
        score = page.get_by_label("Punkte für StatistikTest: Einser", exact=True)
        score.fill("3")
        score.blur()
        expect(page.locator("tr:has-text('Gesamtsumme') td").nth(1)).to_have_text("3")
        page.get_by_role("link", name="Kniffel-Statistik", exact=True).click()
        expect(page).to_have_url(base_url + "/statistik/")
        expect(page.locator("#category-statistics")).to_be_visible()
        expect(page.get_by_text("StatistikTest", exact=True)).to_have_count(0)
        expect(page.locator("#methodik")).to_have_count(0)

        context = browser.new_context(
            java_script_enabled=False, viewport={"width": 390, "height": 844}
        )
        try:
            mobile = context.new_page()
            mobile.goto(base_url + "/statistik/")
            expect(mobile.locator("#category-statistics")).to_be_visible()
            assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            context.close()

    def test_delete_player(self, page: Page, base_url: str):
        """Test deleting a player"""
        page.goto(base_url)
        
        # Setup: add player
        page.wait_for_selector("#score-table", state="visible")
        page.fill("input[name='username']", "DeleteMe")
        page.click("button:has-text('Hinzufügen')")
        page.wait_for_selector("text=DeleteMe", state="visible")
        
        # Set up dialog handler BEFORE clicking delete
        page.on("dialog", lambda dialog: dialog.accept())
        
        # Find and click delete button (× symbol) - specifically in the table header
        delete_btn = page.locator("th button:has-text('×')").first
        delete_btn.click()
        
        # Wait for deletion and verify player is gone from table
        page.wait_for_timeout(1000)
        # Check that the player name is not in any table header
        expect(page.locator("th:has-text('DeleteMe')")).not_to_be_visible()
        expect(page.locator("#scorecard-placeholder")).to_be_visible()



