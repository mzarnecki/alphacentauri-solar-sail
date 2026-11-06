# Roadmap

The daily agent takes the top unblocked item, or a better one it can justify in the devlog.
Tick items off and keep the list ordered. Add new items freely.

## Next up

- [ ] Reconcile `ass.bodies` with SIMBAD and cite each constant. Positions and proper motions match.
      Parallax for A/B differs (ours 750.81 mas, SIMBAD 742.12), and radial velocities differ by 2 to
      6 km/s (A: ours -21.4, SIMBAD -15.252; B: -20.6, -22.586; Proxima: -22.4, -20.578). The A/B
      values depend on orbital phase, so decide which systemic velocity to use.
- [ ] Add A/B orbital motion, so arrival geometry knows where each star is at the arrival date.
- [ ] Solve for the best sundiver: fastest perihelion that stays below the melting point.
- [ ] Materials database (aluminium, graphene, dielectric stacks, ...) in place of a single melting point.
- [ ] Mass budget: sail, booms, payload, and the areal density they imply.

## Flight dynamics

- [ ] Sail attitude control during the turn from edge-on to face-on.
- [ ] Non-ideal sail force model: wrinkles, billowing, non-specular reflection.
- [ ] Interstellar medium: drag, dust impacts and erosion over thousands of years.
- [ ] Relativistic flight time, needed once anybody gets near 0.1 c.
- [ ] Deceleration by photogravitational assist (Heller & Hippke 2017), including B's gravity.
- [ ] Proxima Centauri flare hazard model.

## Spacecraft software

- [ ] Fault-tolerant state machine for a mission of thousands of years with no help from home.
- [ ] Interstellar communications link budget, with hours-long light delays growing to years.
- [ ] Radiation-tolerant storage: error correction that survives 10,000 years.
- [ ] Autonomous navigation from star positions.
- [ ] Science planning: what to photograph, and what to send home with 1 bit/s.
- [ ] Software update protocol for code from a civilisation that has forgotten who you are.

## Project

- [x] GitHub Actions CI running tests, coverage and ruff.
- [x] Live demo web app (`app/streamlit_app.py`).
- [x] Pull requests with a human review checklist in place of direct pushes to `main`.
- [ ] Add a mission dashboard to the demo: days elapsed, distance covered (0 m).
