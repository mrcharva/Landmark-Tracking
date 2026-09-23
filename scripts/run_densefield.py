"""Dense-field (DIC-style) strain for every non-excluded run.

Generalizes the former dic_pilot.py: registry-driven, with a membrane-circle
fallback chain (curated circle -> Hough on the reference image -> bounding
circle of the run's tracked landmarks + 15% margin). Per run writes
*_densefield_triangles.csv + *_densefield_mesh.npz and appends to
results/tracking/densefield_qc.json.

Run: .venv/bin/python scripts/run_densefield.py [--only NAME]
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stretcher import load_registry
from stretcher.densefield import (MIN_POINTS, reference_image, select_textured_grid,
                                  track_field)
from stretcher.detect import video_fps
from stretcher.ring import find_inner_circle
from stretcher.results import MIN_ANGLE_DEG
from stretcher.strain import reference_positions, triangle_strain

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRK = os.path.join(ROOT, "results", "tracking")
QC_PATH = os.path.join(TRK, "densefield_qc.json")

PATCH = 27
REF_FRAMES = range(60)  # first 2 s; recordings start before vacuum onset


def membrane_circle(run, ref_img):
    """(cx, cy, r, method) for the membrane region in cropped coordinates."""
    c = run.get("inner_circle_cropped")
    if c:
        return c["cx"], c["cy"], c["r"], "curated"
    found = find_inner_circle(ref_img.astype(np.uint8))
    if found is not None:
        return found[0], found[1], found[2], "hough"
    markers = pd.read_csv(
        os.path.join(TRK, run["name"].replace(" ", "_") + "_markers.csv"))
    m0 = markers[markers["frame"] == 0]
    cx, cy = m0["x"].mean(), m0["y"].mean()
    r = float(np.hypot(m0["x"] - cx, m0["y"] - cy).max()) * 1.15
    return float(cx), float(cy), r, "landmark-bound"


def process(run):
    t0 = time.time()
    name = run["name"]
    fps, _ = video_fps(run["video"])
    ref = reference_image(run["video"], run["crop"], run.get("rotate"),
                          ref_frames=REF_FRAMES)
    cx, cy, r, method = membrane_circle(run, ref)
    pts, threshold = select_textured_grid(ref, (cx, cy), r * 0.85,
                                          spacing=24, patch=PATCH)
    if len(pts) < MIN_POINTS:
        raise ValueError(f"only {len(pts)} textured grid points")
    traj, qc = track_field(run["video"], pts, ref, run["crop"],
                           run.get("rotate"), patch=PATCH)
    good = traj.groupby("particle")["corr"].median()
    keep = good[good >= 0.7].index
    traj = traj[traj["particle"].isin(keep)]
    if len(keep) < MIN_POINTS:
        raise ValueError(f"only {len(keep)} well-correlated points")

    tri, simplices = triangle_strain(traj, ref_frames=REF_FRAMES)
    tri["time"] = tri["frame"] / fps
    tri = tri[tri["min_angle"] >= MIN_ANGLE_DEG]

    base = os.path.join(TRK, name.replace(" ", "_"))
    tri.to_csv(base + "_densefield_triangles.csv", index=False)
    ref_pts, _ = reference_positions(traj, REF_FRAMES)
    np.savez(base + "_densefield_mesh.npz", points=ref_pts,
             simplices=simplices, center=np.array([cx, cy]), radius=r)

    entry = {
        "name": name, "regime": run["regime"], "well": run["well"],
        "pressure_mbar": run["pressure_mbar"],
        "circle_method": method, "radius_px": round(float(r), 1),
        "texture_threshold": threshold,
        "n_grid_points": int(len(pts)), "n_points_kept": int(len(keep)),
        "n_triangles": int(tri["triangle"].nunique()),
        "median_corr": round(qc["median_corr"], 4),
        "low_corr_fraction": round(qc["frac_frames_below_min_corr"], 5),
        "seconds": round(time.time() - t0, 1),
    }
    print(f"  {name}: {len(keep)}/{len(pts)} pts ({method}), "
          f"{entry['n_triangles']} tri, corr {entry['median_corr']:.3f} "
          f"({entry['seconds']}s)", flush=True)
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    args = ap.parse_args()
    _, runs = load_registry()
    if args.only:
        runs = [r for r in runs if r["name"] == args.only]

    all_qc = {}
    if os.path.exists(QC_PATH):
        with open(QC_PATH) as f:
            all_qc = json.load(f)
    for run in runs:
        try:
            all_qc[run["name"]] = process(run)
        except Exception as e:
            print(f"  {run['name']}: FAILED — {e}", flush=True)
            all_qc[run["name"]] = {"name": run["name"], "error": str(e)}
        with open(QC_PATH, "w") as f:
            json.dump(all_qc, f, indent=1)
    ok = sum(1 for q in all_qc.values() if "error" not in q)
    print(f"\n{ok}/{len(all_qc)} dense-field runs OK")


if __name__ == "__main__":
    main()
