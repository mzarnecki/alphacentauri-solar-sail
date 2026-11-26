"""Mass budget: what the spacecraft is made of, and the areal density that the sail model needs.

Every other module takes "grams per square metre, payload included" on trust. This one adds it up.
"""

from dataclasses import dataclass

import numpy as np
from astropy.constants import c

from ass.bodies import Body


def critical_areal_density(body: Body, reflectivity: float = 1.0) -> float:
    """Areal density (kg/m^2) at which a face-on sail has lightness 1 at body.

    (1 + R) L / (4 pi c GM), from setting Sail.lightness to 1. For a perfect mirror at the Sun this
    is the textbook 1.53 g/m^2 (McInnes, Solar Sailing, 1999, section 2.3; not opened here).
    """
    return (1 + reflectivity) * body.luminosity / (4 * np.pi * c.value * body.gm)


@dataclass(frozen=True)
class MassBudget:
    """A spacecraft as sail film plus fixed masses.

    shortcut: structure is a fixed mass. Real booms grow with the sail's size (roughly with its
    side, sqrt(area)), so a bigger sail costs more than film alone.
    """

    sail_area: float  # m^2
    film_areal_density: float  # kg/m^2 of sail film, coatings included
    payload: float  # kg: instruments, radio, power, computer
    structure: float = 0.0  # kg: booms, deployment, attitude control

    def __post_init__(self):
        if self.sail_area <= 0:
            raise ValueError("sail_area must be positive")
        if self.film_areal_density <= 0:
            raise ValueError("film_areal_density must be positive")
        if self.payload < 0 or self.structure < 0:
            raise ValueError("payload and structure cannot be negative")

    @classmethod
    def from_film(
        cls, sail_area: float, density: float, thickness: float, payload: float, structure=0.0
    ) -> "MassBudget":
        """Film areal density from bulk density (kg/m^3) times thickness (m)."""
        return cls(sail_area, density * thickness, payload, structure)

    @property
    def film(self) -> float:
        return self.sail_area * self.film_areal_density

    @property
    def total(self) -> float:
        return self.film + self.payload + self.structure

    @property
    def areal_density(self) -> float:
        """Whole-spacecraft kg/m^2, the number Sail(areal_density) expects."""
        return self.total / self.sail_area

    def shares(self) -> dict[str, float]:
        """Fraction of the total mass in film, structure and payload."""
        return {
            "film": self.film / self.total,
            "structure": self.structure / self.total,
            "payload": self.payload / self.total,
        }


def sail_area_for(
    target_areal_density: float, film_areal_density: float, payload: float, structure=0.0
) -> float:
    """Sail area (m^2) at which the whole spacecraft comes out at target_areal_density.

    Solves (A sigma_film + m) / A = target for A: A = m / (target - sigma_film). A bigger sail
    dilutes the fixed masses but never the film itself, so the film must be lighter than the target.
    """
    margin = target_areal_density - film_areal_density
    if margin <= 0:
        raise ValueError(
            "the film alone is heavier than the target: no sail is big enough, try a thinner film"
        )
    return (payload + structure) / margin
