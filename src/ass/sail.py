"""Face-on solar sail: thrust, lightness number and how close it can get before it cooks."""

from dataclasses import dataclass

import numpy as np
from astropy.constants import c, sigma_sb

from ass.bodies import Body


def disc_factor(radius: float | None, r: float) -> float:
    """Finite-disc radiation pressure on a face-on flat sail, as a fraction of the point-source push.

    A star of uniform brightness seen from distance r fills a cone of half-angle a, sin a = R / r.
    A photon arriving at angle t to the sail normal pushes it by cos t, whether it is absorbed or
    specularly reflected, and the flux it brings is weighted by cos t too. So the push goes as the
    integral of cos^2 t over the disc, 2 pi (1 - cos^3 a) / 3, against pi sin^2 a for a point source
    of equal flux. Derived here: 2/3 at the photosphere and 1 - (R/r)^2 / 4 far away. McInnes,
    Solar Sailing (1999), section 2.3, treats the same model (not opened for this iteration).
    Heating integrates cos t alone, so Sail.temperature stays exact.
    shortcut: no limb darkening, which puts more light near the centre and pushes harder.
    """
    if radius is None:
        return 1.0
    if r < radius:
        raise ValueError("inside the star: the sail has bigger problems than radiation pressure")
    x = (radius / r) ** 2
    return float(2 * (1 - (1 - x) ** 1.5) / (3 * x))


def disc_work_factor(radius: float | None, r: float) -> float:
    """Energy light adds from r to infinity, as a fraction of the point-source beta GM / r.

    The integral of disc_factor(R, s) / s^2 from r to infinity, in closed form with u = R / r
    (integration by parts): (2 / 3u) [3/2 (u sqrt(1 - u^2) + arcsin u) - (1 - (1 - u^2)^1.5) / u].
    """
    if radius is None:
        return 1.0
    disc_factor(radius, r)  # refuses a sail inside the star
    u = radius / r
    inner = 1.5 * (u * np.sqrt(1 - u**2) + np.arcsin(u)) - (1 - (1 - u**2) ** 1.5) / u
    return float(2 * inner / (3 * u))


@dataclass(frozen=True)
class Sail:
    areal_density: float  # kg/m^2 of the whole spacecraft, payload included
    reflectivity: float = 0.9
    emissivity_total: float = 0.69  # front + back; default is aluminium front, chromium back
    melting_point: float = 933.0  # K; default is aluminium

    def __post_init__(self):
        if self.areal_density <= 0:
            raise ValueError("areal_density must be positive")
        if not 0 <= self.reflectivity <= 1:
            raise ValueError("reflectivity must be between 0 and 1")
        if not 0 < self.emissivity_total <= 2:
            raise ValueError("emissivity_total must be in (0, 2]")

    def acceleration(self, body: Body, r: float) -> float:
        """Radiation-pressure acceleration (m/s^2) at distance r from body, finite disc included."""
        return self.lightness(body) * body.gm / r**2 * disc_factor(body.radius, r)

    def lightness(self, body: Body) -> float:
        """Point-source radiation pressure over gravity. Both fall as 1/r^2, so r drops out.

        Close to the star the finite disc pushes less than this: see disc_factor.
        """
        push = (1 + self.reflectivity) * body.luminosity / (4 * np.pi * c.value)
        return push / (self.areal_density * body.gm)

    def temperature(self, body: Body, r: float) -> float:
        """Radiative-equilibrium temperature (K) at distance r from body."""
        absorbed = (1 - self.reflectivity) * body.luminosity / (4 * np.pi * r**2)
        return (absorbed / (self.emissivity_total * sigma_sb.value)) ** 0.25
