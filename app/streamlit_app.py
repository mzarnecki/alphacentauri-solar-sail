"""Live demo of every ASS module. Run with: uv run streamlit run app/streamlit_app.py"""

from datetime import date

import altair as alt
import astropy.units as u
import httpx
import numpy as np
import pandas as pd
import streamlit as st
from astropy.constants import c

from ass.bodies import (
    AB_ORBIT,
    ALPHA_CEN_A,
    ALPHA_CEN_B,
    PROXIMA,
    SECONDS_PER_YEAR,
    SUN,
    TARGETS,
    binding,
)
from ass.mission import intercept, plan
from ass.research import FEEDS, query_simbad, read_feed, search_arxiv
from ass.sail import Sail
from ass.trajectory import cruise_speed, integrate_dive

AU = u.au.to(u.m)
LY = u.lyr.to(u.m)
DARK = st.context.theme.type == "dark"
SERIES = "#3987e5" if DARK else "#2a78d6"
MUTED = "#898781"


def line_chart(data: pd.DataFrame, x: str, y: str, log_x=False, log_y=False, rule=None, mark=None):
    """A one-series line with a hover crosshair; rule is (y value, label), mark is an x value."""
    x_scale = alt.Scale(type="log" if log_x else "linear", nice=False)
    y_scale = alt.Scale(type="log" if log_y else "linear", zero=False)
    x_enc = alt.X(f"{x}:Q", title=x, scale=x_scale, axis=alt.Axis(grid=False))
    y_enc = alt.Y(f"{y}:Q", title=y, scale=y_scale, axis=alt.Axis(grid=not log_y))
    nearest = alt.selection_point(
        fields=[x], nearest=True, on="pointerover", empty=False, clear="pointerout"
    )
    base = alt.Chart(data).encode(x=x_enc, y=y_enc)
    layers = [
        base.mark_line(color=SERIES, strokeWidth=2),
        base.mark_point(opacity=0, size=400).encode(tooltip=[x, y]).add_params(nearest),
        base.mark_point(color=SERIES, size=64, filled=True, opacity=1).transform_filter(nearest),
    ]
    if rule:
        rule_data = pd.DataFrame({"y": [rule[0]], "label": [rule[1]]})
        rule_base = alt.Chart(rule_data).encode(y="y:Q")
        layers.append(rule_base.mark_rule(color=MUTED, strokeDash=[4, 4]))
        layers.append(
            rule_base.mark_text(align="left", dy=-8, x=8, color=MUTED).encode(text="label:N")
        )
    if mark is not None:
        layers.append(
            alt.Chart(pd.DataFrame({"x": [mark]})).mark_rule(color=MUTED).encode(x="x:Q")
        )
    st.altair_chart(alt.layer(*layers), use_container_width=True)
    with st.expander("Show the numbers"):
        st.dataframe(data, hide_index=True)


st.set_page_config(page_title="ASS mission control", page_icon="🛰️", layout="wide")
st.title("ASS mission control")
st.caption(
    "Alpha centauri Solar Sail. Every number here is computed live by the project's Python "
    "modules. The spacecraft is still imaginary."
)

with st.sidebar:
    st.header("Your spacecraft")
    density = st.number_input(
        "Weight (g/m², payload included)", 0.001, 1000.0, 1.0, format="%.3f", key="density",
        help="LightSail 2 is about 156. Below about 1.5, the Sun repels the sail.",
    )
    reflectivity = st.slider("Reflectivity", 0.5, 1.0, 0.9, 0.01, key="reflectivity")
    perihelion = st.number_input(
        "Closest approach to the Sun (AU)", 0.01, 5.0, 0.1, 0.01, key="perihelion"
    )
    st.header("Your destination")
    target = TARGETS[
        st.selectbox(
            "Star", list(TARGETS), format_func=lambda key: TARGETS[key].name, key="target"
        )
    ]
    periastron = st.number_input(
        "Closest approach to the star (AU)", 0.01, 5.0, 0.1, 0.01, key="periastron"
    )
    launch_year = st.number_input("Launch year", 2026, 100_000, date.today().year, key="launch")

sail = Sail(density / 1000, reflectivity)
mission_tab, sail_tab, trajectory_tab, stars_tab, research_tab = st.tabs(
    ["Mission", "Sail", "Trajectory", "Stars", "Research feed"]
)

with mission_tab:
    st.subheader("How late will you arrive?")
    try:
        mission = plan(sail, target, perihelion * AU, periastron * AU, launch_year)
    except ValueError as error:
        st.error(f"Mission impossible: {error}. Make the sail lighter or dive closer to the Sun.")
    else:
        columns = st.columns(4)
        columns[0].metric("Cruise speed", f"{mission.cruise_speed / 1000:,.0f} km/s")
        columns[1].metric("Share of light speed", f"{mission.cruise_speed / c.value:.3%}")
        columns[2].metric("Flight time", f"{mission.flight_years:,.0f} years")
        columns[3].metric("Arrival", f"year {mission.arrival_year:,.0f}")
        st.info(mission.verdict)

    st.subheader("Flight time by spacecraft weight")
    rows = []
    for grams in np.geomspace(0.01, 1000, 50):
        speed = cruise_speed(Sail(grams / 1000, reflectivity), SUN, perihelion * AU)
        try:
            years = intercept(target, speed, launch_year)[0] / SECONDS_PER_YEAR
        except ValueError:  # too slow to ever catch the star: leave a gap in the line
            continue
        rows.append({"Weight (g/m²)": round(grams, 3), "Flight time (years)": round(years)})
    line_chart(
        pd.DataFrame(rows), "Weight (g/m²)", "Flight time (years)",
        log_x=True, log_y=True, mark=density,
    )
    st.caption(
        "The vertical line is your spacecraft. The curve ends where the sail gets too slow to "
        "catch the star at all."
    )

with sail_tab:
    st.subheader("What the sail feels")
    columns = st.columns(3)
    columns[0].metric("Lightness at the Sun", f"{sail.lightness(SUN):.3f}")
    columns[1].metric(
        "Push at Earth's distance", f"{sail.acceleration(SUN, AU) * 1000:.3f} mm/s²"
    )
    columns[2].metric(
        "Temperature at closest approach", f"{sail.temperature(SUN, perihelion * AU):,.0f} K"
    )
    st.subheader("Temperature by distance from the Sun")
    distances = np.geomspace(0.01, 5, 60)
    line_chart(
        pd.DataFrame(
            {
                "Distance (AU)": distances.round(4),
                "Temperature (K)": [round(sail.temperature(SUN, d * AU)) for d in distances],
            }
        ),
        "Distance (AU)", "Temperature (K)", log_x=True,
        rule=(sail.melting_point, f"Aluminium melts at {sail.melting_point:,.0f} K"),
        mark=perihelion,
    )

with trajectory_tab:
    st.subheader("The sundiver, integrated numerically")
    solution = integrate_dive(sail, SUN, perihelion * AU, 100 * AU)
    limit = cruise_speed(sail, SUN, perihelion * AU) / 1000
    line_chart(
        pd.DataFrame(
            {
                "Distance (AU)": (np.hypot(*solution.y[:2]) / AU).round(4),
                "Speed (km/s)": (np.hypot(*solution.y[2:]) / 1000).round(2),
            }
        ),
        "Distance (AU)", "Speed (km/s)", log_x=True,
        rule=(limit, f"Formula says {limit:,.0f} km/s at infinity"),
    )
    st.caption(
        f"The sail takes {solution.t[-1] / SECONDS_PER_YEAR:.2f} years to reach 100 AU, and the "
        "integrated curve should settle towards the formula's dashed line."
    )

with stars_tab:
    st.subheader("Where we are going")
    rows = []
    for star in TARGETS.values():
        position, velocity = star.state(launch_year)
        years, closest = star.closest_approach()
        rows.append(
            {
                "Star": star.name,
                "Distance (ly)": round(float(np.linalg.norm(position)) / LY, 3),
                "Speed through space (km/s)": round(float(np.linalg.norm(velocity)) / 1000, 1),
                "Your sail's lightness there": round(sail.lightness(star), 3),
                "Closest approach (years away)": round(years - (launch_year - star.epoch)),
                "Closest approach (ly)": round(closest / LY, 2),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.caption(
        "Positions and speeds on your launch date. A and B orbit their shared barycentre, so "
        "their radial velocities differ from SIMBAD's on purpose. These are first-order "
        "estimates, so please do not cite them."
    )
    st.subheader("A and B, waltzing")
    orbit_years = np.arange(launch_year - 80, launch_year + 81)
    line_chart(
        pd.DataFrame(
            {
                "Year": orbit_years,
                "Distance between A and B (AU)": [
                    round(float(np.linalg.norm(AB_ORBIT.sky(y)[0])) / AU, 2) for y in orbit_years
                ],
            }
        ),
        "Year", "Distance between A and B (AU)", mark=launch_year,
    )
    st.caption(
        "Orbit from Akeson et al. 2021. The vertical line is your launch. You will arrive dozens "
        "of orbits later, so the planner aims at where your star will be then, not now."
    )
    st.subheader("Is Proxima staying?")
    relative, escape = binding(PROXIMA, (ALPHA_CEN_A, ALPHA_CEN_B), launch_year)
    columns = st.columns(2)
    columns[0].metric("Proxima's speed relative to A and B", f"{relative:,.0f} m/s")
    columns[1].metric("Speed it would need to leave", f"{escape:,.0f} m/s")
    st.subheader(f"Plan B: wait for {target.name} to come to us")
    position, velocity = target.system_state(launch_year)
    years = np.linspace(0, 60_000, 121)
    line_chart(
        pd.DataFrame(
            {
                "Years from now": years,
                "Distance (ly)": [
                    round(float(np.linalg.norm(position + velocity * y * SECONDS_PER_YEAR)) / LY, 3)
                    for y in years
                ],
            }
        ),
        "Years from now", "Distance (ly)",
        mark=target.closest_approach()[0] - (launch_year - target.epoch),
    )

with research_tab:
    st.subheader("What the daily agent reads")
    st.caption("Live queries to public services. They can be slow, and forum posts are unreviewed.")
    source = st.selectbox("Source", ["arXiv", "SIMBAD", *FEEDS], key="source")
    query = ""
    if source == "arXiv":
        query = st.text_input("Search", 'all:"solar sail"', key="arxiv_query")
    elif source == "SIMBAD":
        query = st.text_input("Object", "Proxima Centauri", key="simbad_query")
    if st.button("Fetch", key="fetch"):
        try:
            with st.spinner("Asking the internet..."):
                if source == "arXiv":
                    results = search_arxiv(query, 10)
                elif source == "SIMBAD":
                    results = query_simbad(query)
                else:
                    results = read_feed(source, 10)
        except (httpx.HTTPError, ValueError, KeyError) as error:  # third parties fail, demo stays up
            st.error(f"{source} did not answer: {error}")
        else:
            st.dataframe(pd.DataFrame(results), hide_index=True)
