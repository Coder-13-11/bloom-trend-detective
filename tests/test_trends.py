import itertools
import math

import numpy as np
import pytest

from bloom.trends import bh_adjust, mk_s, mk_test, sens_slope, verdict


def test_mk_s_monotonic():
    assert mk_s([1, 2, 3, 4, 5]) == 10
    assert mk_s([5, 4, 3, 2, 1]) == -10
    assert mk_s([1, 1, 1]) == 0


def test_exact_p_perfect_monotonic_n7():
    r = mk_test(np.arange(7.0))
    assert r["method"] == "exact_permutation"
    assert r["p"] == pytest.approx(2 / math.factorial(7))  # only identity and reversal reach |S| = 21


def test_all_tied_is_p1():
    r = mk_test([0, 0, 0, 0, 0, 0, 0])
    assert r["p"] == 1.0


def test_exact_matches_brute_force_with_ties():
    x = [0.1, 0.0, 0.0, 0.3, 0.2, 0.0, 0.4]
    s = mk_s(x)
    perms = list(itertools.permutations(x))
    brute = np.mean([abs(mk_s(p)) >= abs(s) for p in perms])
    assert mk_test(x)["p"] == pytest.approx(brute)


def test_normal_approx_large_n_known_value():
    # n = 10 strictly increasing: S = 45, var = 10*9*25/18 = 125, z = 44/sqrt(125)
    r = mk_test(np.arange(10.0))
    assert r["method"] == "normal_tie_corrected"
    from scipy.stats import norm
    assert r["p"] == pytest.approx(2 * norm.sf(44 / math.sqrt(125)))


def test_sens_slope_linear_and_ci_brackets():
    t = np.arange(1981, 2026)
    x = 0.02 * (t - 1981) + np.sin(t)  # noisy upward trend
    s = sens_slope(t, x)
    assert s["slope_lo"] <= s["slope"] <= s["slope_hi"]
    assert sens_slope(np.arange(5), 3 * np.arange(5.0))["slope"] == pytest.approx(3.0)


def test_bh_matches_hand_example():
    p = [0.01, 0.04, 0.03, 0.5]
    # sorted 0.01,0.03,0.04,0.5 -> 0.04,0.06,0.0533,0.5 -> monotone 0.04,0.0533,0.0533,0.5
    assert np.allclose(bh_adjust(p), [0.04, 0.05333333, 0.05333333, 0.5])


def test_verdict_wording():
    assert verdict(0.001, 0.01, 0.1, 7).startswith("Significant upward")
    assert verdict(0.001, 0.01, -0.1, 7).startswith("Significant downward")
    assert verdict(0.03, 0.4, 0.1, 7).startswith("Possible trend")
    assert verdict(0.3, 0.9, 0.1, 7) == "No clear trend yet (n = 7 seasons)"
