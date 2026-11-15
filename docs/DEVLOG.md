# Development log

Newest first. One entry per iteration, written for a future reader who has no memory of this
project, which includes the agent.

## Iteration 5, 2026-11-12

**Shipped:** the best sundiver. `closest_safe_approach()` finds the closest distance at which a sail
stays at 90% of its melting point, and never goes below the photosphere. `ass --perihelion best`
and `--periastron best` use it, and so do two new checkboxes in the demo's sidebar. The Sun, A and
B now have radii. At 1 g/m², the best dive is 0.084 AU and the flight to A drops from 7,183 to
6,630 years.

**Learned:** no optimiser was needed. Arriving on a parabola, the cruise speed is
sqrt(2 beta GM / r) and only grows as r shrinks, so the best dive is wherever the temperature limit
says stop. The point-source heating formula is exact all the way to the photosphere for a face-on
plate, but radiation pressure is not, which matters only for near-perfect mirrors. Those now dive to
the surface of the Sun, so finite-disc pressure is on the roadmap. Also, the default 0.1 AU periastron
at A already runs at 853 K, hotter than the new 840 K working limit, because A is half as bright again
as the Sun. The 90% margin is an engineering placeholder, not physics, until the materials database
lands.

**Blocked:** Proxima has no radius. Two abstracts I opened had no radius in them, and an arXiv ID I
tried from memory (astro-ph/0305410) turned out to be a paper on gamma-ray bursts. That is the reason
to source constants rather than recall them. `--periastron best` at Proxima now refuses and explains
why. Proposal 8 asks for a VizieR tool, which would have settled this with one query.

**Sources:** opened Kervella+ 2017 (arXiv:1610.06185) abstract: angular diameters 8.502 and 5.999 mas,
and radii 1.2234 and 0.8632 R_sun at parallax 747.17 mas. These are rescaled here to Akeson's 750.81,
which gives 1.2175 and 0.8591. Abstracts opened with no radius in them: Kervella+ 2016
(arXiv:1610.06079, a paper on stellar conjunctions), Kervella+ 2017 (arXiv:1611.03495) and Demory+
2009 (arXiv:0906.0602). The Sun's radius, luminosity and temperature are IAU 2015 B3 nominal values,
used through astropy. I did not open the resolution today. arXiv sail search, abstracts only, with
no change to the plan: Project Setu laser-sail multiphysics (arXiv:2609.06156), plus the papers
already logged in iterations 3 and 4. The ADS token is still missing. No prompt injections seen.

**Model:** Claude Opus 5.5.

**Next:** the materials database, which gives each film a melting point, a working temperature and
its optical properties.

## Iteration 4, 2026-11-11

**Shipped:** A and B now orbit their barycentre (`BinaryOrbit`, Akeson+ 2021 Table 8), and every
star's position is carried from its catalogue epoch to any date. `intercept()` takes the launch year
and aims at where the chosen star will be on arrival, orbit included. The demo's Stars tab has a new
chart of the distance between A and B. The flight to A at 1 g/m² went from 7,184 to 7,183 years.
Almost all of that is the epoch fix. The orbit itself moves arrival by about a month and the aiming
point by up to 35 AU.

**Learned:** the elements reproduce Akeson's own measured B-relative-to-A positions to 0.001 arcsec
and 0.01 degrees, and the propagated barycentre lands within 0.07 arcsec of Kervella's independent
1991.25 position. Astrometry alone cannot say which way is towards us. Pourbaix & Boffin 2016 settles
it: omega is B's and the radial velocity formula they quote fixes the sign. Over one orbit, A recedes
from the barycentre at most 6.05 km/s, so SIMBAD's -15.252 km/s for A stays unexplained, and it is now
a test. Proxima's binding speed moved from 268 to 274 m/s once all three stars were taken on the same
date (published: 273 ± 49). Fixed-point aiming converges slowly just above the slowest speed that can
catch the star: 0.2 AU left over a 53,000-year flight, written down in the code.

**Disagreements:** luminosities for A and B differ slightly between Thévenin+ 2002 and Akeson+ 2021.
Left alone today and put on the roadmap. Gaia DR2's -22.586 km/s for B sits between the two possible
signs of the orbit, so it could not decide the convention.

**Sources:** opened Akeson+ 2021 HTML (arXiv:2104.10086), Tables 6, 8, 9 and 12, with the key table
read twice. Kervella+ 2016 HTML (arXiv:1610.06079): no convention stated. Pourbaix & Boffin 2016 HTML
(arXiv:1601.01636): convention. SIMBAD for A and B. All read through WebFetch's summariser, which still
cannot quote formulas reliably (proposal 7). arXiv search, abstracts only, with no change to the plan:
GTOC13 solar sail tour optimisation (arXiv:2607.10150), an LLM agent that derives and solves
low-thrust optimal control problems (arXiv:2607.24051), worth a look when the sundiver gets
optimised. No prompt injections seen.

**Model:** Claude Opus 5.5.

**Next:** solve for the best sundiver, the fastest perihelion that stays below the melting point.

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
