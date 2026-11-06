import numpy as np
import pytest
from astropy.constants import au

from ass.bodies import ALPHA_CEN_A, SECONDS_PER_YEAR
from ass.mission import Mission, intercept, plan
from ass.sail import Sail


def test_intercept_point_is_where_the_star_will_be_and_reachable_in_time():
    speed = 100_000.0
    t, point = intercept(ALPHA_CEN_A, speed)
    r, v = ALPHA_CEN_A.state()
    np.testing.assert_allclose(point, r + v * t)
    assert np.linalg.norm(point) == pytest.approx(speed * t, rel=1e-9)


def test_approaching_star_shortens_the_trip_versus_a_static_star():
    speed = 100_000.0
    t, _ = intercept(ALPHA_CEN_A, speed)
    assert t < np.linalg.norm(ALPHA_CEN_A.state()[0]) / speed


def test_speed_equal_to_the_stars_still_reaches_it():
    # Leading quadratic coefficient vanishes here.
    speed = float(np.linalg.norm(ALPHA_CEN_A.state()[1]))
    t, point = intercept(ALPHA_CEN_A, speed)
    assert np.linalg.norm(point) == pytest.approx(speed * t, rel=1e-6)


def test_star_cannot_be_reached_at_walking_pace():
    with pytest.raises(ValueError, match="never be reached"):
        intercept(ALPHA_CEN_A, 1.4)


def test_plan_for_a_one_gram_sail():
    mission = plan(Sail(1e-3), ALPHA_CEN_A, 0.1 * au.value, 0.1 * au.value, 2030)
    assert mission.target == "Alpha Centauri A"
    assert mission.lightness == pytest.approx(1.45, abs=0.01)
    assert mission.cruise_speed == pytest.approx(160_700, rel=0.01)
    assert mission.arrival_year == pytest.approx(2030 + mission.flight_years)
    assert mission.flight_years * SECONDS_PER_YEAR == pytest.approx(
        intercept(ALPHA_CEN_A, mission.cruise_speed)[0]
    )


@pytest.mark.parametrize(
    ("temperature", "cruise", "expected"),
    [(1000.0, 1.0, "MELTS"), (900.0, 2.0, "FLYBY"), (900.0, 1.0, "CAPTURE")],
)
def test_verdicts(temperature, cruise, expected):
    mission = Mission("X", 1.0, cruise, 1.0, temperature, 933.0, 1.0, 1.0)
    assert mission.verdict.startswith(expected)
