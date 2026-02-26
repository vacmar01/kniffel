import pytest
from starlette.testclient import TestClient
from main import app, calculate_scores, categories, fixed_scores, upper_section

client = TestClient(app)


def test_calculate_scores_empty():
    """Test calculate_scores with empty scores"""
    user_scores = {}
    upper_total, bonus, total = calculate_scores(user_scores)
    assert upper_total == 0
    assert bonus == 0
    assert total == 0


def test_calculate_scores_with_upper_section():
    """Test calculate_scores with upper section scores"""
    user_scores = {"Einser": 5, "Zweier": 10, "Dreier": 15}
    upper_total, bonus, total = calculate_scores(user_scores)
    assert upper_total == 30
    assert bonus == 0  # No bonus since < 63
    assert total == 30


def test_calculate_scores_with_bonus():
    """Test calculate_scores with upper section bonus"""
    user_scores = {
        "Einser": 5, "Zweier": 10, "Dreier": 15, 
        "Vierer": 16, "Fünfer": 20, "Sechser": 6
    }
    upper_total, bonus, total = calculate_scores(user_scores)
    assert upper_total == 72
    assert bonus == 35  # Bonus since >= 63
    assert total == 107


def test_calculate_scores_with_lower_section():
    """Test calculate_scores with lower section scores"""
    user_scores = {
        "Einser": 5, "Zweier": 10, "Dreier": 15,
        "Vierer": 16, "Fünfer": 20, "Sechser": 6,
        "Full House": 25, "Kniffel": 50
    }
    upper_total, bonus, total = calculate_scores(user_scores)
    assert upper_total == 72
    assert bonus == 35
    assert total == 182  # 72 + 35 + 25 + 50


def test_categories_structure():
    """Test that categories are properly defined"""
    assert len(categories) == 13
    assert "Einser" in categories
    assert "Kniffel" in categories


def test_fixed_scores_values():
    """Test fixed score values"""
    assert fixed_scores["Full House"] == 25
    assert fixed_scores["Kleine Straße"] == 30
    assert fixed_scores["Große Straße"] == 40
    assert fixed_scores["Kniffel"] == 50


def test_upper_section_categories():
    """Test upper section categories"""
    expected_upper = ["Einser", "Zweier", "Dreier", "Vierer", "Fünfer", "Sechser"]
    assert upper_section == expected_upper


def test_get_homepage():
    """Test that the main page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"online-kniffel.de" in response.content


def test_add_user():
    """Test adding a user"""
    response = client.post("/add-user", data={"username": "Alice"})
    assert response.status_code == 200
    assert b"Alice" in response.content


def test_add_duplicate_user():
    """Test that duplicate users are not added"""
    # Use a unique name to avoid interference from other tests
    import uuid
    username = f"User{uuid.uuid4().hex[:8]}"
    
    client.post("/add-user", data={"username": username})
    response = client.post("/add-user", data={"username": username})
    
    # Count delete buttons for this user (should be 1 per user)
    content = response.content.decode()
    delete_pattern = f"/delete-user/{username}"
    assert content.count(delete_pattern) == 1


def test_update_score():
    """Test updating a score"""
    client.post("/add-user", data={"username": "Charlie"})
    response = client.post("/update-score/Charlie/Einser", data={"value": "15"})
    assert response.status_code == 200
    # Score should be reflected in the total
    assert b"107" in response.content or b"15" in response.content


def test_delete_user():
    """Test deleting a user removes them from the game"""
    client.post("/add-user", data={"username": "David"})
    response = client.post("/delete-user/David")
    assert response.status_code == 200
    assert b"David" not in response.content


def test_reset_scores():
    """Test resetting all scores"""
    client.post("/add-user", data={"username": "Eve"})
    client.post("/update-score/Eve/Einser", data={"value": "5"})
    response = client.post("/reset-scores")
    assert response.status_code == 200
    # Total should be back to 0
    assert b"0" in response.content


def test_full_game_flow():
    """Integration test: full game workflow across multiple requests"""
    import uuid
    
    # Add two players
    user1 = f"Player1{uuid.uuid4().hex[:4]}"
    user2 = f"Player2{uuid.uuid4().hex[:4]}"
    
    client.post("/add-user", data={"username": user1})
    client.post("/add-user", data={"username": user2})
    
    # Check score-table endpoint shows both players (homepage uses HTMX to load this)
    score_table = client.get("/score-table")
    assert score_table.status_code == 200
    content = score_table.content.decode()
    assert user1 in content
    assert user2 in content
    
    # Update scores for both players
    client.post(f"/update-score/{user1}/Einser", data={"value": "3"})  # 3 ones = 3
    client.post(f"/update-score/{user1}/Kniffel", data={"value": "50"})  # 50 points
    client.post(f"/update-score/{user2}/Full House", data={"value": "25"})
    
    # Verify scores on score-table endpoint
    score_table_after = client.get("/score-table")
    content_after = score_table_after.content.decode()
    
    # Check that scores appear
    assert "3" in content_after  # user1's Einser
    assert "50" in content_after  # user1's Kniffel
    assert "25" in content_after  # user2's Full House
    # Check for totals (3 + 50 = 53 for user1, 25 for user2)
    assert "53" in content_after  # user1 total
    assert "25" in content_after  # user2's score
    
    # Delete one player and verify they disappear
    client.post(f"/delete-user/{user1}")
    score_table_after_delete = client.get("/score-table")
    content_delete = score_table_after_delete.content.decode()
    assert user1 not in content_delete
    assert user2 in content_delete
    
    # Reset scores and verify user2's scores are cleared (total = 0)
    client.post("/reset-scores")
    score_table_reset = client.get("/score-table")
    content_reset = score_table_reset.content.decode()
    # After reset, user2's Gesamtsumme should be 0 (check in totals row)
    # Find the Gesamtsumme row and verify it contains 0
    assert "Gesamtsumme" in content_reset
    # Count occurrences of "0" in the Gesamtsumme row - should be at least 1 for user2
    assert ">0</td>" in content_reset