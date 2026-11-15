import json

import numpy as np
import pandas as pd
import pytest

from bloom.backtest import add_lags
from bloom.labels import dn_to_chla, hist_median, label_observed_window, summarize_histogram
from bloom.normalize import cyan_weekly_to_observations


def hist(values, land=0, nodata=0):
    h = np.zeros(256)
    for v in values:
        h[v] += 1
    h[254], h[255] = land, nodata
    return h


def test_threshold_dn130_is_about_12ugL():
    assert dn_to_chla(130) == pytest.approx(12.07, abs=0.05)


def test_median_matches_numpy_odd_and_even():
    for vals in ([0, 0, 200], [0, 100, 130, 250], [5], [129, 131]):
        assert hist_median(hist(vals)) == pytest.approx(np.median(vals))


def test_median_excludes_land_and_nodata():
    assert hist_median(hist([140, 140, 0], land=1000, nodata=1000)) == 140


def test_threshold_equality_is_bloom():
    assert label_observed_window(130.0, 100, 10) == "bloom"
    assert label_observed_window(129.5, 100, 10) == "non_bloom"


def test_missing_or_sparse_is_unknown_not_negative():
    assert label_observed_window(float("nan"), 0, 1) == "unknown"
    assert label_observed_window(200.0, 5, 10) == "unknown"
    s = summarize_histogram(hist([], nodata=50))
    assert s["n_valid"] == 0 and np.isnan(s["median_dn"])


def test_bad_histograms_rejected():
    with pytest.raises(ValueError):
        summarize_histogram(np.zeros(10))
    h = hist([1]); h[3] = -1
    with pytest.raises(ValueError):
        hist_median(h)


def _write(tmp_path, data, daily=False):
    p = tmp_path / "cyan_weekly_1_2025.json"
    p.write_text(json.dumps({"OBJECTID": "1", "daily": daily, "data": data}))
    return p


def test_normalize_rejects_daily_and_non_sunday(tmp_path):
    with pytest.raises(ValueError):
        cyan_weekly_to_observations([_write(tmp_path, {"2025 5": hist([1]).tolist()}, daily=True)], "1", 1)
    # 2025 day 6 = Jan 6 2025 (Monday)
    with pytest.raises(ValueError):
        cyan_weekly_to_observations([_write(tmp_path, {"2025 6": hist([1]).tolist()})], "1", 1)


def test_normalize_sunday_ok(tmp_path):
    o = cyan_weekly_to_observations([_write(tmp_path, {"2025 5": hist([200, 200, 0]).tolist()})], "1", 1)
    assert o.start.iloc[0] == pd.Timestamp("2025-01-05") and o.label_state.iloc[0] == "bloom"


def test_lags_do_not_bridge_missing_weeks():
    obs = pd.DataFrame(dict(cyan_objectid=1, start=pd.to_datetime(["2025-01-05", "2025-01-19"]),
                            label_state=["bloom", "non_bloom"], median_dn=[200, 0], frac_ge_bloom=[1, 0]))
    r = add_lags(obs)
    # week 2025-01-19's lag1 (2025-01-12) is missing -> unknown, NOT the 2025-01-05 value
    assert r.loc[r.start == "2025-01-19", "lag1_state"].item() == "unknown"
    assert r.loc[r.start == "2025-01-19", "lag2_state"].item() == "bloom"
