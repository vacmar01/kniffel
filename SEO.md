# SEO rollout checklist

## Scope

The public site is **https://online-kniffel.de/**. The former domain
`onlinekniffel.de` is no longer controlled by this project. Do not assume that
its links or search history transfer to the current domain.

The homepage targets digital-scorecard searches such as `kniffelblock online`,
`kniffel block online`, and `kniffel online ausfüllen`. It is not a virtual-dice
game, online multiplayer service, or computer opponent. Keep those related
scorecard searches on one useful page rather than creating duplicate landing
pages for every wording.

## After deployment

- Verify the player flow on desktop and mobile: add players, enter scores,
  reload, reset, and remove players. Existing browser sessions should still work.
- Check that `/` returns 200, uses German HTML language metadata, and contains
  exactly one canonical URL: `https://online-kniffel.de/`.
- Check that `/robots.txt` and `/sitemap.xml` return 200 with the correct content
  types and production URLs. The homepage and `/statistik/` belong in the sitemap;
  admin routes and HTMX fragments do not.
- Confirm HTTP redirects to HTTPS in hosting configuration. If you configure a
  `www` hostname, give it a valid certificate and permanently redirect it to the
  canonical hostname. Don't advertise hostnames that aren't configured.
- Inspect the homepage in Google Search Console: indexed status,
  Google-selected canonical, last crawl, and any fetch/render errors. The
  performance export alone cannot diagnose indexing or server-availability issues.
- Check Search Console's manual actions, security issues, and crawl statistics.
- Submit `https://online-kniffel.de/sitemap.xml` in Search Console. Request
  homepage indexing after deployment; repeated requests aren't a growth strategy.
- Record the deployment date to compare performance against a known baseline.

The admin and score-table fragment routes return `X-Robots-Tag: noindex`.
Crawlers aren't blocked from reading that directive. This is not access control;
admin routes must remain authenticated.

## Rebuild relevant links

- Set the GitHub repository's website/About link to the current production URL.
  The README already links there instead of the obsolete Railway demo.
- Update your own profiles or listings that still link to the former domain.
- If you can identify relevant sites mentioning the old scorecard, ask them to
  update the destination. You cannot change their links from this repository.
- Share the tool with genuinely relevant board-game resources. Avoid bought link
  packages, bulk directory submissions, and automated link exchanges.

## Measure the right outcomes

Save Search Console baselines for the homepage and the queries
`kniffel block online` and `kniffelblock online`. Compare equal-length periods,
consistent countries/devices, and clicks, impressions, CTR, and query-specific
positions. The blended site-wide position changes with the query mix and is not
an exact keyword ranking. Keep organic search clicks separate from total visits.

Review over several weeks, not daily fluctuations. Neither metadata changes,
structured data, nor a sitemap guarantee ranking recovery or rich results.
Keep private Search Console exports out of commits.

## Public statistics and future score benchmarks

`/statistik/` reads the deployment's existing analytics database and publishes
aggregate category entry counts, zero-point shares, and mean points per entry.
It uses the same schema locally and in production; no production export or
manual data import is needed. It excludes invalid scores, never changes the
database, and does not publish session identifiers or event metadata.

Automatic 28-day analytics deletion has been removed. Existing event logs still
lack the player/game identifiers and final scorecards needed for trustworthy
final-score statistics. Do not publish averages or percentiles from raw entry
events: corrections and incomplete games would bias them.

Before building a score-benchmark page:

1. Audit a production database export locally, without publishing player data.
2. Design anonymous game/player identifiers, completed scorecard snapshots,
   correction/deduplication behaviour, and score validity checks.
3. Review retention, access, and privacy disclosures. Long-term aggregated
   statistics need not mean indefinite retention of session-linked raw events.
4. Publish sample sizes, periods, exclusions, and the fact that observations
   describe this site's users, not all Kniffel players or theoretical dice odds.
5. Add a score-comparison page only when completed-scorecard data supports it.
   Expand where the data answers genuinely different questions.
