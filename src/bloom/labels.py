"""Observed-window labels from CyAN DN histograms.

CyAN digital numbers (DN): 0 = below detection, 1..253 = valid cyanobacteria
index, 254 = land, 255 = no data (CyAN product convention; to be re-verified
against the CyAN product user guide — see research/decisions.md D-007).

EPA label (Schaeffer et al. 2024 code, cyan_processing_conus.R line 170):
    bloom = median(DN over fully-covered resolvable pixels) >= 130   (~12 ug/L chl-a)
We reproduce the >= inequality and the median, but the CyAN web API histogram
is over the API's own pixel set, which may differ from EPA's coverage_fraction==1
and resolvable-lake mask. Treat this as an approximation of the EPA label.
"""
from __future__ import annotations

import numpy as np

BLOOM_DN = 130
VALID = slice(0, 254)  # DN 0..253 inclusive
LAND, NODATA = 254, 255


def dn_to_chla(dn: np.ndarray | float) -> np.ndarray:
    """CyAN DN -> cyanobacteria index -> approx chl-a (ug/L).
    CI = 10**(3/250*DN - 4.2); chl-a ~= 6620*CI - 3.1 (Seegers et al. 2021 / CyAN docs)."""
    dn = np.asarray(dn, dtype=float)
    ci = 10 ** (3.0 / 250.0 * dn - 4.2)
    return 6620.0 * ci - 3.1


def hist_median(counts) -> float:
    """Median of DN values encoded as a histogram over DN 0..253, matching R's
    median() (average of the two middle values for an even count). NaN if empty."""
    c = np.asarray(counts, dtype=float)[VALID]
    if np.any(c < 0) or not np.all(np.isfinite(c)):
        raise ValueError("histogram counts must be finite and non-negative")
    n = c.sum()
    if n == 0:
        return float("nan")
    cum = np.cumsum(c)
    def kth(k):  # 1-based order statistic
        return float(np.searchsorted(cum, k))
    if n % 2 == 1:
        return kth((n + 1) / 2)
    return (kth(n / 2) + kth(n / 2 + 1)) / 2.0


def summarize_histogram(counts) -> dict:
    c = np.asarray(counts, dtype=float)
    if c.shape != (256,):
        raise ValueError(f"expected 256-bin histogram, got {c.shape}")
    valid = c[VALID].sum()
    total_water = valid + c[NODATA]  # land excluded from the denominator
    med = hist_median(c)
    above = c[BLOOM_DN:254].sum()
    detect = c[1:254].sum()
    return dict(
        n_valid=int(valid), n_nodata=int(c[NODATA]), n_land=int(c[LAND]),
        valid_fraction=(valid / total_water) if total_water else np.nan,
        median_dn=med,
        frac_ge_bloom=(above / valid) if valid else np.nan,
        frac_detect=(detect / valid) if valid else np.nan,
    )


def label_observed_window(median_dn: float, n_valid: int, min_valid: int) -> str:
    """'bloom' / 'non_bloom' / 'unknown'. Too few valid pixels -> unknown, never negative."""
    if n_valid is None or n_valid < min_valid or not np.isfinite(median_dn):
        return "unknown"
    return "bloom" if median_dn >= BLOOM_DN else "non_bloom"
