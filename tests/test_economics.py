import math

import numpy as np
import pytest

from bloom.economics import (break_even_probability, choose_action, expected_cost,
                             policy_expense, relative_economic_value, required_efficacy)


@pytest.mark.parametrize("p", [-0.01, 1.01, float("nan")])
def test_invalid_probabilities_rejected(p):
    with pytest.raises(ValueError):
        expected_cost(p, 10, 0.5, 1, True)


def test_p0_p1_costs():
    assert expected_cost(0.0, 10, 0.5, 1, False) == 0
    assert expected_cost(0.0, 10, 0.5, 1, True) == 1          # pay C, no event
    assert expected_cost(1.0, 10, 0.5, 1, False) == 10
    assert expected_cost(1.0, 10, 0.5, 1, True) == 1 + 5


def test_break_even_and_tie_goes_to_no_action():
    ps = break_even_probability(2, 0.5, 10)
    assert ps == pytest.approx(0.4)
    assert not choose_action(0.4, 2, 0.5, 10)      # equality -> no action
    assert choose_action(0.4000001, 2, 0.5, 10)
    # at p*, both actions have identical expected cost
    assert expected_cost(ps, 10, 0.5, 2, True) == pytest.approx(expected_cost(ps, 10, 0.5, 2, False))


def test_zero_effect_or_zero_loss_is_infinite_threshold():
    assert math.isinf(break_even_probability(1, 0.0, 10))
    assert math.isinf(break_even_probability(1, 0.5, 0))
    assert not choose_action(1.0, 1, 0.0, 10)


def test_zero_cost_action_taken_whenever_p_positive():
    assert break_even_probability(0, 0.5, 10) == 0
    assert choose_action(0.01, 0, 0.5, 10) and not choose_action(0.0, 0, 0.5, 10)


def test_p_star_above_one_never_acts():
    # USGS SIR 2024-5091 basic HABITATS DDC=0.25: C=4.56, eL=1.83 ($M 2018)
    ps = break_even_probability(4.56, 1.0, 1.83)
    assert ps > 1 and not choose_action(1.0, 4.56, 1.0, 1.83)


def test_required_efficacy():
    assert required_efficacy(0.5, 1, 10) == pytest.approx(0.2)
    assert math.isinf(required_efficacy(0.0, 1, 10))


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        break_even_probability(-1, 0.5, 10)
    with pytest.raises(ValueError):
        expected_cost(0.5, 10, 1.5, 1, True)


def test_rev_perfect_and_climatology():
    o = np.array([1, 0, 0, 1, 0, 0, 0, 0], bool)
    assert relative_economic_value(o, o, 0.2) == pytest.approx(1.0)
    s = o.mean()
    never = np.zeros_like(o)
    always = np.ones_like(o)
    # best constant action has REV 0
    best_const = always if 0.2 < s else never
    assert relative_economic_value(best_const, o, 0.2) == pytest.approx(0.0)


def test_rev_units_and_sign():
    o = np.array([1, 0, 0, 0], bool)
    a = np.array([0, 1, 1, 1], bool)  # always wrong
    assert policy_expense(a, o, 0.1) == pytest.approx((0.3 + 1) / 4)
    assert relative_economic_value(a, o, 0.1) < 0


def test_rev_undefined_cases():
    o = np.zeros(5, bool)
    assert math.isnan(relative_economic_value(o, o, 0.2))      # no events
    o2 = np.array([1, 0], bool)
    assert math.isnan(relative_economic_value(o2, o2, 1.5))    # alpha >= 1


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        policy_expense([True], [True, False], 0.1)
