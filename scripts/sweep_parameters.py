"""Sensitivity of the reported strain to the analysis parameters.

Every threshold in the pipeline is a choice, and a reader is entitled to ask
what the reported numbers would have been under a different one. This script
answers that for the parameters that can move a result, by re-deriving the
per-pressure plateau strain while varying one parameter at a time.

Detection is the expensive step (~20 s per video), so the raw per-frame
detections are cached once per run under results/sweeps/features/ and every
landmark sweep reuses them. The dense-field sweep re-runs the patch tracking,
which takes only seconds per run.

Outputs results/sweeps/*.csv and analysis_notes/parameter_sensitivity.md.

Run: .venv/bin/python scripts/sweep_parameters.py [--only NAME]
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stretcher import load_registry
from stretcher.densefield import reference_image, select_grid, track_field
from stretcher.detect import detect_video, video_fps
from stretcher.resample import to_common_grid
from stretcher.strain import triangle_strain
from stretcher.sync import pressure_phases, xcorr_offset
from stretcher.track import fill_gaps, link, reference_window
from stretcher.results import load_pressure_record

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "sweeps")
FEAT = os.path.join(OUT, "features")
NOTES = os.path.join(ROOT, "analysis_notes")
GRID = np.linspace(-3, 27, 1500)

# reported defaults, for reference lines in the tables
DEFAULTS = dict(coverage=0.9, memory=30, min_angle=15.0, keep_corr=0.7)


def cached_features(run):
    """Per-frame detections for one run, computed once and reused."""
    os.makedirs(FEAT, exist_ok=True)
    path = os.path.join(FEAT, run["name"].replace(" ", "_") + ".csv")
    if not os.path.exists(path):
        detect_video(run).to_csv(path, index=False)
        print(f"    detected {run['name']}", flush=True)
    return pd.read_csv(path)


def plateau_from_traj(filled, fps, run, min_angle, weighted=True):
    """Per-membrane plateau strain from a gap-filled trajectory set."""
    ref = reference_window(filled, fps)
    tri, _ = triangle_strain(filled, ref_frames=ref)
    tri["time"] = tri["frame"] / fps
    press = load_pressure_record(run["name"])
    mean_ts = tri.groupby("time")["mean_principal"].mean()
    offset, _ = xcorr_offset(mean_ts.index.to_numpy(), mean_ts.to_numpy(), press)
    phases = pressure_phases(press)
    t_on, t_off = phases[0]
    tri["t0"] = tri["time"] - offset - t_on
    tri = tri[tri["min_angle"] >= min_angle]
    if tri.empty:
        return np.nan, 0
    if weighted:
        ts = tri.groupby("t0").apply(
            lambda g: np.average(g["mean_principal"], weights=g["area0"]),
            include_groups=False)
    else:
        ts = tri.groupby("t0")["mean_principal"].mean()
    trace = to_common_grid(ts.index.to_numpy(), ts.to_numpy(), GRID)
    w1 = min(25.0, (t_off - t_on) - 1.0)
    m = (GRID >= 5.0) & (GRID <= w1)
    return float(np.nanmean(trace[m])), int(tri["triangle"].nunique())


def sweep_landmarks(runs):
    """Coverage threshold, linking memory, min angle, area weighting."""
    rows = []
    for run in runs:
        feats = cached_features(run)
        fps, n_frames = video_fps(run["video"])

        # --- coverage threshold (memory at its default) ---
        traj = link(feats, memory=DEFAULTS["memory"])
        for cov in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
            try:
                filled, _ = fill_gaps(traj, n_frames, min_coverage=cov)
                pl, ntri = plateau_from_traj(filled, fps, run,
                                             DEFAULTS["min_angle"])
                nmk = filled["particle"].nunique()
            except Exception:
                pl, ntri, nmk = np.nan, 0, 0
            rows.append(dict(run=run["name"], pressure=run["pressure_mbar"],
                             parameter="coverage", value=cov, plateau=pl,
                             n_markers=nmk, n_triangles=ntri))

        # --- linking memory (coverage at its default) ---
        for mem in (5, 15, 30, 60, 120):
            try:
                tr = link(feats, memory=mem)
                filled, _ = fill_gaps(tr, n_frames,
                                      min_coverage=DEFAULTS["coverage"])
                pl, ntri = plateau_from_traj(filled, fps, run,
                                             DEFAULTS["min_angle"])
                nmk = filled["particle"].nunique()
            except Exception:
                pl, ntri, nmk = np.nan, 0, 0
            rows.append(dict(run=run["name"], pressure=run["pressure_mbar"],
                             parameter="memory", value=mem, plateau=pl,
                             n_markers=nmk, n_triangles=ntri))

        # --- min angle and area weighting (both at default linking) ---
        filled, _ = fill_gaps(traj, n_frames,
                              min_coverage=DEFAULTS["coverage"])
        for ang in (0.0, 5.0, 10.0, 15.0, 20.0, 25.0):
            pl, ntri = plateau_from_traj(filled, fps, run, ang)
            rows.append(dict(run=run["name"], pressure=run["pressure_mbar"],
                             parameter="min_angle", value=ang, plateau=pl,
                             n_markers=filled["particle"].nunique(),
                             n_triangles=ntri))
        for wt, lab in ((True, 1.0), (False, 0.0)):
            pl, ntri = plateau_from_traj(filled, fps, run,
                                         DEFAULTS["min_angle"], weighted=wt)
            rows.append(dict(run=run["name"], pressure=run["pressure_mbar"],
                             parameter="area_weighted", value=lab, plateau=pl,
                             n_markers=filled["particle"].nunique(),
                             n_triangles=ntri))
        print(f"  {run['name']}: landmark sweeps done", flush=True)
    return pd.DataFrame(rows)


def sweep_dense(runs, patch=27, spacing=24):
    """Dense-field keep-correlation threshold."""
    from stretcher.results import MIN_ANGLE_DEG
    rows = []
    for run in runs:
        if not run.get("inner_circle_cropped"):
            continue
        ref = reference_image(run["video"], run["crop"], run.get("rotate"),
                              ref_frames=range(60))
        c = run["inner_circle_cropped"]
        pts = select_grid(ref, (c["cx"], c["cy"]), c["r"] * 0.85,
                          spacing=spacing, patch=patch)
        if len(pts) < 6:
            continue
        traj, _ = track_field(run["video"], pts, ref, run["crop"],
                              run.get("rotate"), patch=patch)
        fps, _ = video_fps(run["video"])
        good = traj.groupby("particle")["corr"].median()
        for keep in (0.5, 0.6, 0.7, 0.8, 0.9):
            sel = traj[traj["particle"].isin(good[good >= keep].index)]
            if sel["particle"].nunique() < 6:
                rows.append(dict(run=run["name"],
                                 pressure=run["pressure_mbar"],
                                 parameter="keep_corr", value=keep,
                                 plateau=np.nan, n_markers=0, n_triangles=0))
                continue
            tri, _ = triangle_strain(sel, ref_frames=range(60))
            tri["time"] = tri["frame"] / fps
            tri = tri[tri["min_angle"] >= MIN_ANGLE_DEG]
            press = load_pressure_record(run["name"])
            t_on, t_off = pressure_phases(press)[0]
            mean_ts = tri.groupby("time")["mean_principal"].mean()
            offset, _ = xcorr_offset(mean_ts.index.to_numpy(),
                                     mean_ts.to_numpy(), press)
            tri["t0"] = tri["time"] - offset - t_on
            hold = tri[(tri["t0"] >= 5) & (tri["t0"] <= min(25.0, (t_off - t_on) - 1))]
            per = hold.groupby("triangle").apply(
                lambda g: np.average(g["mean_principal"], weights=g["area0"]),
                include_groups=False)
            rows.append(dict(run=run["name"], pressure=run["pressure_mbar"],
                             parameter="keep_corr", value=keep,
                             plateau=float(per.mean()),
                             n_markers=sel["particle"].nunique(),
                             n_triangles=int(len(per))))
        print(f"  {run['name']}: dense sweep done", flush=True)
    return pd.DataFrame(rows)


def summarize(df):
    """Per-pressure mean plateau and retained elements, per parameter value."""
    out = []
    for (param, val), g in df.groupby(["parameter", "value"]):
        per_run = g.dropna(subset=["plateau"])
        row = dict(parameter=param, value=val, n_runs=len(per_run),
                   markers=per_run["n_markers"].mean(),
                   triangles=per_run["n_triangles"].mean())
        for p in (50, 100, 200):
            sub = per_run[per_run["pressure"] == p]
            row[f"plateau_{p}"] = sub["plateau"].mean() if len(sub) else np.nan
        out.append(row)
    return pd.DataFrame(out).sort_values(["parameter", "value"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    args = ap.parse_args()
    _, runs = load_registry(regime="static")
    if args.only:
        runs = [r for r in runs if r["name"] == args.only]
    os.makedirs(OUT, exist_ok=True)

    print("landmark sweeps")
    lm = sweep_landmarks(runs)
    lm.to_csv(os.path.join(OUT, "landmark_sweeps.csv"), index=False)
    print("dense-field sweep")
    dn = sweep_dense(runs)
    dn.to_csv(os.path.join(OUT, "dense_sweeps.csv"), index=False)

    both = pd.concat([lm, dn], ignore_index=True)
    summ = summarize(both)
    summ.to_csv(os.path.join(OUT, "summary.csv"), index=False)

    lines = ["# Parameter sensitivity\n",
             "Per-pressure mean plateau strain (static runs) as one parameter "
             "is varied and all others are held at their reported values "
             f"({DEFAULTS}). `markers`/`triangles` are means over runs.\n"]
    for param, g in summ.groupby("parameter"):
        lines.append(f"## {param}\n")
        lines.append(g.drop(columns="parameter")
                      .to_markdown(index=False, floatfmt=".4f") + "\n")
    with open(os.path.join(NOTES, "parameter_sensitivity.md"), "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
