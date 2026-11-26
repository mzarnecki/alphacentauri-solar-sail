from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from ass import research

APP = Path(__file__).parent.parent / "app/streamlit_app.py"
ATOM = (
    b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><id>x</id>'
    b"<title>A sail</title><published>2026-01-01T00:00:00Z</published>"
    b"<author><name>A</name></author><summary>s</summary>"
    b'<link href="https://example.org/1"/></entry></feed>'
)


@pytest.fixture
def app():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    return at


def test_default_view_reports_the_mission(app):
    assert [tab.label for tab in app.tabs] == [
        "Mission", "Sail", "Mass budget", "Trajectory", "Stars", "Research feed",
    ]
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Cruise speed"] == "161 km/s"
    assert metrics["Lightness at the Sun"] == "1.455"
    # 1 - (R/r)^2 / 4 at 0.1 AU, with R the Sun's radius.
    assert metrics["Push lost to the Sun's size at closest approach"] == "0.054%"
    assert app.info[0].value.startswith("CAPTURE")
    assert metrics["Proxima's speed relative to A and B"] == "274 m/s"
    assert metrics["Speed it would need to leave"] == "556 m/s"


def test_mass_budget_adds_up_and_sizes_the_sail(app):
    metrics = {metric.label: metric.value for metric in app.metric}
    # 10^4 m^2 of 0.5 g/m^2 film is 5 kg, plus 1 kg payload and 1 kg structure.
    assert metrics["Whole spacecraft"] == "0.700 g/m²"
    assert metrics["Total mass"] == "7.00 kg"
    assert metrics["Lightness 1 for a perfect mirror"] == "1.53 g/m²"
    # 2 kg of fixed mass over the 0.5 g/m^2 left for it at the sidebar's 1 g/m^2.
    assert "this film needs 4,000 m² of sail" in app.info[1].value


def test_a_film_heavier_than_the_whole_target_gets_a_warning(app):
    app.number_input(key="film").set_value(2.0).run()
    assert not app.exception
    assert "no sail is big enough" in app.warning[0].value


def test_a_heavy_sail_gets_an_explanation_not_a_crash(app):
    app.number_input(key="density").set_value(156.0).run()
    assert not app.exception
    assert "Mission impossible" in app.error[0].value


def test_changing_the_star_changes_the_report(app):
    app.selectbox(key="target").select("proxima").run()
    assert not app.exception
    assert "Plan B: wait for Proxima Centauri" in [s.value for s in app.subheader][-2]


def test_best_dives_go_as_close_as_the_sail_survives(app):
    app.checkbox(key="best_perihelion").check().run()
    app.checkbox(key="best_peri").check().run()
    assert not app.exception
    captions = [caption.value for caption in app.sidebar.caption]
    assert "Best dive: 0.0837 AU from the Sun." in captions
    assert "Best dive: 0.1031 AU from the star." in captions
    assert {m.label: m.value for m in app.metric}["Cruise speed"] == "176 km/s"


def test_best_dive_at_proxima_explains_itself(app):
    app.selectbox(key="target").select("proxima").run()
    app.checkbox(key="best_peri").check().run()
    assert not app.exception
    assert "no radius on file" in app.sidebar.warning[0].value


def test_stars_tab_shows_the_binary_orbit(app):
    assert "A and B, waltzing" in [s.value for s in app.subheader]


@pytest.mark.parametrize(
    ("source", "response"),
    [
        ("arXiv", {"content": ATOM}),
        ("centauri-dreams", {"content": ATOM}),
        ("arxiv-astro-ph-ep", {"content": ATOM}),
        ("SIMBAD", {"json": {"metadata": [{"name": "main_id"}], "data": [["alf Cen A"]]}}),
    ],
)
def test_research_sources_render(app, monkeypatch, source, response):
    monkeypatch.setattr(
        research.httpx, "get",
        lambda url, **_: httpx.Response(200, request=httpx.Request("GET", url), **response),
    )
    app.selectbox(key="source").select(source).run()
    app.button(key="fetch").click().run()
    assert not app.exception
    assert not app.error
    assert len(app.dataframe) >= 1


def test_a_failing_source_shows_an_error(app, monkeypatch):
    monkeypatch.setattr(
        research.httpx, "get",
        lambda url, **_: httpx.Response(503, request=httpx.Request("GET", url)),
    )
    app.button(key="fetch").click().run()
    assert not app.exception
    assert "did not answer" in app.error[0].value
