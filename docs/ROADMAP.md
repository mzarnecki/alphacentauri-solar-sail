# Roadmap

The daily agent takes the top unblocked item, or a better one it can justify in the devlog.
Tick items off and keep the list ordered. Add new items freely.

## Next up

- [ ] Solve for the best sundiver: fastest perihelion that stays below the melting point.
- [ ] Materials database (aluminium, graphene, dielectric stacks, ...) in place of a single melting point.
- [ ] Mass budget: sail, booms, payload, and the areal density they imply.
- [ ] Choose one luminosity source for A and B. Thévenin+ 2002 gives 1.519 and 0.5002, Akeson+ 2021
      Table 8 gives 1.5059 and 0.4981, and the orbit and masses already come from Akeson.
- [ ] Find the source behind SIMBAD's -15.252 km/s for A (2021MNRAS.506..150B). The orbit now shows
      A never recedes from the barycentre faster than 6.05 km/s, and that value needs 7.08.

## Done

- [x] Add A/B orbital motion with the Akeson+ 2021 elements, and aim at each star where it will be
      on arrival (iteration 4).
- [x] Propagate star positions from their catalogue epoch to the launch date (iteration 4).
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
