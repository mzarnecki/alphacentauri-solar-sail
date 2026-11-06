import numpy as np
import pytest
from astropy.constants import au

from ass.bodies import SUN
from ass.sail import Sail
from ass.trajectory import cruise_speed, integrate_dive, parabolic_speed


def test_parabolic_speed_at_one_au():
    assert parabolic_speed(SUN, au.value) == pytest.approx(42_120, rel=1e-3)


def test_cruise_speed_from_parabolic_arrival_is_sqrt_two_beta_gm_over_r():
    sail = Sail(1e-3)
    expected = np.sqrt(2 * sail.lightness(SUN) * SUN.gm / (0.1 * au.value))
    assert cruise_speed(sail, SUN, 0.1 * au.value) == pytest.approx(expected)


def test_closer_dive_goes_faster():
    sail = Sail(1e-3)
    assert cruise_speed(sail, SUN, 0.1 * au.value) > cruise_speed(sail, SUN, 0.5 * au.value)


def test_heavy_slow_sail_stays_bound():
    with pytest.raises(ValueError, match="bound"):
        cruise_speed(Sail(1.0), SUN, au.value, v_peri=30_000.0)


@pytest.mark.parametrize(
    ("density", "v_peri"),
    [(1e-3, None), (1e-3, 0.0), (0.1, None)],
    ids=["light-parabolic", "light-from-rest", "heavy-decelerating"],
)
def test_integrator_conserves_the_energy_the_analytic_formula_assumes(density, v_peri):
    sail = Sail(density)
    r_peri, r_end = 0.1 * au.value, 50 * au.value
    solution = integrate_dive(sail, SUN, r_peri, r_end, v_peri)
    final = solution.y[:, -1]

    assert np.hypot(*final[:2]) == pytest.approx(r_end, rel=1e-6)
    v_inf = cruise_speed(sail, SUN, r_peri, v_peri)
    expected = np.sqrt(v_inf**2 + 2 * (1 - sail.lightness(SUN)) * SUN.gm / r_end)
    assert np.hypot(*final[2:]) == pytest.approx(expected, rel=1e-6)
