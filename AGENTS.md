# AGENTS.md

This file contains guidance for AI agents working on this codebase.

## Project Overview

This is an online Kniffel (Yahtzee) score tracker built with FastHTML, HTMX, AlpineJS and TailwindCSS. It's a single-file web application that allows players to track scores without requiring user registration.

## Key Conventions

### Always Use `uv` for Python

Use `uv` for ALL Python operations - running tests, starting the app, installing packages:

```bash
# Run tests
uv run pytest test_main.py -v

# Run browser tests
uv run pytest test_playwright.py -v

# Start the development server
uv run main.py              # Uses port 5001 (default)
uv run main.py 5002         # Uses custom port

# Install packages
uv pip install <package>
```

**Never use `python`, `pip`, or `pytest` directly** - always use `uv run` or `uv pip`.

### Testing

The project has comprehensive testing documented in **TESTING.md**. Always refer to it for:
- How to run unit tests (14 tests in `test_main.py`)
- How to run browser tests (7 tests in `test_playwright.py`)
- Test isolation (browser tests use port 5002)
- Debugging tips

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

### Architecture

- **Single-file application**: All server logic is in `main.py`
- **Session-based storage**: User data stored in browser sessions (no database)
- **Real-time updates**: Uses HTMX for dynamic score updates without page refreshes
- **Port configuration**: Server accepts optional port argument (default 5001)

### Frontend Stack

- **Tailwind CSS v4** - CSS framework via `@tailwindcss/vite` plugin
- **HTMX** - For dynamic updates without page reloads
- **AlpineJS** - For client-side interactivity (tooltips, etc.)
- **Vite** - Build tool bundling everything together

**Important**: After making changes to `assets/`, you must rebuild:

```bash
# Build everything (CSS + JS bundle via Vite)
npm run build

# Watch mode (auto-rebuild on changes - run in separate terminal)
npm run watch
```

**File structure:**
- `assets/main.js` - Entry point importing CSS, HTMX, and Alpine
- `assets/tailwind.css` - Tailwind CSS entry file
- `static/bundle.css` - Compiled CSS (output by Vite)
- `static/bundle.js` - Compiled JS bundle (output by Vite)

Vite processes everything through a single build step, outputting both CSS and JS to `static/`.

### Common Development Tasks

```bash
# Run dev server
uv run main.py

# Run tests
uv run pytest -v

# Run specific test
uv run pytest test_main.py::test_calculate_scores_with_bonus -v

# Build everything (CSS + JS bundle)
npm run build

# Watch mode (auto-rebuild on changes)
npm run watch
```

## Files Structure

```
main.py              # Main application (FastHTML, routes, logic)
test_main.py         # Unit tests (HTTP routes, scoring logic)
test_playwright.py   # Browser tests (HTMX interactions, UI)
TESTING.md           # Comprehensive testing documentation
requirements.txt     # Python dependencies
```

## Important Notes

- Browser tests are isolated on port 5002, completely separate from dev server (5001)
- Test data does not interfere with manual testing
- Always check TESTING.md before modifying tests
- Use `uv` exclusively for Python operations
