"""End-to-end mission estimate: speed, aiming point, arrival date, and a verdict."""

from dataclasses import dataclass

import numpy as np

from ass.bodies import SECONDS_PER_YEAR, SUN, Star
from ass.sail import Sail
from ass.trajectory import cruise_speed


def intercept(star: Star, speed: float, launch_year: float) -> tuple[float, np.ndarray]:
    """Flight time (s) and arrival point (m) of a straight flight from the Sun at constant speed.

    Solves |r + v t + d| = speed * t, because the star moves while we cruise: r and v are its
    system's straight-line motion and d is its orbital offset from the barycentre on arrival.
    shortcut: non-relativistic, fine for solar-sail speeds, needs gamma above about 0.1 c.
    """
    r, v = star.system_state(launch_year)
    offset = np.zeros(3)
    # Fixed-point iteration on d, which is at most 35 AU and moves at most 8.4 km/s (B at
    # periastron). Fast sails converge to metres. Just above the slowest speed that can catch the
    # star, convergence is slow: 0.2 AU is left at 23.5 km/s, which is 15 days of 53,000 years.
    for _ in range(8):
        start = r + offset
        roots = np.roots([np.dot(v, v) - speed**2, 2 * np.dot(start, v), np.dot(start, start)])
        times = roots[np.isreal(roots) & (roots.real > 0)].real
        if times.size == 0:
            raise ValueError(f"{star.name} can never be reached at {speed} m/s")
        t = float(times.min())
        arrival = launch_year + t / SECONDS_PER_YEAR
        offset = star.state(arrival)[0] - star.system_state(arrival)[0]
    return t, r + v * t + offset


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
    flight_time, _ = intercept(star, speed, launch_year)
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
