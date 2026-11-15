import numpy as np
import pandas as pd

from bloom.fieldtruth import _fit, field_weeks
from bloom.insitu import dist_to_ring_m, field_lake_years, points_in_ring

SQ = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], float)


def test_point_in_ring():
    assert points_in_ring([0.5, 1.5, 0.5, 0.01], [0.5, 0.5, -0.1, 0.99], SQ).tolist() == [True, False, False, True]


def test_distance_to_ring_metres():
    d = dist_to_ring_m([0.5], [-0.001], SQ)[0]  # 0.001 deg of latitude south of the edge
    assert 105 < d < 116


def test_field_lake_years_uses_date_means_and_median():
    res = pd.DataFrame(dict(station=["a", "b", "a", "a"], chl=[10.0, 30.0, 100.0, 1.0],
                            date=pd.to_datetime(["2024-06-01", "2024-06-01", "2024-07-01", "2024-08-01"])))
    match = pd.DataFrame(dict(station=["a", "b"], cyan_objectid=[1, 1]))
    g = field_lake_years(res, match).iloc[0]
    # date means: 20, 100, 1 -> median 20 ; two of three dates >= 12
    assert g.n_dates == 3 and bool(g.year_ok)
    assert np.isclose(10 ** g.med_log_chl, 20.0)
    assert np.isclose(g.share_ge12, 2 / 3)


def test_field_weeks_start_on_sunday():
    res = pd.DataFrame(dict(station=["a"], chl=[5.0], date=pd.to_datetime(["2025-06-04"])))  # Wednesday
    w = field_weeks(res, pd.DataFrame(dict(station=["a"], cyan_objectid=[1])))
    assert w.start.iloc[0] == pd.Timestamp("2025-06-01") and w.start.dt.day_of_week.iloc[0] == 6


def test_drift_model_recovers_year_slope_with_lake_effects():
    rng = np.random.default_rng(0)
    rows = []
    for lake in range(30):
        base = rng.normal(0, 20)
        for yr in range(6):
            for _ in range(8):
                x = rng.normal(1, 0.3)
                rows.append(dict(cyan_objectid=lake, log_chl=x, year_c=yr, y=base + 15 * x + 2.0 * yr + rng.normal(0, 1)))
    b = _fit(pd.DataFrame(rows), "y", ["log_chl", "year_c"])
    assert abs(b[0] - 15) < 0.5 and abs(b[1] - 2.0) < 0.1
