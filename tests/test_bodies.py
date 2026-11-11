from dataclasses import replace

import astropy.units as u
import numpy as np
import pytest
from astropy.constants import M_sun, au

from ass.bodies import (
    AB_ORBIT,
    ALPHA_CEN_A,
    ALPHA_CEN_B,
    PROXIMA,
    SUN,
    TARGETS,
    BinaryOrbit,
    binding,
    escape_speed,
)


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
    position, velocity = ALPHA_CEN_A.system_state()
    radial = np.dot(position, velocity) / np.linalg.norm(position)
    assert radial == pytest.approx(-22_332, abs=5)


def test_tangential_speed_matches_the_literature():
    # Kervella+ 2016 (arXiv:1610.06079) Sect. 3.2: components -22.9666 and +4.4019 km/s. They use an
    # older proper motion and parallax, so allow for the difference from Akeson+ 2021.
    position, velocity = ALPHA_CEN_A.system_state()
    radial = np.dot(position, velocity) / np.linalg.norm(position)
    tangential = np.sqrt(np.dot(velocity, velocity) - radial**2)
    assert tangential == pytest.approx(np.hypot(22_966.6, 4_401.9), abs=50)


def test_a_and_b_do_not_drift_apart_over_a_flight():
    # Same barycentre, so after many orbits they are still a binary.
    separation = ALPHA_CEN_A.state(12_026.0)[0] - ALPHA_CEN_B.state(12_026.0)[0]
    assert 11 < np.linalg.norm(separation) * u.m.to(u.au) < 36


@pytest.mark.parametrize(
    ("year", "separation_arcsec", "position_angle_deg"),
    # Akeson+ 2021 (arXiv:2104.10086): Table 12 for 2010.00, Table 6 (ALMA) for 2019.6505.
    [(2010.00, 6.751, 245.357), (2019.6505, 5.27869, 343.7729)],
)
def test_orbit_reproduces_measured_positions_of_b_relative_to_a(
    year, separation_arcsec, position_angle_deg
):
    separation, angle = AB_ORBIT.separation_and_position_angle(year)
    assert separation == pytest.approx(separation_arcsec, abs=0.002)
    assert angle == pytest.approx(position_angle_deg, abs=0.02)


def test_stars_on_the_sky_follow_the_orbit():
    year = 2019.6505
    a, _ = ALPHA_CEN_A.state(year)
    b, _ = ALPHA_CEN_B.state(year)
    angle = np.arccos(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b))
    assert np.degrees(angle) * 3600 == pytest.approx(5.27869, abs=0.002)
    north = np.array([0.0, 0.0, 1.0]) - a[2] * a / np.dot(a, a)
    east = np.cross(north, a)  # north x line of sight points east on the sky
    position_angle = np.degrees(np.arctan2(np.dot(b - a, east / np.linalg.norm(east)),
                                           np.dot(b - a, north / np.linalg.norm(north))))
    assert position_angle % 360 == pytest.approx(343.7729, abs=0.05)


def test_orbit_obeys_keplers_third_law_with_the_published_masses():
    # a^3 / P^2 in AU and years is the total mass in solar masses: 1.0788 + 0.9092 (Table 8).
    a_au = AB_ORBIT.semi_major_axis_arcsec / (AB_ORBIT.parallax_mas / 1000)
    assert a_au**3 / AB_ORBIT.period_yr**2 == pytest.approx(1.0788 + 0.9092, rel=2e-3)


def test_closest_and_farthest_separation_are_11_and_35_au():
    distances = [
        np.linalg.norm(AB_ORBIT.sky(year)[0]) * u.m.to(u.au)
        for year in np.linspace(1955.564, 1955.564 + 79.762, 801)
    ]
    assert min(distances) == pytest.approx(23.30 * (1 - 0.51947), abs=0.01)
    assert max(distances) == pytest.approx(23.30 * (1 + 0.51947), abs=0.01)


def test_orbital_speed_follows_the_vis_viva_equation():
    # v^2 = GM (2/r - 1/a), with GM from Kepler's third law in the same units.
    a = AB_ORBIT.semi_major_axis_arcsec / (AB_ORBIT.parallax_mas / 1000) * au.value
    gm = 4 * np.pi**2 * a**3 / (AB_ORBIT.period_yr * u.yr.to(u.s)) ** 2
    for year in (1955.564, 1990.0, 2026.0):
        r, v = AB_ORBIT.sky(year)
        assert np.dot(v, v) == pytest.approx(gm * (2 / np.linalg.norm(r) - 1 / a), rel=1e-9)


def test_velocity_is_the_derivative_of_position():
    step = 1e-4
    r0, v = AB_ORBIT.sky(2026.0)
    r1, _ = AB_ORBIT.sky(2026.0 + step)
    np.testing.assert_allclose((r1 - r0) / (step * u.yr.to(u.s)), v, rtol=1e-3)


def test_simbad_radial_velocity_for_a_is_out_of_reach_of_the_orbit():
    # SIMBAD gives -15.252 km/s for A (2021MNRAS.506..150B), 7.08 km/s above the barycentre's
    # -22.332. Over a full orbit, A never recedes faster than about 6.05 km/s from it.
    speeds = [
        ALPHA_CEN_A.state(year)[1] - ALPHA_CEN_A.system_state(year)[1]
        for year in np.linspace(1955.564, 1955.564 + 79.762, 2001)
    ]
    line_of_sight = ALPHA_CEN_A.system_state()[0] / np.linalg.norm(ALPHA_CEN_A.system_state()[0])
    radial = [np.dot(v, line_of_sight) for v in speeds]
    assert max(radial) == pytest.approx(6_050, abs=20)
    assert -15_252 - -22_332 > max(radial)


def test_barycentre_motion_matches_an_independent_older_position():
    # Kervella+ 2016/2017 barycentre at J1991.25, as quoted in Akeson+ 2021 Table 9: 14:39:40.2068,
    # -60:50:13.673, +/- 25 and 19 mas. Allow 0.1 arcsec, as their proper motions differ by 20
    # mas/yr. We land 32 and 67 mas away in RA and Dec. An epoch off by a year would be 3.7 arcsec.
    from astropy.coordinates import CartesianRepresentation, SkyCoord

    position, _ = ALPHA_CEN_A.system_state(1991.25)
    coord = SkyCoord(CartesianRepresentation(*position * u.m), frame="icrs")
    expected = SkyCoord("14h39m40.2068s", "-60d50m13.673s", frame="icrs")
    assert coord.separation(expected).to_value(u.arcsec) < 0.1


def test_a_circular_face_on_orbit_is_a_circle_on_the_sky():
    orbit = BinaryOrbit(1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 2000.0, 1000.0)
    for year in (2000.0, 2000.25, 2000.6):
        north, east, away = orbit.sky(year)[0] / au.value
        assert np.hypot(north, east) == pytest.approx(1.0)
        assert away == pytest.approx(0.0)


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
    assert 11 < separation * u.m.to(u.au) < 36


def test_plan_b_is_waiting_for_alpha_centauri_to_come_to_us():
    years, distance = ALPHA_CEN_A.closest_approach()
    assert years == pytest.approx(28_000, abs=500)
    assert light_years(distance) == pytest.approx(3.14, abs=0.01)
