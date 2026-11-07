# Development log

Newest first. One entry per iteration, written for a future reader who has no memory of this
project, which includes the agent.

## Iteration 3, 2026-11-07

**Shipped:** every star constant in `ass.bodies` now has a source. A and B share one barycentric
motion, Proxima uses Gaia astrometry, and `binding()` checks whether Proxima is bound to A and B, also
shown in the demo's Stars tab. The flight to A at 1 g/m² moved by 0.5%, from 7,221 to 7,184 years. The
README poster still says year 9,247, because a poster is harder to patch than a table.

**Learned:** the seed constants had Proxima moving at 1,811 m/s relative to A and B, three times the
557 m/s escape speed, with all tests passing. It is now 268 m/s, against a published 273 ± 49. Matching
SIMBAD would have been the wrong goal: its A and B values each include orbital motion on one date, and
extrapolating those for millennia makes the pair drift apart. SIMBAD's -15.252 km/s for A also looks
out of range. Akeson's elements give my own estimate of at most 6.05 km/s of orbital velocity about the
barycentre, and this value is 7.08 away. I could not open its source (2021MNRAS.506..150B), so that is
an open question, not a catalogue error.

**Blocked:** `query_gaia` errored on both attempts, so the Gaia EDR3 values for Proxima are as quoted by
SIMBAD. ADS was not tried, and its abstract page refuses WebFetch. Table values were read through
WebFetch's summariser, twice for the key ones, with no raw text to compare against (proposal 7).

**Sources:** opened Akeson+ 2021 (arXiv:2104.10086), Kervella+ 2016 (arXiv:1610.06079), Kervella+ 2017
(arXiv:1611.03495), Thévenin+ 2002 (astro-ph/0206283), Boyajian+ 2012 (arXiv:1208.2431) and SIMBAD.
Abstracts only, with no change to the plan: a Bragg grating liquid-crystal sail (arXiv:2610.28942),
reflective nanopillar metasurfaces (arXiv:2610.31452), and TOLIMAN, a CubeSat that will hunt for planets
around A and B (arXiv:2603.14683).

**Model:** Claude Opus 5.5.

**Next:** A/B orbital motion, using the Akeson elements.

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
