"""Game logic and scoring calculations."""
from models import categories, fixed_scores, upper_section


def calculate_scores(user_scores):
    """
    Calculate the scores for the game and return the upper total, bonus, and total as a tuple.
    """
    upper_total = sum(user_scores.get(cat, 0) or 0 for cat in upper_section)
    bonus = 35 if upper_total >= 63 else 0
    total = (
        upper_total
        + bonus
        + sum(
            user_scores.get(cat, 0) or 0
            for cat in categories
            if cat not in upper_section
        )
    )
    return upper_total, bonus, total


def is_fixed_score_category(category):
    """Check if a category has a fixed score."""
    return category in fixed_scores


def get_fixed_score_value(category):
    """Get the fixed score value for a category."""
    return fixed_scores.get(category)
