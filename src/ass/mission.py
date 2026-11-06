"""End-to-end mission estimate: speed, aiming point, arrival date, and a verdict."""

from dataclasses import dataclass

import numpy as np

from ass.bodies import SECONDS_PER_YEAR, SUN, Star
from ass.sail import Sail
from ass.trajectory import cruise_speed


def intercept(star: Star, speed: float) -> tuple[float, np.ndarray]:
    """Flight time (s) and arrival point (m) of a straight flight from the Sun at constant speed.

    Solves |r + v t| = speed * t, because the star moves while we cruise.
    shortcut: non-relativistic, fine for solar-sail speeds, needs gamma above about 0.1 c.
    """
    r, v = star.state()
    roots = np.roots([np.dot(v, v) - speed**2, 2 * np.dot(r, v), np.dot(r, r)])
    times = roots[np.isreal(roots) & (roots.real > 0)].real
    if times.size == 0:
        raise ValueError(f"{star.name} can never be reached at {speed} m/s")
    t = float(times.min())
    return t, r + v * t


@dataclass(frozen=True)
class Mission:
    target: str
    lightness: float
    cruise_speed: float
    capture_speed: float
    peak_temperature: float
    melting_point: float
    flight_years: float
    arrival_year: float

    @property
    def verdict(self) -> str:
        if self.peak_temperature >= self.melting_point:
            return "MELTS: congratulations, you have invented a very expensive comet"
        if self.cruise_speed > self.capture_speed:
            return "FLYBY: one blurry photo, then the void, forever"
        return "CAPTURE: the sail can brake on starlight and stay"


def plan(sail: Sail, star: Star, r_peri: float, r_arrival: float, launch_year: float) -> Mission:
    """Dive past the Sun at r_peri, cruise to star, try to brake at r_arrival from it."""
    speed = cruise_speed(sail, SUN, r_peri)
    flight_time, _ = intercept(star, speed)
    return Mission(
        target=star.name,
        lightness=sail.lightness(SUN),
        cruise_speed=speed,
        capture_speed=cruise_speed(sail, star, r_arrival),
        peak_temperature=max(sail.temperature(SUN, r_peri), sail.temperature(star, r_arrival)),
        melting_point=sail.melting_point,
        flight_years=flight_time / SECONDS_PER_YEAR,
        arrival_year=launch_year + flight_time / SECONDS_PER_YEAR,
    )
