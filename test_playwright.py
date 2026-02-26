"""
Playwright-based browser integration tests for Kniffel.
These test the actual user interactions that HTMX route tests can't verify.
"""

import subprocess
import time
import socket
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
def base_url():
    """Base URL for the app - always starts fresh server on port 5002 for test isolation"""
    url = f"http://localhost:{TEST_PORT}"
    
    # Check if test port is already in use (another test run or leftover process)
    if wait_for_server("localhost", TEST_PORT, timeout=1):
        print(f"\nWarning: Port {TEST_PORT} already in use, attempting to use it...")
        yield url
        return
    
    # Start fresh server with uv on isolated port
    print(f"\nStarting test server on port {TEST_PORT}...")
    proc = subprocess.Popen(
        ["uv", "run", "main.py", str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to be ready
    if not wait_for_server("localhost", TEST_PORT, timeout=30):
        proc.terminate()
        proc.wait()
        raise RuntimeError(f"Server failed to start on port {TEST_PORT} within 30 seconds")
    
    print(f"Test server ready on port {TEST_PORT}!")
    
    yield url
    
    # Cleanup
    print("\nShutting down test server...")
    proc.terminate()
    proc.wait()


class TestKniffelBrowser:
    """Browser tests for Kniffel game"""
    
    def test_homepage_loads(self, page: Page, base_url: str):
        """Test that the homepage loads with correct content"""
        page.goto(base_url)
        
        # Check title
        expect(page).to_have_title("online-kniffel.de - Kniffelblock online")
        
        # Check for add player form
        expect(page.locator("input[placeholder='Spielername']")).to_be_visible()
        expect(page.locator("button", has_text="Hinzufügen")).to_be_visible()
    
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



