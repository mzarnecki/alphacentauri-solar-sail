import numpy as np
import pytest
from astropy.constants import au

from ass.bodies import SUN
from ass.budget import MassBudget, critical_areal_density, sail_area_for
from ass.sail import Sail
from ass.trajectory import cruise_speed

# Karlapp, Heller & Tajmar 2023 (arXiv:2308.16698, abstract): a 1 kg spacecraft carrying 720 g of
# aerographite (0.18 kg/m^3, absorptivity ~1) on 10^4 m^2 of sail.
AEROGRAPHITE = MassBudget(sail_area=1e4, film_areal_density=0.72 / 1e4, payload=0.28)


def test_karlapp_aerographite_craft_comes_out_at_a_tenth_of_a_gram():
    assert AEROGRAPHITE.total == pytest.approx(1.0)
    assert AEROGRAPHITE.areal_density == pytest.approx(1e-4)
    # The same film from bulk density: 0.4 mm of aerographite.
    film = MassBudget.from_film(1e4, 0.18, 0.4e-3, payload=0.28)
    assert film.areal_density == pytest.approx(AEROGRAPHITE.areal_density)
    assert AEROGRAPHITE.shares() == pytest.approx({"film": 0.72, "structure": 0, "payload": 0.28})


def test_karlapp_sundive_to_point_six_au_reaches_their_escape_speed():
    # Their abstract: a dive to 0.6 AU gives 148 km/s. Assumed here (not stated in the abstract):
    # the sail falls edge-on from a circular 1 AU orbit, so it arrives on a 1 x 0.6 AU ellipse,
    # and a black sail has reflectivity 0.
    sail = Sail(AEROGRAPHITE.areal_density, reflectivity=0.0)
    r = 0.6 * au.value
    v_peri = np.sqrt(SUN.gm * (2 / r - 1 / (0.8 * au.value)))
    assert cruise_speed(sail, SUN, r, v_peri) / 1000 == pytest.approx(148, rel=0.02)


@pytest.mark.parametrize("grams, km_s", [(4.9, 105), (2.3, 155)])
def test_turyshev_ideal_sail_at_five_hundredths_of_an_au(grams, km_s):
    # Turyshev 2026 (arXiv:2602.04198, abstract): an ideal sail passing 0.05 AU needs 4.9 g/m^2 for
    # 105 km/s and 2.3 g/m^2 for 155 km/s. We get 105.3 and 153.6, so the second is 0.9% low.
    sail = Sail(grams / 1000, reflectivity=1.0)
    assert cruise_speed(sail, SUN, 0.05 * au.value) / 1000 == pytest.approx(km_s, rel=0.015)


def test_critical_areal_density_is_the_textbook_value_and_means_lightness_one():
    assert critical_areal_density(SUN) * 1000 == pytest.approx(1.53, abs=0.005)
    black = critical_areal_density(SUN, reflectivity=0.0)
    assert black == pytest.approx(critical_areal_density(SUN) / 2)
    assert Sail(black, reflectivity=0.0).lightness(SUN) == pytest.approx(1.0)


def test_sail_area_for_hits_the_target():
    area = sail_area_for(1e-3, 0.5e-3, payload=1.0, structure=1.0)
    assert area == pytest.approx(4000)
    assert MassBudget(area, 0.5e-3, 1.0, 1.0).areal_density == pytest.approx(1e-3)


def test_film_heavier_than_the_target_is_refused():
    with pytest.raises(ValueError, match="no sail is big enough"):
        sail_area_for(1e-3, 1e-3, payload=1.0)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"sail_area": 0}, "sail_area"),
        ({"film_areal_density": 0}, "film_areal_density"),
        ({"payload": -1}, "negative"),
        ({"structure": -1}, "negative"),
    ],
)
def test_nonsense_budgets_are_refused(kwargs, match):
    args = {"sail_area": 1.0, "film_areal_density": 1e-3, "payload": 1.0} | kwargs
    with pytest.raises(ValueError, match=match):
        MassBudget(**args)
