# AGENTS.md

This file contains guidance for AI agents working on this codebase.

## Project Overview

This is an online Kniffel (Yahtzee) score tracker built with FastHTML, HTMX, AlpineJS and TailwindCSS. It's a web application that allows players to track scores without requiring user registration.

## Key Conventions

### Always Use `uv` for Python

Use `uv` for ALL Python operations - running tests, starting the app, installing packages

**Never use `python`, `pip`, or `pytest` directly** - always use `uv run` or `uv pip`.

### Testing

- prefer dependency injection over mocking. Refactor if you must. 

Quick reference:
```bash
# All tests
uv run pytest -v

# Just unit tests (fast)
uv run pytest test_main.py -v

# Browser tests with auto-started server
uv run pytest test_playwright.py -v

# Browser tests with visible browser
uv run pytest test_playwright.py -v --headed
```

## Important Notes

- Browser tests are isolated on port 5002, completely separate from dev server (5001)
- Test data does not interfere with manual testing
- Always check TESTING.md before modifying tests
- Use `uv` exclusively for Python operations
- The dev server is usually already started by the user. Always check whether the user has already started a dev server on port 5001 before starting it yourself
- The analytics database can be found in the data/ folder
