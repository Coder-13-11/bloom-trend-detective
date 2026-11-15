"""Decision-theoretic economics. Pure functions; no data access.

Notation (master plan §5.2):
  p  probability of the hazard in the decision window
  L  expected damage if the hazard occurs and no action is taken
  e  fraction of L avoided by the action (conditional on the hazard), 0..1
  C  incremental cost of taking the action (paid whether or not the hazard occurs)

Expected cost  no action: p*L          action: C + p*(1-e)*L
Act iff p*e*L > C  <=>  p > p* = C/(e*L).  Ties (p == p*) -> do not act (cheaper to
defer an indifferent action; documented convention, see decisions.md D-012).
"""
from __future__ import annotations

import math

import numpy as np


def _check_p(p):
    a = np.asarray(p, dtype=float)
    if np.any(~np.isfinite(a)) or np.any(a < 0) or np.any(a > 1):
        raise ValueError("probabilities must be finite and in [0, 1]")
    return a


def _check_nonneg(name, x):
    if not math.isfinite(x) or x < 0:
        raise ValueError(f"{name} must be finite and >= 0, got {x}")


def expected_cost(p, L: float, e: float, C: float, act):
    """Expected cost of acting (act=True) or not (act=False)."""
    p = _check_p(p)
    for n, v in (("L", L), ("C", C)):
        _check_nonneg(n, v)
    if not 0 <= e <= 1:
        raise ValueError("efficacy e must be in [0, 1]")
    act = np.asarray(act, dtype=bool)
    return np.where(act, C + p * (1 - e) * L, p * L)


def break_even_probability(C: float, e: float, L: float) -> float:
    """p* = C/(e L). Returns +inf when e*L == 0 (no probability justifies a costly
    action; if C == 0 too, acting is never strictly better). Values > 1 mean the
    action cannot be justified even with certainty."""
    _check_nonneg("C", C); _check_nonneg("L", L)
    if not 0 <= e <= 1:
        raise ValueError("efficacy e must be in [0, 1]")
    eL = e * L
    if eL == 0:
        return math.inf
    return C / eL


def required_efficacy(p: float, C: float, L: float) -> float:
    """Minimum efficacy e* = C/(p L) for the action to break even at probability p."""
    _check_p(p); _check_nonneg("C", C); _check_nonneg("L", L)
    if p * L == 0:
        return math.inf
    return C / (p * L)


def choose_action(p, C: float, e: float, L: float):
    """Expected-cost-minimising binary action for each probability (strict >)."""
    p = _check_p(p)
    return p > break_even_probability(C, e, L)


# ---- Cost-loss verification (Richardson 2000, QJRMS 126:649-667; Murphy 1977) ----

def policy_expense(actions, outcomes, alpha: float) -> float:
    """Mean expense per decision in units of avoidable loss (eL = 1), cost = alpha.
    actions/outcomes boolean arrays over identical evaluation windows."""
    a = np.asarray(actions, dtype=bool); o = np.asarray(outcomes, dtype=bool)
    if a.shape != o.shape or a.size == 0:
        raise ValueError("actions and outcomes must be non-empty and the same shape")
    if not 0 <= alpha:
        raise ValueError("alpha must be >= 0")
    return float(np.mean(alpha * a + (~a & o)))


def relative_economic_value(actions, outcomes, alpha: float, base_rate: float | None = None) -> float:
    """REV = (E_clim - E_policy)/(E_clim - E_perfect).
    E_clim  = min(alpha, s) (best constant action knowing only base rate s),
    E_perfect = s*alpha (act exactly when the event occurs, if alpha < 1).
    REV = 1 perfect, 0 no better than climatology, < 0 worse. NaN if undefined
    (s == 0, or alpha >= 1 so no policy can beat never acting)."""
    o = np.asarray(outcomes, dtype=bool)
    s = float(o.mean()) if base_rate is None else float(base_rate)
    e_pol = policy_expense(actions, o, alpha)
    e_clim = min(alpha, s)
    e_perf = s * min(alpha, 1.0)
    denom = e_clim - e_perf
    if denom <= 0:
        return float("nan")
    return (e_clim - e_pol) / denom
