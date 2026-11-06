# Development log

Newest first. One entry per iteration, written for a future reader who has no memory of this
project, which includes the agent.

## Human change, 2026-11-06: review through pull requests

**Shipped:** the runner now pushes `iteration/*` branches and opens PRs, and never touches `main`. Each
PR carries a checklist for scientific claims and public copy. One iteration awaits review at a time.

**Why:** tests and the secret scan cannot tell whether the science is right. They all passed while the
star constants disagreed with SIMBAD. Someone has to own that question, and now the process says who.

## Iteration 2, 2026-11-06

**Shipped:** all six proposals: an `ass-research` MCP server (arXiv, ADS, SIMBAD, Gaia, feeds), a daily
push gated by tests and a secret scan, and CI. Also the mission control demo app, and a tighter agent
sandbox now that its commits become public.

**Learned:** the first comparison with SIMBAD found real disagreements in parallax and radial velocity,
now on the roadmap. Cloudy Nights does not want bots, and Reddit rate-limits quickly. systemd's home
sandboxing does nothing in user units on this machine, and it says nothing about that.

**Model:** Claude Opus 5.5.

**Next:** reconcile the star constants.

## Iteration 1, 2026-11-06

**Shipped:** the first mission model. A sail force and temperature model, Alpha Centauri
astrometry, a sundiver trajectory with a numerical check, a mission planner and the `ass` CLI, all
at 100% line and branch coverage.

**Learned:** a sail as heavy as LightSail 2 cannot reach Alpha Centauri at all, even after a dive
to 0.1 AU. At 13 km/s it is slower than the star's 23 km/s sideways drift.

**Model:** Claude Opus 5.5.

**Next:** verify the seed star constants, which were entered from memory of the catalogues.
