"""`ass`: find out how late you will arrive."""

import argparse
from datetime import date

import astropy.units as u
from astropy.constants import c

from ass.bodies import TARGETS
from ass.mission import plan
from ass.sail import Sail


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ass", description="Plan a solar sail to Alpha Centauri.")
    parser.add_argument("--areal-density", type=float, default=1.0, help="g/m^2, payload included")
    parser.add_argument("--perihelion", type=float, default=0.1, help="closest Sun approach, AU")
    parser.add_argument("--periastron", type=float, default=0.1, help="closest star approach, AU")
    parser.add_argument("--reflectivity", type=float, default=0.9)
    parser.add_argument("--target", choices=TARGETS, default="a")
    parser.add_argument("--launch-year", type=float, default=date.today().year)
    args = parser.parse_args(argv)

    if args.perihelion <= 0 or args.periastron <= 0:
        parser.error("--perihelion and --periastron must be positive")
    try:
        sail = Sail(args.areal_density / 1000, args.reflectivity)
        mission = plan(
            sail,
            TARGETS[args.target],
            args.perihelion * u.au.to(u.m),
            args.periastron * u.au.to(u.m),
            args.launch_year,
        )
    except ValueError as error:
        parser.error(str(error))

    print(f"Target:        {mission.target}")
    print(f"Lightness:     {mission.lightness:.3f} (above 1, the Sun pushes harder than it pulls)")
    print(f"Cruise speed:  {mission.cruise_speed / 1000:,.0f} km/s "
          f"({mission.cruise_speed / c.value:.3%} of c)")
    print(f"Capture limit: {mission.capture_speed / 1000:,.0f} km/s")
    print(f"Peak temp:     {mission.peak_temperature:,.0f} K "
          f"(melts at {mission.melting_point:,.0f} K)")
    print(f"Flight time:   {mission.flight_years:,.0f} years")
    print(f"Arrival:       year {mission.arrival_year:,.0f}")
    print(f"Verdict:       {mission.verdict}")
