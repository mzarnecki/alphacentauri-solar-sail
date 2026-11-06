import asyncio

import httpx
import pytest

from ass import research

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2601.00001v1</id><title>A  &lt;b&gt;sail&lt;/b&gt;</title>
<published>2026-01-01T00:00:00Z</published><author><name>A. Author</name></author>
<summary>Light pushes.</summary><link href="https://example.org/1"/></entry>
<entry><id>http://arxiv.org/abs/2601.00002v1</id><title>Bare post</title>
<published>2026-01-02T00:00:00Z</published><author><name>B. Author</name></author>
<summary>x</summary><link href="https://example.org/2"/></entry>
</feed>"""


@pytest.fixture
def web(monkeypatch):
    """Replace the network with one canned response and record what was asked for."""
    calls = []

    def serve(content=b"", json=None, status=200):
        def fake_get(url, **kwargs):
            calls.append((url, kwargs))
            request = httpx.Request("GET", url)
            if json is not None:
                return httpx.Response(status, json=json, request=request)
            return httpx.Response(status, content=content, request=request)

        monkeypatch.setattr(research.httpx, "get", fake_get)
        return calls

    return serve


def test_search_arxiv_parses_and_strips_html(web):
    calls = web(ATOM)
    results = research.search_arxiv('all:"solar sail"', max_results=500)
    assert results[0]["title"] == "A sail"
    assert results[0]["authors"] == ["A. Author"]
    assert calls[0][1]["params"]["max_results"] == research.MAX_RESULTS
    assert "ass-research" in calls[0][1]["headers"]["User-Agent"]


def test_http_errors_are_raised_not_swallowed(web):
    web(status=503)
    with pytest.raises(httpx.HTTPStatusError):
        research.search_arxiv("x")


def test_search_ads_needs_a_token(monkeypatch):
    monkeypatch.delenv("ADS_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="ADS_API_TOKEN"):
        research.search_ads("sail")


def test_search_ads_sends_the_token(web, monkeypatch):
    monkeypatch.setenv("ADS_API_TOKEN", "tok")
    calls = web(json={"response": {"docs": [{"bibcode": "2017ApJ"}]}})
    assert research.search_ads("sail") == [{"bibcode": "2017ApJ"}]
    assert calls[0][1]["headers"]["Authorization"] == "Bearer tok"


def test_simbad_maps_columns_and_escapes_quotes(web):
    calls = web(json={"metadata": [{"name": "main_id"}, {"name": "plx_value"}],
                      "data": [["* alf Cen A", 750.81]]})
    assert research.query_simbad("it's") == [{"main_id": "* alf Cen A", "plx_value": 750.81}]
    assert "id = 'it''s'" in calls[0][1]["params"]["QUERY"]


def test_gaia_passes_adql_through(web):
    calls = web(json={"metadata": [{"name": "n"}], "data": [[1]]})
    assert research.query_gaia("SELECT 1 AS n") == [{"n": 1}]
    assert calls[0][1]["params"]["QUERY"] == "SELECT 1 AS n"


def test_read_feed_limits_results(web):
    web(ATOM)
    results = research.read_feed("centauri-dreams", limit=1)
    assert [r["link"] for r in results] == ["https://example.org/1"]


def test_read_feed_only_fetches_the_allowlist(web):
    calls = web(ATOM)
    with pytest.raises(ValueError, match="unknown feed"):
        research.read_feed("https://evil.example/")
    assert calls == []


def test_all_tools_are_registered_with_mcp():
    names = {tool.name for tool in asyncio.run(research.mcp.list_tools())}
    assert names == {"search_arxiv", "search_ads", "query_simbad", "query_gaia", "read_feed"}


def test_main_runs_the_server(monkeypatch):
    ran = []
    monkeypatch.setattr(research.mcp, "run", lambda: ran.append(True))
    research.main()
    assert ran == [True]
