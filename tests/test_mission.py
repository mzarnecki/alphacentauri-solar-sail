import numpy as np
import pytest
from astropy.constants import au

from ass.bodies import ALPHA_CEN_A, ALPHA_CEN_B, PROXIMA, SECONDS_PER_YEAR
from ass.mission import Mission, intercept, plan
from ass.sail import Sail


@pytest.mark.parametrize("star", [ALPHA_CEN_A, ALPHA_CEN_B, PROXIMA])
def test_intercept_point_is_where_the_star_will_be_and_reachable_in_time(star):
    speed = 100_000.0
    t, point = intercept(star, speed, 2026)
    np.testing.assert_allclose(point, star.state(2026 + t / SECONDS_PER_YEAR)[0], atol=1e3)
    assert np.linalg.norm(point) == pytest.approx(speed * t, rel=1e-9)


def test_a_and_b_are_different_destinations():
    # Same barycentre, but the arrival points differ by the binary's separation then: 11 to 35 AU.
    _, a = intercept(ALPHA_CEN_A, 100_000.0, 2026)
    _, b = intercept(ALPHA_CEN_B, 100_000.0, 2026)
    assert 11 < np.linalg.norm(a - b) / au.value < 36


def test_approaching_star_shortens_the_trip_versus_a_static_star():
    speed = 100_000.0
    t, _ = intercept(ALPHA_CEN_A, speed, 2026)
    assert t < np.linalg.norm(ALPHA_CEN_A.state(2026)[0]) / speed


def test_a_later_launch_finds_the_star_closer():
    speed = 100_000.0
    assert intercept(PROXIMA, speed, 3000)[0] < intercept(PROXIMA, speed, 2026)[0]


def test_speed_equal_to_the_stars_still_reaches_it():
    # Leading quadratic coefficient vanishes here.
    speed = float(np.linalg.norm(PROXIMA.state()[1]))
    t, point = intercept(PROXIMA, speed, 2026)
    assert np.linalg.norm(point) == pytest.approx(speed * t, rel=1e-6)


def test_star_cannot_be_reached_at_walking_pace():
    with pytest.raises(ValueError, match="never be reached"):
        intercept(ALPHA_CEN_A, 1.4, 2026)


def test_plan_for_a_one_gram_sail():
    mission = plan(Sail(1e-3), ALPHA_CEN_A, 0.1 * au.value, 0.1 * au.value, 2030)
    assert mission.target == "Alpha Centauri A"
    assert mission.lightness == pytest.approx(1.45, abs=0.01)
    assert mission.cruise_speed == pytest.approx(160_700, rel=0.01)
    assert mission.arrival_year == pytest.approx(2030 + mission.flight_years)
    assert mission.flight_years * SECONDS_PER_YEAR == pytest.approx(
        intercept(ALPHA_CEN_A, mission.cruise_speed, 2030)[0]
    )


@pytest.mark.parametrize(
    ("temperature", "cruise", "expected"),
    [(1000.0, 1.0, "MELTS"), (900.0, 2.0, "FLYBY"), (900.0, 1.0, "CAPTURE")],
)
def test_verdicts(temperature, cruise, expected):
    mission = Mission("X", 1.0, cruise, 1.0, temperature, 933.0, 1.0, 1.0)
    assert mission.verdict.startswith(expected)
