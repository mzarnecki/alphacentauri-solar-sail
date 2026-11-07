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


def escape_speed(total_mass: float, separation: float) -> float:
    """Speed (m/s) at which two bodies with this combined mass (kg) separate for good."""
    return float(np.sqrt(2 * G.value * total_mass / separation))


def binding(companion: Star, primaries: tuple[Star, ...]) -> tuple[float, float]:
    """Companion's speed relative to the primaries' barycentre, and the escape speed there (m/s).

    The companion is gravitationally bound if the first is smaller. Same test as Kervella+ 2017
    (arXiv:1611.03495), who include the companion's own mass. shortcut: treats the primaries as a
    point at their barycentre, which is fine at a separation of thousands of AU.
    """
    mass = sum(star.mass for star in primaries)
    position = sum(star.mass * star.state()[0] for star in primaries) / mass
    velocity = sum(star.mass * star.state()[1] for star in primaries) / mass
    r, v = companion.state()
    return (
        float(np.linalg.norm(v - velocity)),
        escape_speed(mass + companion.mass, float(np.linalg.norm(r - position))),
    )


SUN = Body("Sun", M_sun.value, L_sun.value)

# A and B share the motion of their barycentre, because a flight lasts many 80-year orbits and the
# catalogue values for each star include its orbital motion on the observation date, which would
# otherwise be extrapolated for millennia. SIMBAD disagrees on purpose: see docs/DEVLOG.md.
# Akeson+ 2021 (arXiv:2104.10086) Tables 8-9: orbital parallax, barycentre proper motion, masses.
AB_PARALLAX_MAS = 750.81
AB_PM_RA_COSDEC_MAS_YR = -3639.95
AB_PM_DEC_MAS_YR = 700.40
# Kervella+ 2017 (arXiv:1611.03495): barycentre, corrected for gravitational redshift. Akeson's fit
# gives -22.3796 without that correction, which would not be comparable with Proxima below.
AB_RADIAL_VELOCITY_KM_S = -22.332
# shortcut: positions are SIMBAD's for J2000, but state() treats them as the launch-day positions,
# and A/B orbital motion is ignored. Luminosities for A and B: Thevenin+ 2002 (astro-ph/0206283).
ALPHA_CEN_A = Star(
    "Alpha Centauri A", 1.0788 * M_sun.value, 1.519 * L_sun.value,
    219.90206, -60.83399, AB_PARALLAX_MAS, AB_PM_RA_COSDEC_MAS_YR, AB_PM_DEC_MAS_YR,
    AB_RADIAL_VELOCITY_KM_S,
)
ALPHA_CEN_B = Star(
    "Alpha Centauri B", 0.9092 * M_sun.value, 0.5002 * L_sun.value,
    219.89610, -60.83753, AB_PARALLAX_MAS, AB_PM_RA_COSDEC_MAS_YR, AB_PM_DEC_MAS_YR,
    AB_RADIAL_VELOCITY_KM_S,
)
# Position, parallax and proper motion: Gaia EDR3 via SIMBAD. Radial velocity and mass: Kervella+
# 2017 (arXiv:1611.03495). Luminosity: Boyajian+ 2012 (arXiv:1208.2431) Table 6.
PROXIMA = Star(
    "Proxima Centauri", 0.1221 * M_sun.value, 0.00155 * L_sun.value,
    217.42894, -62.67949, 768.0665, -3781.741, 769.465, -22.204,
)
TARGETS = {"a": ALPHA_CEN_A, "b": ALPHA_CEN_B, "proxima": PROXIMA}
