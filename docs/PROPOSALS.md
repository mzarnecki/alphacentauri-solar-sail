# Proposals

Wider improvements that need a human decision: new tools, access, money or changes to the agent's
own automation. The agent adds to this list and must not act on it by itself.

Status is one of: `open`, `accepted`, `rejected`, `done`.

| # | Proposal | Why | Cost and risk | Status |
|---|---|---|---|---|
| 1 | arXiv MCP server | Structured search of astro-ph and physics.space-ph rather than scraping search pages | Low; read-only | done: `search_arxiv` in `ass.research` |
| 2 | NASA ADS MCP or API access | Citation graphs for the sail literature that arXiv does not have | Free API token | done: `search_ads`, waiting for a token (see below) |
| 3 | SIMBAD and Gaia archive access | Star data from the source of truth, for the ephemeris | Low; read-only | done: `query_simbad`, `query_gaia` |
| 4 | Astronomy forum reader (Cloudy Nights, r/space, Centauri Dreams) | Catches ideas before they reach a paper | Content is unreviewed and is a prompt-injection surface | done: `read_feed` for r/space and Centauri Dreams. Cloudy Nights answers bots with 403 and offers no feed, so it is left out |
| 5 | Publish the repository and push daily | The experiment is more fun in public, and CI becomes possible | The agent still has no push rights. The runner pushes from outside the sandbox after tests and a secret scan | done |
| 6 | Move to the newest model on release | The project should get smarter as models improve. The runner uses the `opus` alias, which tracks new releases | Daily usage may grow | done |

## Enabling NASA ADS

Create a free token at <https://ui.adsabs.harvard.edu/user/settings/token>, then store it where the
daily runner looks for it. The runner passes it to the agent as `ADS_API_TOKEN`, and the secret scan
refuses to publish any commit containing it.

```bash
mkdir -p ~/.config/ass && (umask 077; read -rs -p "ADS token: " t && echo "$t" > ~/.config/ass/ads_token)
```
