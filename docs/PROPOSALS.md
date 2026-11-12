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
| 5 | Publish the repository and push daily | The experiment is more fun in public, and CI becomes possible | The agent still has no push rights. The runner pushes a branch from outside the sandbox after tests and a secret scan, then opens a PR for a human to merge | done, needs a GitHub token (see below) |
| 6 | Move to the newest model on release | The project should get smarter as models improve. The runner uses the `opus` alias, which tracks new releases | Daily usage may grow | done |
| 7 | `read_arxiv_paper` tool in `ass-research`, returning a paper's plain text and tables | Constants come from tables, and today's only route to them runs through a summarising model, so each value had to be read twice with no raw text to compare against. A do-it-yourself fetch script needs approval that an unattended run does not get | Low; read-only. Paper text is untrusted, so it widens the prompt-injection surface slightly. Changing the MCP server's registration stays with the human. Iteration 4 needed four page reads to learn one sign convention, because the summariser reports what a page "does not say" rather than quoting equations | open |
| 8 | `query_vizier` tool in `ass-research`, for catalogue tables by name (for example Boyajian+ 2012 Table 6) | Stellar radii, luminosities and temperatures are published as machine-readable tables in VizieR, and an abstract rarely carries them. Iteration 5 spent three of its five lookups on abstracts that held no radius, and Proxima's radius is still unsourced. One table query would have answered it with raw numbers and no summariser | Low; read-only, free, with a public TAP endpoint (astroquery already supports it). Catalogue tables are data rather than prose, so they carry little prompt-injection risk. Adding the tool and registering it stays with the human | open |

## Enabling pull requests

Create a [fine-grained token](https://github.com/settings/personal-access-tokens/new) for this
repository only, with **Pull requests: read and write** and nothing else, and store it for the runner.
Without it, branches are still pushed and the log has a link for opening the PR by hand.

```bash
mkdir -p ~/.config/ass && (umask 077; read -rs -p "GitHub token: " t && echo "$t" > ~/.config/ass/github_token)
```

Then, in the repository settings on GitHub:

- Turn on **Automatically delete head branches**. The agent waits until the iteration branch is gone,
  so a closed but undeleted branch stalls it.
- Add a branch ruleset for `main` that requires a pull request and the `test` status check.

## Enabling NASA ADS

Create a free token at <https://ui.adsabs.harvard.edu/user/settings/token>, then store it where the
daily runner looks for it. The runner passes it to the agent as `ADS_API_TOKEN`, and the secret scan
refuses to publish any commit containing it.

```bash
mkdir -p ~/.config/ass && (umask 077; read -rs -p "ADS token: " t && echo "$t" > ~/.config/ass/ads_token)
```
