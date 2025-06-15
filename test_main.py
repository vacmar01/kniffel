import pytest
from main import calculate_scores, categories, fixed_scores, upper_section


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