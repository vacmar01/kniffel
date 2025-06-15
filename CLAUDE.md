# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an online Kniffel (Yahtzee) score tracker built with FastHTML, HTMX, AlpineJS and TailwindCSS. It's a single-file web application that allows players to track scores for the dice game Kniffel without requiring user registration.

## Architecture

- **Single-file application**: All server logic is contained in `main.py`
- **Session-based storage**: User data and scores are stored in browser sessions (no database)
- **Real-time updates**: Uses HTMX for dynamic score updates without page refreshes
- **Component-based HTML**: Functions return FastHTML components that generate HTML
- **Responsive design**: Uses TailwindCSS via CDN for styling

## Key Components

- **Score calculation logic**: `calculate_scores()` handles upper section bonus (35 points for ≥63) and totals
- **Dynamic score inputs**: `ScoreInput()` creates different input types for fixed-score vs variable-score categories
- **Session management**: Players and scores stored in `session["users"]` and `session["scores"]`
- **HTMX integration**: Score updates trigger server requests that return updated table HTML

## Common Development Commands

```bash
# Run the development server
python main.py

# Install dependencies
pip install -r requirements.txt
```

## Game Logic Rules

- Upper section categories (Einser-Sechser) count matching dice
- Fixed-score categories have predetermined values (Full House: 25, Kniffel: 50, etc.)
- Upper section bonus: 35 points when sum ≥ 63
- Session stores: `users` (list of player names), `scores` (nested dict: user -> category -> value)

## Analytics Integration

Uses Plausible analytics for tracking user interactions. Event tracking is implemented for key actions like adding players and accessing "more info".