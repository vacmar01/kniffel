# Kniffelblock online

A free digital Kniffel (Yahtzee) scorecard for games with real dice. Track multiple
players on one device, with automatic totals and upper-section bonuses. No account
required.

**Use the scorecard: [online-kniffel.de](https://online-kniffel.de/)**

Built with FastHTML, HTMX, AlpineJS and TailwindCSS.

## Development

Use `uv` for all Python operations. Check whether port 5001 is already running
before starting another development server.

```bash
uv pip install -r requirements.txt
npm ci
uv run main.py
```

Open `http://localhost:5001`. After changing frontend classes, run `npm run build`
or use `npm run watch` during development.

See [TESTING.md](TESTING.md) for isolated unit/browser tests and
[SEO.md](SEO.md) for deployment and search-performance checks.
