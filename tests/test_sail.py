import numpy as np
import pytest
from astropy.constants import au
from scipy.integrate import quad

from ass.bodies import PROXIMA, SUN
from ass.sail import Sail, disc_factor, disc_work_factor


def test_critical_density_of_a_perfect_mirror_is_the_textbook_value():
    # McInnes, Solar Sailing: lightness 1 at 1.53 g/m^2.
    assert Sail(1.53e-3, reflectivity=1.0).lightness(SUN) == pytest.approx(1.0, abs=0.002)


def test_lightsail_2_acceleration_matches_flight_scale():
    # 5 kg on 32 m^2 flew at about 0.058 mm/s^2 at best.
    assert Sail(5 / 32).acceleration(SUN, au.value) == pytest.approx(5.8e-5, rel=0.1)


def test_lightness_does_not_depend_on_distance():
    # Up to the finite disc, which costs 5 parts per million at 1 AU.
    sail = Sail(1e-3)
    ratio = sail.acceleration(SUN, au.value) / (SUN.gm / au.value**2)
    assert ratio == pytest.approx(sail.lightness(SUN), rel=1e-5)


def test_temperature_falls_with_inverse_square_root_of_distance():
    sail = Sail(1e-3)
    assert sail.temperature(SUN, au.value) == pytest.approx(
        sail.temperature(SUN, 4 * au.value) * 2
    )


def test_perfect_mirror_stays_at_absolute_zero():
    assert Sail(1e-3, reflectivity=1.0).temperature(SUN, au.value) == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"areal_density": 0},
        {"areal_density": 1, "reflectivity": 1.1},
        {"areal_density": 1, "reflectivity": -0.1},
        {"areal_density": 1, "emissivity_total": 0},
        {"areal_density": 1, "emissivity_total": 2.1},
    ],
)
def test_impossible_sails_are_rejected(kwargs):
    with pytest.raises(ValueError):
        Sail(**kwargs)


def test_finite_disc_pushes_two_thirds_at_the_photosphere():
    # A uniform disc filling half the sky: the integral of cos^2 t over the hemisphere is 2 pi / 3,
    # against pi for a point source of the same flux.
    assert disc_factor(1.0, 1.0) == pytest.approx(2 / 3)


def test_finite_disc_fades_to_a_point_source_far_away():
    # Series expansion: 1 - (R/r)^2 / 4. At 1 AU the Sun's disc costs 5 parts per million.
    for ratio in (0.01, 0.05):
        assert disc_factor(1.0, 1 / ratio) == pytest.approx(1 - ratio**2 / 4, rel=1e-5)
    assert 1 - disc_factor(SUN.radius, au.value) == pytest.approx(5.4e-6, rel=0.01)


@pytest.mark.parametrize("r_over_radius", [1.0, 1.5, 4.0])
def test_finite_disc_matches_a_brute_force_sum_over_the_disc(r_over_radius):
    # Independent of the closed form: integrate cos^2 t over the cone numerically.
    edge = np.arcsin(1 / r_over_radius)
    push, _ = quad(lambda t: 2 * np.pi * np.cos(t) ** 2 * np.sin(t), 0, edge)
    point = np.pi * np.sin(edge) ** 2
    assert disc_factor(1.0, r_over_radius) == pytest.approx(push / point, rel=1e-9)


@pytest.mark.parametrize("r_over_radius", [1.0, 1.2, 3.0, 30.0])
def test_disc_work_factor_is_the_integral_of_the_push(r_over_radius):
    work, _ = quad(lambda s: disc_factor(1.0, s) / s**2, r_over_radius, np.inf)
    assert disc_work_factor(1.0, r_over_radius) == pytest.approx(work * r_over_radius, rel=1e-8)


def test_stars_without_a_radius_are_points_and_sails_inside_stars_are_refused():
    assert disc_factor(None, 1.0) == disc_work_factor(None, 1.0) == 1.0
    sail = Sail(1e-3)
    assert sail.acceleration(PROXIMA, au.value) == pytest.approx(
        sail.lightness(PROXIMA) * PROXIMA.gm / au.value**2
    )
    for factor in (disc_factor, disc_work_factor):
        with pytest.raises(ValueError, match="inside the star"):
            factor(SUN.radius, 0.5 * SUN.radius)
