"""`ass`: find out how late you will arrive."""

import argparse
from datetime import date

import astropy.units as u
from astropy.constants import c

from ass.bodies import SUN, TARGETS, Body
from ass.mission import plan
from ass.sail import Sail
from ass.trajectory import closest_safe_approach

AU = u.au.to(u.m)


def distance(text: str) -> float | None:
    """An approach distance in AU, or None for "best": as close as the sail survives."""
    return None if text == "best" else float(text)


def approach(sail: Sail, body: Body, au: float | None) -> float:
    return closest_safe_approach(sail, body) if au is None else au * AU


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ass", description="Plan a solar sail to Alpha Centauri.")
    parser.add_argument("--areal-density", type=float, default=1.0, help="g/m^2, payload included")
    parser.add_argument(
        "--perihelion", type=distance, default=0.1,
        help="closest Sun approach in AU, or 'best' for as close as the sail survives",
    )
    parser.add_argument(
        "--periastron", type=distance, default=0.1,
        help="closest star approach in AU, or 'best' for as close as the sail survives",
    )
    parser.add_argument("--reflectivity", type=float, default=0.9)
    parser.add_argument("--target", choices=TARGETS, default="a")
    parser.add_argument("--launch-year", type=float, default=date.today().year)
    args = parser.parse_args(argv)

    if any(d is not None and d <= 0 for d in (args.perihelion, args.periastron)):
        parser.error("--perihelion and --periastron must be positive")
    star = TARGETS[args.target]
    try:
        sail = Sail(args.areal_density / 1000, args.reflectivity)
        r_peri = approach(sail, SUN, args.perihelion)
        r_arrival = approach(sail, star, args.periastron)
        mission = plan(sail, star, r_peri, r_arrival, args.launch_year)
    except ValueError as error:
        parser.error(str(error))

    print(f"Target:        {mission.target}")
    print(f"Dives:         {r_peri / AU:.3f} AU from the Sun, {r_arrival / AU:.3f} AU from the star")
    print(f"Lightness:     {mission.lightness:.3f} (above 1, the Sun pushes harder than it pulls)")
    print(f"Cruise speed:  {mission.cruise_speed / 1000:,.0f} km/s "
          f"({mission.cruise_speed / c.value:.3%} of c)")
    print(f"Capture limit: {mission.capture_speed / 1000:,.0f} km/s")
    print(f"Peak temp:     {mission.peak_temperature:,.0f} K "
          f"(melts at {mission.melting_point:,.0f} K)")
    print(f"Flight time:   {mission.flight_years:,.0f} years")
    print(f"Arrival:       year {mission.arrival_year:,.0f}")
    print(f"Verdict:       {mission.verdict}")
