from dataclasses import replace

import astropy.units as u
import numpy as np
import pytest
from astropy.constants import M_sun, au

from ass.bodies import ALPHA_CEN_A, ALPHA_CEN_B, PROXIMA, SUN, TARGETS, binding, escape_speed


def light_years(metres):
    return metres * u.m.to(u.lyr)


def test_sun_gm():
    assert SUN.gm == pytest.approx(1.327e20, rel=1e-3)


@pytest.mark.parametrize(
    ("star", "expected_ly"), [(ALPHA_CEN_A, 4.34), (ALPHA_CEN_B, 4.34), (PROXIMA, 4.25)]
)
def test_catalogue_distances(star, expected_ly):
    position, _ = star.state()
    assert light_years(np.linalg.norm(position)) == pytest.approx(expected_ly, abs=0.01)


def test_proxima_is_the_closest_star():
    assert min(TARGETS.values(), key=lambda s: np.linalg.norm(s.state()[0])) is PROXIMA


def test_system_is_approaching_at_the_published_barycentric_velocity():
    # Kervella+ 2017 (arXiv:1611.03495): -22.332 +/- 0.005 km/s.
    position, velocity = ALPHA_CEN_A.state()
    radial = np.dot(position, velocity) / np.linalg.norm(position)
    assert radial == pytest.approx(-22_332, abs=5)


def test_tangential_speed_matches_the_literature():
    # Kervella+ 2016 (arXiv:1610.06079) Sect. 3.2: components -22.9666 and +4.4019 km/s. They use an
    # older proper motion and parallax, so allow for the difference from Akeson+ 2021.
    position, velocity = ALPHA_CEN_A.state()
    radial = np.dot(position, velocity) / np.linalg.norm(position)
    tangential = np.sqrt(np.dot(velocity, velocity) - radial**2)
    assert tangential == pytest.approx(np.hypot(22_966.6, 4_401.9), abs=50)


def test_a_and_b_do_not_drift_apart_over_a_flight():
    # Same barycentric motion. Under 10 m/s remains, because their lines of sight differ slightly.
    assert np.linalg.norm(ALPHA_CEN_A.state()[1] - ALPHA_CEN_B.state()[1]) < 10


def test_escape_speed_reproduces_the_published_value():
    # Kervella+ 2017: 545 +/- 11 m/s at 12,947 au, with their masses 1.1055 + 0.9373 + 0.1221.
    mass = (1.1055 + 0.9373 + 0.1221) * M_sun.value
    assert escape_speed(mass, 12_947 * au.value) == pytest.approx(545, abs=1)


def test_proxima_is_bound_to_alpha_centauri():
    # Kervella+ 2017: bound, with a relative velocity of 273 +/- 49 m/s.
    relative, escape = binding(PROXIMA, (ALPHA_CEN_A, ALPHA_CEN_B))
    assert relative == pytest.approx(273, abs=49)
    assert relative < escape


def test_a_fast_companion_is_not_bound():
    runaway = replace(PROXIMA, radial_velocity_km_s=PROXIMA.radial_velocity_km_s + 5)
    relative, escape = binding(runaway, (ALPHA_CEN_A, ALPHA_CEN_B))
    assert relative > escape


def test_a_and_b_are_within_a_binary_separation_on_the_sky():
    separation = np.linalg.norm(ALPHA_CEN_A.state()[0] - ALPHA_CEN_B.state()[0])
    assert separation * u.m.to(u.au) < 40


def test_plan_b_is_waiting_for_alpha_centauri_to_come_to_us():
    years, distance = ALPHA_CEN_A.closest_approach()
    assert years == pytest.approx(28_000, abs=500)
    assert light_years(distance) == pytest.approx(3.14, abs=0.01)
