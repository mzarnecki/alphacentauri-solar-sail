import re

import pytest

from ass.cli import main


def test_default_plan_reports_a_verdict(capsys):
    main([])
    out = capsys.readouterr().out
    assert "Alpha Centauri A" in out
    assert "Verdict:" in out


def arrival_year(out):
    return int(re.search(r"Arrival: +year ([\d,]+)", out).group(1).replace(",", ""))


def test_target_and_launch_year_flow_into_the_report(capsys):
    main(["--target", "proxima", "--launch-year", "3000"])
    first = capsys.readouterr().out
    main(["--target", "proxima", "--launch-year", "4000"])
    assert "Proxima Centauri" in first
    # Waiting 1,000 years lets Proxima come about 4,600 AU closer, so the flight is shorter.
    assert 800 < arrival_year(capsys.readouterr().out) - arrival_year(first) < 1000


@pytest.mark.parametrize(
    "argv",
    [
        ["--areal-density", "0"],
        ["--perihelion", "0"],
        ["--periastron", "-1"],
        ["--reflectivity", "2"],
    ],
)
def test_bad_input_is_a_usage_error_not_a_traceback(argv, capsys):
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err
