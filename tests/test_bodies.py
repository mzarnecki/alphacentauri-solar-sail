import astropy.units as u
import numpy as np
import pytest

from ass.bodies import ALPHA_CEN_A, ALPHA_CEN_B, PROXIMA, SUN, TARGETS


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


def test_system_is_approaching_at_catalogue_radial_velocity():
    position, velocity = ALPHA_CEN_A.state()
    radial = np.dot(position, velocity) / np.linalg.norm(position)
    assert radial == pytest.approx(-21_400, rel=1e-6)


def test_a_and_b_are_within_a_binary_separation_on_the_sky():
    separation = np.linalg.norm(ALPHA_CEN_A.state()[0] - ALPHA_CEN_B.state()[0])
    assert separation * u.m.to(u.au) < 40


def test_plan_b_is_waiting_for_alpha_centauri_to_come_to_us():
    years, distance = ALPHA_CEN_A.closest_approach()
    assert 25_000 < years < 30_000
    assert 2.8 < light_years(distance) < 3.5
