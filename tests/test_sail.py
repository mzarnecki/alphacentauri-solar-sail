import pytest
from astropy.constants import au

from ass.bodies import SUN
from ass.sail import Sail


def test_critical_density_of_a_perfect_mirror_is_the_textbook_value():
    # McInnes, Solar Sailing: lightness 1 at 1.53 g/m^2.
    assert Sail(1.53e-3, reflectivity=1.0).lightness(SUN) == pytest.approx(1.0, abs=0.002)


def test_lightsail_2_acceleration_matches_flight_scale():
    # 5 kg on 32 m^2 flew at about 0.058 mm/s^2 at best.
    assert Sail(5 / 32).acceleration(SUN, au.value) == pytest.approx(5.8e-5, rel=0.1)


def test_lightness_does_not_depend_on_distance():
    sail = Sail(1e-3)
    ratio = sail.acceleration(SUN, au.value) / (SUN.gm / au.value**2)
    assert ratio == pytest.approx(sail.lightness(SUN))


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
