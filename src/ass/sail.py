"""Face-on solar sail: thrust, lightness number and how close it can get before it cooks."""

from dataclasses import dataclass

import numpy as np
from astropy.constants import c, sigma_sb

from ass.bodies import Body


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
        """Radiation-pressure acceleration (m/s^2) at distance r from body."""
        flux = body.luminosity / (4 * np.pi * r**2)
        return (1 + self.reflectivity) * flux / (c.value * self.areal_density)

    def lightness(self, body: Body) -> float:
        """Radiation pressure over gravity. Independent of distance: both fall as 1/r^2."""
        return self.acceleration(body, 1.0) / body.gm

    def temperature(self, body: Body, r: float) -> float:
        """Radiative-equilibrium temperature (K) at distance r from body."""
        absorbed = (1 - self.reflectivity) * body.luminosity / (4 * np.pi * r**2)
        return (absorbed / (self.emissivity_total * sigma_sb.value)) ** 0.25
