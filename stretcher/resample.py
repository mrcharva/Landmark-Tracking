"""Resampling onto a common time grid — the safe version of what the old
plot notebook did with np.interp over concatenated triangles."""

import numpy as np


def to_common_grid(time, values, grid):
    """np.interp with a monotonicity check and NaN outside the record.

    The submission's static figures called np.interp on a non-monotonic time
    axis (all triangles concatenated) and silently plotted one triangle.
    This refuses non-monotonic input outright.
    """
    t = np.asarray(time, float)
    v = np.asarray(values, float)
    if np.any(np.diff(t) < 0):
        raise ValueError(
            "time axis is not monotonic — average replicates (e.g. "
            "groupby('time').mean()) before resampling")
    return np.interp(grid, t, v, left=np.nan, right=np.nan)


def mean_then_resample(df, grid, time_col="time", value_col="strain"):
    """Average replicate rows at each time point, then resample."""
    ts = df.groupby(time_col)[value_col].mean()
    return to_common_grid(ts.index.to_numpy(), ts.to_numpy(), grid)
