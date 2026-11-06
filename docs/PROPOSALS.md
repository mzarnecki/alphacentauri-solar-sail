# Proposals

Wider improvements that need a human decision: new tools, access, money or changes to the agent's
own automation. The agent adds to this list and must not act on it by itself.

Status is one of: `open`, `accepted`, `rejected`, `done`.

| # | Proposal | Why | Cost and risk | Status |
|---|---|---|---|---|
| 1 | arXiv MCP server | Structured search of astro-ph and physics.space-ph rather than scraping search pages | Low; read-only | open |
| 2 | NASA ADS MCP or API access | Citation graphs for the sail literature that arXiv does not have | Free API token | open |
| 3 | SIMBAD and Gaia archive access | Star data from the source of truth, for the ephemeris | Low; read-only | open |
| 4 | Astronomy forum reader (Cloudy Nights, r/space, Centauri Dreams) | Catches ideas before they reach a paper | Content is unreviewed and is a prompt-injection surface | open |
| 5 | Publish the repository and push daily | The experiment is more fun in public, and CI becomes possible | The agent has no push rights by design; a push step would run outside its sandbox after review | open |
| 6 | Move to the newest model on release | The project should get smarter as models improve. The runner uses the `opus` alias, which tracks new releases | Daily usage may grow | open |
