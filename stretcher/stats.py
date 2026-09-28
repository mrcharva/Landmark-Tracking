"""Aggregation with honest n: triangles -> gel (well) -> condition.

The submission pooled all triangles of all wells into one SD band (pseudo-
replication: adjacent triangles share vertices) and pooled pressures into
"n = 9". Here aggregation is hierarchical and every summary carries its n.
"""

import numpy as np
import pandas as pd


def summarize(df, by, value_col):
    """Group and return n / mean / sd / sem / ci95 per group."""
    g = df.groupby(by)[value_col]
    out = g.agg(n="count", mean="mean", sd=lambda s: s.std(ddof=1))
    out["sem"] = out["sd"] / np.sqrt(out["n"])
    out["ci95"] = 1.96 * out["sem"]
    return out.reset_index()


def per_gel_then_condition(df, value_col, gel_cols=("well",),
                           condition_cols=("pressure_mbar",),
                           within_gel_cols=()):
    """Collapse pseudo-replicates (triangles/markers) to one value per gel
    first, then summarize across gels per condition. n = number of gels."""
    gel_cols, condition_cols = list(gel_cols), list(condition_cols)
    per_gel = (df.groupby(condition_cols + gel_cols + list(within_gel_cols))
                 [value_col].mean().reset_index())
    return summarize(per_gel, condition_cols + list(within_gel_cols), value_col)


def fit_exponential_decay(t, y, tau_bounds=(0.1, 60.0)):
    """Fit y(t) = y_inf + A * exp(-(t - t0)/tau) over a decay window.

    Returns dict(tau, A, y_inf, rmse). t may start anywhere (t0 = t[0]).
    Used for the post-release strain relaxation of the hydrogel.
    """
    from scipy.optimize import curve_fit

    t = np.asarray(t, float)
    y = np.asarray(y, float)
    m = np.isfinite(t) & np.isfinite(y)
    t, y = t[m] - t[m][0], y[m]
    if len(t) < 8:
        raise ValueError("too few samples for a decay fit")

    def model(tt, y_inf, A, tau):
        return y_inf + A * np.exp(-tt / tau)

    A0 = y[0] - y[-1]
    p0 = [y[-1], A0 if A0 != 0 else 1e-3, max(tau_bounds[0], t[-1] / 3)]
    lo = [-1.0, -1.0, tau_bounds[0]]
    hi = [1.0, 1.0, tau_bounds[1]]
    popt, _ = curve_fit(model, t, y, p0=p0, bounds=(lo, hi), maxfev=10000)
    rmse = float(np.sqrt(np.mean((model(t, *popt) - y) ** 2)))
    return {"y_inf": float(popt[0]), "A": float(popt[1]),
            "tau": float(popt[2]), "rmse": rmse}
