"""Strain <-> pressure alignment driven by the pressure record.

Replaces the manual syncDict (static) and the strain-minimum anchor (cyclic,
which pointed at a smoothing artifact). The pressure CSVs contain a clean
step; the strain record contains the same step. Align the two onsets.
"""

import numpy as np
import pandas as pd


def load_pressure(path):
    """Pressure CSV -> DataFrame with columns time (s, from 0) and mbar.

    Sensor files are index,time,measurePressure (Fluigent export)."""
    df = pd.read_csv(path)
    df = df.rename(columns={"measurePressure": "mbar"})
    if not {"time", "mbar"} <= set(df.columns):
        raise ValueError(f"unexpected pressure CSV columns in {path}")
    df["time"] = df["time"] - df["time"].iloc[0]
    return df[["time", "mbar"]]


def pressure_onset(pressure, depth_fraction=0.5, threshold_mbar=None,
                   min_samples=2):
    """Time of the main vacuum onset.

    The sensors show a small pre-plateau (~-9 mbar) seconds before the full
    step, so a fixed threshold anchors on the wrong step. Default threshold
    = depth_fraction * the record's deepest pressure; pass threshold_mbar to
    override. Sustained = below threshold for min_samples samples; the
    crossing time is linearly interpolated.
    """
    if threshold_mbar is None:
        threshold_mbar = depth_fraction * float(pressure["mbar"].min())
    below = (pressure["mbar"] < threshold_mbar).to_numpy()
    run = 0
    for i, b in enumerate(below):
        run = run + 1 if b else 0
        if run >= min_samples:
            j = i - run + 1  # first below-threshold sample
            if j == 0:
                return float(pressure["time"].iloc[0])
            t0, t1 = pressure["time"].iloc[j - 1], pressure["time"].iloc[j]
            p0, p1 = pressure["mbar"].iloc[j - 1], pressure["mbar"].iloc[j]
            return float(t0 + (threshold_mbar - p0) / (p1 - p0) * (t1 - t0))
    raise ValueError("no vacuum onset found in pressure record")


def strain_onset(time, strain, fraction=0.5):
    """Time when |strain| first crosses `fraction` of its early plateau.

    Plateau estimate = median of |strain| over the top quartile of |strain|.
    Robust to the initial noise; no smoothing required.
    """
    s = np.abs(np.asarray(strain, float))
    plateau = np.median(s[s >= np.quantile(s, 0.75)])
    idx = np.argmax(s >= fraction * plateau)
    if idx == 0 and s[0] < fraction * plateau:
        raise ValueError("strain never crosses the onset threshold")
    return float(np.asarray(time)[idx])


def align(strain_df, pressure, time_col="time", strain_col="strain",
          offset_override_s=None):
    """Shift strain_df's time axis so its onset coincides with the pressure
    onset. Returns (shifted copy, offset_seconds_applied)."""
    if offset_override_s is not None:
        off = offset_override_s
    else:
        mean_ts = strain_df.groupby(time_col)[strain_col].mean()
        t_strain = strain_onset(mean_ts.index.to_numpy(), mean_ts.to_numpy())
        t_press = pressure_onset(pressure)
        off = t_strain - t_press
    out = strain_df.copy()
    out[time_col] = out[time_col] - off
    return out, off


def pressure_phases(pressure, depth_fraction=0.5, min_s=3.0):
    """Vacuum intervals [(t_on, t_off), ...] from a pressure record.

    Threshold = depth_fraction * deepest pressure; crossing times linearly
    interpolated. An interval still open at the end of the record gets
    t_off = last sample time. Intervals shorter than min_s (sensor glitches,
    transient overshoot crossings) are dropped. Drives per-run metric
    windows so analysis never hardcodes hold timings.
    """
    t = pressure["time"].to_numpy(float)
    p = pressure["mbar"].to_numpy(float)
    thr = depth_fraction * p.min()
    below = p < thr
    phases, t_on = [], None
    for i in range(1, len(p)):
        if below[i] and not below[i - 1]:
            t_on = t[i - 1] + (thr - p[i - 1]) / (p[i] - p[i - 1]) * (t[i] - t[i - 1])
        elif not below[i] and below[i - 1] and t_on is not None:
            t_off = t[i - 1] + (thr - p[i - 1]) / (p[i] - p[i - 1]) * (t[i] - t[i - 1])
            phases.append((float(t_on), float(t_off)))
            t_on = None
    if t_on is not None:
        phases.append((float(t_on), float(t[-1])))
    return [(a, b) for a, b in phases if b - a >= min_s]


def xcorr_offset(strain_time, strain, pressure, dt=0.05, max_lag_s=20.0):
    """Time offset between a strain trace and a pressure record by
    normalized cross-correlation (uses the full waveform, not one onset).

    Returns (offset_s, peak_corr): subtract offset_s from strain time to
    land on the pressure record's time base. peak_corr (0..1) doubles as a
    pairing score - useful to test which pressure record belongs to a video.

    max_lag_s defaults to 20 s: video and sensor recordings were started
    within seconds of each other, and the cyclic square wave's 30 s period
    makes larger lags ambiguous (a one-period slip correlates almost as
    well). Verify alignment downstream with phase_agreement().
    """
    strain_time = np.asarray(strain_time, float)
    s_grid = np.arange(strain_time.min(), strain_time.max(), dt)
    p_grid = np.arange(pressure["time"].min(), pressure["time"].max(), dt)
    s = np.interp(s_grid, strain_time, np.asarray(strain, float))
    p = np.interp(p_grid, pressure["time"], -pressure["mbar"])
    max_lag = int(max_lag_s / dt)
    min_overlap = max(int(10.0 / dt), min(len(s), len(p)) // 2)
    cands = []  # (r, overlap, lag)
    for k in range(-max_lag, max_lag + 1):
        # lag k: s[i] pairs with p[i + k]
        i0, i1 = max(0, -k), min(len(s), len(p) - k)
        if i1 - i0 < min_overlap:
            continue
        a, b = s[i0:i1], p[i0 + k:i1 + k]
        sa, sb = a.std(), b.std()
        if sa == 0 or sb == 0:
            continue
        r = float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))
        cands.append((r, i1 - i0, k))
    if not cands:
        raise ValueError("no lag with sufficient overlap")
    # periodic waveforms produce near-equal peaks one period apart; among
    # near-maximal correlations, prefer the lag explaining the most data
    best_r = max(r for r, _, _ in cands)
    best_lag = max((c for c in cands if c[0] >= best_r - 0.02),
                   key=lambda c: c[1])[2]
    # s time + offset = p time  =>  subtract offset from strain time to
    # land on the pressure record's base, matching align()'s convention
    offset = float(strain_time.min() - pressure["time"].min() - best_lag * dt)
    return offset, best_r


def phase_agreement(strain_time, strain, pressure, offset_s):
    """QC for an alignment: fraction of vacuum-hold time where the aligned
    strain is above half its own plateau. ~1.0 = phases agree; ~0.5 or less
    = the alignment slipped (e.g. by one square-wave period)."""
    t = np.asarray(strain_time, float) - offset_s
    s = np.asarray(strain, float)
    plateau = np.median(s[s >= np.quantile(s, 0.75)])
    hits = total = 0
    for t_on, t_off in pressure_phases(pressure):
        m = (t >= t_on + 1.0) & (t <= t_off - 1.0)
        if m.sum() == 0:
            continue
        hits += int((s[m] > 0.5 * plateau).sum())
        total += int(m.sum())
    return float(hits / total) if total else float("nan")
