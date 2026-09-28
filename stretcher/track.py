"""Linking detections into trajectories + explicit gap policy.

Old pipeline: tp.link(search_range=50, memory=1000) — a marker could vanish
for 33 s and be relinked, and gaps were filled by copying the nearest
existing frame (zero-order hold -> flat plateaus and jumps).

Here: short memory (markers are painted on the gel; they never leave),
linear interpolation of interior gaps, and a per-marker QC report.
"""

import numpy as np
import pandas as pd
import trackpy as tp

tp.quiet()


def link(features, search_range=50, memory=30):
    """tp.link with sane defaults (memory = 1 s at 30 fps)."""
    return tp.link(features, search_range=search_range, memory=memory)


def marker_qc(traj, n_frames):
    """Per-marker coverage: fraction of frames with a detection."""
    counts = traj.groupby("particle")["frame"].nunique()
    return (counts / n_frames).rename("coverage").sort_values()


def fill_gaps(traj, n_frames, min_coverage=0.9):
    """Keep markers with >= min_coverage, linearly interpolate their gaps.

    Returns (filled_traj, qc) where filled_traj has one row per kept marker
    per frame 0..n_frames-1 and qc is the coverage series for ALL markers.
    """
    qc = marker_qc(traj, n_frames)
    keep = qc[qc >= min_coverage].index
    grid = np.arange(n_frames)
    out = []
    for pid in keep:
        sub = traj[traj["particle"] == pid].sort_values("frame")
        f = sub["frame"].to_numpy()
        filled = pd.DataFrame({
            "frame": grid,
            "x": np.interp(grid, f, sub["x"]),
            "y": np.interp(grid, f, sub["y"]),
            "particle": pid,
        })
        out.append(filled)
    if not out:
        raise ValueError("no marker meets the coverage threshold")
    return pd.concat(out, ignore_index=True), qc


def reference_window(filled, fps, min_frames=10, margin_frames=15):
    """Pre-onset frame window from mean marker displacement vs frame 0.

    Returns a range of quiet frames suitable as the strain reference
    (average positions over it to cut reference noise by ~sqrt(N))."""
    from stretcher.sync import strain_onset

    piv_x = filled.pivot(index="frame", columns="particle", values="x")
    piv_y = filled.pivot(index="frame", columns="particle", values="y")
    disp = np.hypot(piv_x - piv_x.iloc[0], piv_y - piv_y.iloc[0]).mean(axis=1)
    t = piv_x.index.to_numpy() / fps
    try:
        onset_t = strain_onset(t, disp.to_numpy())
    except ValueError:
        return range(min_frames)  # no clear motion; minimal reference
    return range(max(min_frames, int(onset_t * fps) - margin_frames))
