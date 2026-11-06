"""The sundiver manoeuvre: fall towards a star edge-on, turn face-on at closest approach, leave."""

import numpy as np
from scipy.integrate import solve_ivp

from ass.bodies import Body
from ass.sail import Sail


def parabolic_speed(body: Body, r: float) -> float:
    return np.sqrt(2 * body.gm / r)


def cruise_speed(sail: Sail, body: Body, r_peri: float, v_peri: float | None = None) -> float:
    """Speed at infinity after opening the sail at r_peri, from energy conservation.

    v_peri defaults to arrival on a parabolic orbit. By time reversal, the same number is the
    fastest arrival speed the sail can shed at a star and still end up bound to it.
    """
    v = parabolic_speed(body, r_peri) if v_peri is None else v_peri
    v_inf_squared = v**2 - 2 * (1 - sail.lightness(body)) * body.gm / r_peri
    if v_inf_squared <= 0:
        raise ValueError("sail stays bound: too heavy or too slow to escape")
    return float(np.sqrt(v_inf_squared))


def integrate_dive(
    sail: Sail, body: Body, r_peri: float, r_end: float, v_peri: float | None = None
):
    """Integrate the outbound leg from r_peri to r_end. Returns scipy's solution, state [x,y,vx,vy].

    shortcut: other stars' gravity and sail degradation are ignored, add them to the RHS when
    the mission needs a flight-grade propagator.
    """
    v = parabolic_speed(body, r_peri) if v_peri is None else v_peri
    effective_gm = body.gm * (1 - sail.lightness(body))

    def rhs(_t, s):
        return [s[2], s[3], *(-effective_gm * s[:2] / np.hypot(s[0], s[1]) ** 3)]

    def reached_end(_t, s):
        return np.hypot(s[0], s[1]) - r_end

    reached_end.terminal = True
    # Generous bound, the terminal event ends the run: v_inf is reached within a few r_peri.
    t_max = 10 * r_end / cruise_speed(sail, body, r_peri, v)
    return solve_ivp(
        rhs, (0, t_max), [r_peri, 0.0, 0.0, v], events=reached_end, rtol=1e-10, atol=1e-3
    )
