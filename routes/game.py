"""Game routes for player and score management."""
from fasthtml.common import *
from app import rt, add_toast
from components.game import ScoreTableContainer
from services.analytics import log_event
from models import fixed_scores


@rt("/add-user")
def post(session, username: str):
    """
    Add a user to the game.
    """
    users = session.get("users", [])
    if username and username not in users:
        users.append(username.strip())
        session["users"] = users
        log_event(session, "player_added")

    add_toast(session, f"{username} wurde hinzugefügt", "success")
    return ScoreTableContainer(session)


@rt("/delete-user/{username}")
def post(session, username: str):
    """
    Delete a user from the game.
    """
    users = session.get("users", [])
    if username in users:
        users.remove(username)
        session["users"] = users
        scores = session.get("scores", {})
        if username in scores:
            del scores[username]
            session["scores"] = scores
        log_event(session, "player_removed")
    return ScoreTableContainer(session)


@rt("/score-table")
def get(session):
    """
    Get the score table container HTML element for the game.
    """
    return ScoreTableContainer(session)


@rt("/update-score/{user}/{category}")
def post(session, user: str, category: str, value: str):
    """
    Update the score for a user and category.
    """
    scores = session.get("scores", {})
    scores.setdefault(user, {})

    if value == "":
        scores[user][category] = None
        log_event(session, "score_cleared", category=category)
    elif category in fixed_scores:
        if value == "0":  # "Gestrichen"
            scores[user][category] = 0
            log_event(session, "score_crossed_out", category=category, value=0)
        else:  # "Gewürfelt"
            scores[user][category] = fixed_scores[category]
            log_event(
                session,
                "score_entered",
                category=category,
                value=fixed_scores[category],
            )
    else:
        int_value = int(float(value)) if value else None
        scores[user][category] = int_value
        if int_value is not None:
            log_event(session, "score_entered", category=category, value=int_value)

    session["scores"] = scores
    return ScoreTableContainer(session)


@rt("/reset-scores")
def post(session):
    """
    Reset the scores for all users.
    """
    session["scores"] = {user: {} for user in session.get("users", [])}
    log_event(session, "scores_reset")
    return ScoreTableContainer(session)
