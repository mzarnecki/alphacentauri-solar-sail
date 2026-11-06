# Development log

Newest first. One entry per iteration, written for a future reader who has no memory of this
project, which includes the agent.

## Iteration 1, 2026-11-06

**Shipped:** the first mission model. A sail force and temperature model, Alpha Centauri
astrometry, a sundiver trajectory with a numerical check, a mission planner and the `ass` CLI, all
at 100% line and branch coverage.

**Learned:** a sail as heavy as LightSail 2 cannot reach Alpha Centauri at all, even after a dive
to 0.1 AU. At 13 km/s it is slower than the star's 23 km/s sideways drift.

**Model:** Claude Opus 5.5.

**Next:** verify the seed star constants, which were entered from memory of the catalogues.
