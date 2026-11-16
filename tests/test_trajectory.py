import numpy as np
import pytest
from astropy.constants import au, sigma_sb

from ass.bodies import PROXIMA, SUN
from ass.sail import Sail, disc_work_factor
from ass.trajectory import (
    WORKING_FRACTION,
    closest_safe_approach,
    cruise_speed,
    integrate_dive,
    parabolic_speed,
)


def test_black_plate_reaches_its_textbook_temperature_at_one_au():
    # IAU 2015 Resolution B3: nominal solar irradiance at 1 AU is 1361 W/m^2. A black plate facing
    # the Sun and radiating from both sides settles at (S / 2 sigma)^(1/4), which is 331 K.
    black = Sail(1e-3, reflectivity=0.0, emissivity_total=2.0)
    limit = (1361 / (2 * sigma_sb.value)) ** 0.25
    assert limit == pytest.approx(331, abs=0.5)
    assert closest_safe_approach(black, SUN, limit) == pytest.approx(au.value, rel=1e-3)


def test_best_dive_sits_exactly_at_the_working_temperature():
    sail = Sail(1e-3)
    r = closest_safe_approach(sail, SUN)
    assert sail.temperature(SUN, r) == pytest.approx(WORKING_FRACTION * sail.melting_point)
    assert r > SUN.radius


def test_best_dive_beats_every_safe_dive_in_a_brute_force_scan():
    sail = Sail(1e-3)
    limit = WORKING_FRACTION * sail.melting_point
    safe = [r for r in np.geomspace(0.01, 1, 2000) * au.value if sail.temperature(SUN, r) <= limit]
    fastest_scanned = max(cruise_speed(sail, SUN, r) for r in safe)
    best = cruise_speed(sail, SUN, closest_safe_approach(sail, SUN))
    assert best >= fastest_scanned
    assert best == pytest.approx(fastest_scanned, rel=3e-3)


def test_a_perfect_mirror_stops_at_the_photosphere():
    # IAU 2015 Resolution B3: nominal solar radius is 695,700 km.
    assert closest_safe_approach(Sail(1e-3, reflectivity=1.0), SUN) == pytest.approx(6.957e8)


def test_star_without_a_radius_or_a_silly_limit_is_refused():
    with pytest.raises(ValueError, match="no radius"):
        closest_safe_approach(Sail(1e-3), PROXIMA)
    with pytest.raises(ValueError, match="positive"):
        closest_safe_approach(Sail(1e-3), SUN, 0.0)


def test_parabolic_speed_at_one_au():
    assert parabolic_speed(SUN, au.value) == pytest.approx(42_120, rel=1e-3)


def test_cruise_speed_from_parabolic_arrival_is_sqrt_two_beta_gm_over_r():
    # Exact for a point source, and Proxima is one until it gets a radius.
    sail = Sail(1e-3)
    expected = np.sqrt(2 * sail.lightness(PROXIMA) * PROXIMA.gm / (0.1 * au.value))
    assert cruise_speed(sail, PROXIMA, 0.1 * au.value) == pytest.approx(expected)
    # The Sun's finite disc costs 0.1 AU dives about (R/r)^2 / 24 of that speed.
    point = np.sqrt(2 * sail.lightness(SUN) * SUN.gm / (0.1 * au.value))
    u = SUN.radius / (0.1 * au.value)
    assert cruise_speed(sail, SUN, 0.1 * au.value) == pytest.approx(point * (1 - u**2 / 24))


def test_finite_disc_costs_a_mirror_at_the_photosphere_five_percent_of_its_speed():
    # Opening at the photosphere, light delivers (2/3) (3 pi / 4 - 1) = 0.904 of the point-source
    # energy: the push starts at 2/3 but recovers within a few radii.
    mirror = Sail(1e-3, reflectivity=1.0)
    point = np.sqrt(2 * mirror.lightness(SUN) * SUN.gm / SUN.radius)
    ratio = cruise_speed(mirror, SUN, SUN.radius) / point
    assert ratio == pytest.approx(np.sqrt(2 / 3 * (3 * np.pi / 4 - 1)), rel=1e-9)
    assert ratio == pytest.approx(0.951, abs=5e-4)


def test_finite_disc_never_moves_the_best_dive_outwards():
    # The light's work from r to infinity grows as r shrinks, so closer is still faster.
    mirror = Sail(1e-3, reflectivity=1.0)
    speeds = [cruise_speed(mirror, SUN, r) for r in np.geomspace(1, 50, 200) * SUN.radius]
    assert all(np.diff(speeds) < 0)


def test_closer_dive_goes_faster():
    sail = Sail(1e-3)
    assert cruise_speed(sail, SUN, 0.1 * au.value) > cruise_speed(sail, SUN, 0.5 * au.value)


def test_heavy_slow_sail_stays_bound():
    with pytest.raises(ValueError, match="bound"):
        cruise_speed(Sail(1.0), SUN, au.value, v_peri=30_000.0)


@pytest.mark.parametrize(
    ("density", "reflectivity", "r_peri", "v_peri"),
    [
        (1e-3, 0.9, 0.1 * au.value, None),
        (1e-3, 0.9, 0.1 * au.value, 0.0),
        (0.1, 0.9, 0.1 * au.value, None),
        (1e-3, 1.0, SUN.radius, None),
    ],
    ids=["light-parabolic", "light-from-rest", "heavy-decelerating", "mirror-at-photosphere"],
)
def test_integrator_conserves_the_energy_the_analytic_formula_assumes(
    density, reflectivity, r_peri, v_peri
):
    # The integrator applies the finite-disc push point by point, the formula uses its closed-form
    # integral, so the photosphere case checks one against the other where the disc matters most.
    sail = Sail(density, reflectivity)
    r_end = 50 * au.value
    solution = integrate_dive(sail, SUN, r_peri, r_end, v_peri)
    final = solution.y[:, -1]

    assert np.hypot(*final[:2]) == pytest.approx(r_end, rel=1e-6)
    v_inf = cruise_speed(sail, SUN, r_peri, v_peri)
    light = sail.lightness(SUN) * disc_work_factor(SUN.radius, r_end)
    expected = np.sqrt(v_inf**2 + 2 * (1 - light) * SUN.gm / r_end)
    assert np.hypot(*final[2:]) == pytest.approx(expected, rel=1e-6)
