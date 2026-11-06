"""The Sun and the Alpha Centauri system: where they are and how hard they shine."""

from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.constants import G, L_sun, M_sun
from astropy.coordinates import Distance, SkyCoord

SECONDS_PER_YEAR = u.yr.to(u.s)


@dataclass(frozen=True)
class Body:
    name: str
    mass: float
    luminosity: float

    @property
    def gm(self) -> float:
        return G.value * self.mass


@dataclass(frozen=True)
class Star(Body):
    """A star with ICRS astrometry, as seen from the Sun at the catalogue epoch."""

    ra_deg: float
    dec_deg: float
    parallax_mas: float
    pm_ra_cosdec_mas_yr: float
    pm_dec_mas_yr: float
    radial_velocity_km_s: float

    def state(self) -> tuple[np.ndarray, np.ndarray]:
        """Heliocentric Cartesian position (m) and velocity (m/s)."""
        coord = SkyCoord(
            ra=self.ra_deg * u.deg,
            dec=self.dec_deg * u.deg,
            distance=Distance(parallax=self.parallax_mas * u.mas),
            pm_ra_cosdec=self.pm_ra_cosdec_mas_yr * u.mas / u.yr,
            pm_dec=self.pm_dec_mas_yr * u.mas / u.yr,
            radial_velocity=self.radial_velocity_km_s * u.km / u.s,
        )
        return coord.cartesian.xyz.to_value(u.m), coord.velocity.d_xyz.to_value(u.m / u.s)

    def closest_approach(self) -> tuple[float, float]:
        """Years from the epoch until closest approach to the Sun, and the distance then (m).

        shortcut: straight-line motion, upgrade to a Galactic potential for >100 kyr accuracy.
        """
        r, v = self.state()
        t = -np.dot(r, v) / np.dot(v, v)
        return t / SECONDS_PER_YEAR, float(np.linalg.norm(r + v * t))


SUN = Body("Sun", M_sun.value, L_sun.value)

# Seed values (Akeson+ 2021 for A/B, Gaia DR3 for Proxima), not yet re-checked against SIMBAD: see
# docs/ROADMAP.md. shortcut: A/B orbital motion ignored, position is the catalogue epoch's only.
ALPHA_CEN_A = Star(
    "Alpha Centauri A", 1.0788 * M_sun.value, 1.519 * L_sun.value,
    219.9021, -60.8340, 750.81, -3679.25, 473.67, -21.4,
)
ALPHA_CEN_B = Star(
    "Alpha Centauri B", 0.9092 * M_sun.value, 0.500 * L_sun.value,
    219.8961, -60.8375, 750.81, -3614.39, 802.98, -20.6,
)
PROXIMA = Star(
    "Proxima Centauri", 0.1221 * M_sun.value, 0.0017 * L_sun.value,
    217.4289, -62.6795, 768.07, -3781.74, 769.47, -22.4,
)
TARGETS = {"a": ALPHA_CEN_A, "b": ALPHA_CEN_B, "proxima": PROXIMA}
