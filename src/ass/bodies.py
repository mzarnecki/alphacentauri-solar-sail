"""The Sun and the Alpha Centauri system: where they are and how hard they shine."""

from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.constants import G, L_sun, M_sun, au
from astropy.coordinates import Distance, SkyCoord
from scipy.optimize import newton

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
class BinaryOrbit:
    """Keplerian orbit of a binary's secondary relative to its primary, as seen from the Sun.

    Angles follow the visual-binary convention used by Pourbaix & Boffin 2016 (arXiv:1601.01636):
    omega is the secondary's, and positive z points away from us, so dz/dt is its radial velocity
    relative to the primary. Thiele-Innes rotation as in Heintz, Double Stars (1978).
    """

    period_yr: float
    semi_major_axis_arcsec: float
    eccentricity: float
    inclination_deg: float
    periastron_arg_deg: float
    node_deg: float
    periastron_year: float
    parallax_mas: float

    def _plane(self, year: float) -> tuple[np.ndarray, np.ndarray]:
        """Position (m) and velocity (m/s) in the orbital plane, x towards periastron."""
        e = self.eccentricity
        mean_anomaly = 2 * np.pi * (year - self.periastron_year) / self.period_yr
        anomaly = newton(
            lambda big_e: big_e - e * np.sin(big_e) - mean_anomaly, mean_anomaly,
            fprime=lambda big_e: 1 - e * np.cos(big_e),
        )
        a = self.semi_major_axis_arcsec / (self.parallax_mas / 1000) * au.value
        speed = 2 * np.pi * a / (self.period_yr * SECONDS_PER_YEAR) / np.sqrt(1 - e**2)
        root = np.sqrt(1 - e**2)
        position = a * np.array([np.cos(anomaly) - e, root * np.sin(anomaly)])
        true_anomaly = np.arctan2(position[1], position[0])
        velocity = speed * np.array([-np.sin(true_anomaly), e + np.cos(true_anomaly)])
        return position, velocity

    def _rotation(self) -> np.ndarray:
        """Columns map orbital-plane x and y to sky (north, east, away from us)."""
        i, w, node = np.radians([self.inclination_deg, self.periastron_arg_deg, self.node_deg])
        return np.array([
            [np.cos(node) * np.cos(w) - np.sin(node) * np.sin(w) * np.cos(i),
             -np.cos(node) * np.sin(w) - np.sin(node) * np.cos(w) * np.cos(i)],
            [np.sin(node) * np.cos(w) + np.cos(node) * np.sin(w) * np.cos(i),
             -np.sin(node) * np.sin(w) + np.cos(node) * np.cos(w) * np.cos(i)],
            [np.sin(w) * np.sin(i), np.cos(w) * np.sin(i)],
        ])

    def sky(self, year: float) -> tuple[np.ndarray, np.ndarray]:
        """Secondary relative to primary in (north, east, away) metres and metres per second."""
        position, velocity = self._plane(year)
        return self._rotation() @ position, self._rotation() @ velocity

    def separation_and_position_angle(self, year: float) -> tuple[float, float]:
        """Apparent separation (arcsec) and position angle (degrees east of north)."""
        north, east, _ = self.sky(year)[0] / au.value * (self.parallax_mas / 1000)
        return float(np.hypot(north, east)), float(np.degrees(np.arctan2(east, north)) % 360)


def sky_basis(ra_deg: float, dec_deg: float) -> np.ndarray:
    """Columns are the ICRS unit vectors pointing north, east and away from us at (ra, dec)."""
    ra, dec = np.radians([ra_deg, dec_deg])
    return np.array([
        [-np.sin(dec) * np.cos(ra), -np.sin(ra), np.cos(dec) * np.cos(ra)],
        [-np.sin(dec) * np.sin(ra), np.cos(ra), np.cos(dec) * np.sin(ra)],
        [np.cos(dec), 0.0, np.sin(dec)],
    ])


@dataclass(frozen=True)
class Star(Body):
    """A star with ICRS astrometry, as seen from the Sun at the catalogue epoch, a Julian year.

    For a binary member, the astrometry is the barycentre's and orbit_share is the fraction of
    the secondary-minus-primary vector that this star sits from it: -m_B/M for A, +m_A/M for B.
    """

    ra_deg: float
    dec_deg: float
    parallax_mas: float
    pm_ra_cosdec_mas_yr: float
    pm_dec_mas_yr: float
    radial_velocity_km_s: float
    epoch: float = 2000.0
    orbit: BinaryOrbit | None = None
    orbit_share: float = 0.0

    def system_state(self, year: float | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Heliocentric position (m) and velocity (m/s) of the star, or its binary's barycentre.

        shortcut: straight-line motion from the epoch, ignoring light-time and the Galaxy, which is
        fine for the thousands of years a flight takes.
        """
        coord = SkyCoord(
            ra=self.ra_deg * u.deg,
            dec=self.dec_deg * u.deg,
            distance=Distance(parallax=self.parallax_mas * u.mas),
            pm_ra_cosdec=self.pm_ra_cosdec_mas_yr * u.mas / u.yr,
            pm_dec=self.pm_dec_mas_yr * u.mas / u.yr,
            radial_velocity=self.radial_velocity_km_s * u.km / u.s,
        )
        position = coord.cartesian.xyz.to_value(u.m)
        velocity = coord.velocity.d_xyz.to_value(u.m / u.s)
        elapsed = (self.epoch if year is None else year) - self.epoch
        return position + velocity * elapsed * SECONDS_PER_YEAR, velocity

    def state(self, year: float | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Heliocentric position (m) and velocity (m/s) of the star itself, orbit included."""
        position, velocity = self.system_state(year)
        if self.orbit is None:
            return position, velocity
        basis = sky_basis(self.ra_deg, self.dec_deg)
        offset, motion = self.orbit.sky(self.epoch if year is None else year)
        return position + self.orbit_share * basis @ offset, velocity + self.orbit_share * basis @ motion

    def closest_approach(self) -> tuple[float, float]:
        """Years from the epoch until closest approach to the Sun, and the distance then (m).

        shortcut: straight-line motion, upgrade to a Galactic potential for >100 kyr accuracy.
        """
        r, v = self.system_state()
        t = -np.dot(r, v) / np.dot(v, v)
        return t / SECONDS_PER_YEAR, float(np.linalg.norm(r + v * t))


def escape_speed(total_mass: float, separation: float) -> float:
    """Speed (m/s) at which two bodies with this combined mass (kg) separate for good."""
    return float(np.sqrt(2 * G.value * total_mass / separation))


def binding(
    companion: Star, primaries: tuple[Star, ...], year: float = 2020.0
) -> tuple[float, float]:
    """Companion's speed relative to the primaries' barycentre, and the escape speed there (m/s).

    The companion is gravitationally bound if the first is smaller. Same test as Kervella+ 2017
    (arXiv:1611.03495), who include the companion's own mass. shortcut: treats the primaries as a
    point at their barycentre, which is fine at a separation of thousands of AU. All positions are
    taken on the same date, because the stars move 4.8 AU a year relative to the Sun.
    """
    mass = sum(star.mass for star in primaries)
    position = sum(star.mass * star.state(year)[0] for star in primaries) / mass
    velocity = sum(star.mass * star.state(year)[1] for star in primaries) / mass
    r, v = companion.state(year)
    return (
        float(np.linalg.norm(v - velocity)),
        escape_speed(mass + companion.mass, float(np.linalg.norm(r - position))),
    )


SUN = Body("Sun", M_sun.value, L_sun.value)

# Akeson+ 2021 (arXiv:2104.10086). Table 9: barycentre position at J2019.5 and proper motion.
# Table 8: orbital parallax, orbit of B relative to A, masses. A and B sit on either side of the
# barycentre, so a flight lasting many 80-year orbits never extrapolates one star's orbital motion.
AB_EPOCH = 2019.5
AB_RA_DEG = 219.85892215
AB_DEC_DEG = -60.83163195
AB_PARALLAX_MAS = 750.81
AB_PM_RA_COSDEC_MAS_YR = -3639.95
AB_PM_DEC_MAS_YR = 700.40
# Kervella+ 2017 (arXiv:1611.03495): barycentre, corrected for gravitational redshift. Akeson's fit
# gives -22.3796 without that correction, which would not be comparable with Proxima below.
AB_RADIAL_VELOCITY_KM_S = -22.332
AB_ORBIT = BinaryOrbit(79.762, 17.4930, 0.51947, 79.2430, 231.519, 205.073, 1955.564, 750.81)
A_MASS_FRACTION = 0.54266
# Luminosities for A and B: Thevenin+ 2002 (astro-ph/0206283).
ALPHA_CEN_A = Star(
    "Alpha Centauri A", 1.0788 * M_sun.value, 1.519 * L_sun.value,
    AB_RA_DEG, AB_DEC_DEG, AB_PARALLAX_MAS, AB_PM_RA_COSDEC_MAS_YR, AB_PM_DEC_MAS_YR,
    AB_RADIAL_VELOCITY_KM_S, AB_EPOCH, AB_ORBIT, -(1 - A_MASS_FRACTION),
)
ALPHA_CEN_B = Star(
    "Alpha Centauri B", 0.9092 * M_sun.value, 0.5002 * L_sun.value,
    AB_RA_DEG, AB_DEC_DEG, AB_PARALLAX_MAS, AB_PM_RA_COSDEC_MAS_YR, AB_PM_DEC_MAS_YR,
    AB_RADIAL_VELOCITY_KM_S, AB_EPOCH, AB_ORBIT, A_MASS_FRACTION,
)
# Position, parallax and proper motion: Gaia EDR3 via SIMBAD, which gives the position at J2000. Radial velocity and mass: Kervella+
# 2017 (arXiv:1611.03495). Luminosity: Boyajian+ 2012 (arXiv:1208.2431) Table 6.
PROXIMA = Star(
    "Proxima Centauri", 0.1221 * M_sun.value, 0.00155 * L_sun.value,
    217.42894, -62.67949, 768.0665, -3781.741, 769.465, -22.204,
)
TARGETS = {"a": ALPHA_CEN_A, "b": ALPHA_CEN_B, "proxima": PROXIMA}
