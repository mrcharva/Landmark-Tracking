"""Loaders for the re-tracked outputs in results/tracking/ — shared by
analysis and figure scripts so both see identical data and filters."""

import os

import numpy as np
import pandas as pd

from stretcher.resample import to_common_grid
from stretcher.sync import pressure_phases

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRK = os.path.join(ROOT, "results", "tracking")

STRAIN = "mean_principal"
MIN_ANGLE_DEG = 15.0  # sliver triangles amplify centroid noise


def _base(name):
    return os.path.join(TRK, name.replace(" ", "_"))


def load_pressure_record(name):
    return pd.read_csv(_base(name) + "_pressure.csv")


def load_triangles(name):
    """(df, phases): triangle strain with time re-zeroed at the first
    vacuum onset; quality-filtered; phases on the same zeroed base."""
    df = pd.read_csv(_base(name) + "_triangles.csv")
    press = load_pressure_record(name)
    phases = pressure_phases(press)
    t0 = phases[0][0]
    df["time"] = df["time"] - t0
    if "min_angle" in df.columns:
        df = df[df["min_angle"] >= MIN_ANGLE_DEG]
    return df, [(a - t0, b - t0) for a, b in phases]


def membrane_trace(df, grid, value_col=STRAIN):
    """Area-weighted membrane mean strain resampled onto grid."""
    if "area0" in df.columns:
        w = df.groupby("time").apply(
            lambda g: np.average(g[value_col], weights=g["area0"]),
            include_groups=False)
    else:
        w = df.groupby("time")[value_col].mean()
    return to_common_grid(w.index.to_numpy(), w.to_numpy(), grid)


def radial_at_max(name):
    """Per-marker radial strain / angle at the maximum-deformation frame."""
    rad = pd.read_csv(_base(name) + "_radial.csv")
    fmax = rad.groupby("frame")["radial_strain"].mean().idxmax()
    return rad[rad["frame"] == fmax]


def plateau_stats(trace, grid, phases):
    """(plateau, drift) over the first vacuum hold, per analyze conventions."""
    t_off = phases[0][1]
    w0, w1 = 5.0, min(25.0, t_off - 1.0)
    m = (grid >= w0) & (grid <= w1)
    plateau = float(np.nanmean(trace[m]))
    drift = (float(np.nanmean(trace[(grid >= w1 - 2) & (grid <= w1)]))
             - float(np.nanmean(trace[(grid >= w0) & (grid <= w0 + 2)])))
    return plateau, drift
