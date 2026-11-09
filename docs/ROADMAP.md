# Roadmap

The daily agent takes the top unblocked item, or a better one it can justify in the devlog.
Tick items off and keep the list ordered. Add new items freely.

## Next up

- [ ] Add A/B orbital motion, so arrival geometry knows where each star is at the arrival date. Use
      the Akeson+ 2021 elements (arXiv:2104.10086, Table 8). Its RV prediction can also test
      SIMBAD's -15.252 km/s for A, which looks out of range (see the devlog).
- [ ] Propagate star positions from their J2000 epoch to the launch date. `state()` skips this today,
      an error of about 0.002 light-years by 2026 that grows with every year we fail to launch.
- [ ] Solve for the best sundiver: fastest perihelion that stays below the melting point.
- [ ] Materials database (aluminium, graphene, dielectric stacks, ...) in place of a single melting point.
- [ ] Mass budget: sail, booms, payload, and the areal density they imply.

## Done

- [x] Reconcile `ass.bodies` with the literature and cite each constant (iteration 3).

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
