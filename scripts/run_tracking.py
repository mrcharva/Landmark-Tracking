"""Re-track experiment videos end-to-end with the fixed pipeline.

Per run: detect markers (sub-pixel) -> link -> gap-fill -> per-triangle
strain (raw, unsmoothed) -> pressure-onset time alignment -> CSVs under
results/tracking/ plus a QC entry in results/tracking/qc.json.

Usage:
    .venv/bin/python scripts/run_tracking.py [--regime static|cyclic] [--only NAME]
"""

import argparse
import json
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from stretcher import load_registry
from stretcher.detect import detect_video, read_frame, video_fps
from stretcher.strain import radial_strain, triangle_strain
from stretcher.sync import (load_pressure, phase_agreement, strain_onset,
                            xcorr_offset)
from stretcher.track import fill_gaps, link, reference_window

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "tracking")
QC_IMG = os.path.join(OUT, "qc_images")


def qc_image(run, filled, ref_frames, path):
    """Annotated reference + max-displacement frames, side by side."""
    piv_x = filled.pivot(index="frame", columns="particle", values="x")
    piv_y = filled.pivot(index="frame", columns="particle", values="y")
    disp = np.hypot(piv_x - piv_x.iloc[0], piv_y - piv_y.iloc[0]).mean(axis=1)
    f_ref, f_max = int(list(ref_frames)[0]), int(disp.idxmax())
    panels = []
    for f in (f_ref, f_max):
        gray = read_frame(run["video"], f, run["crop"], run.get("rotate"))
        vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        sub = filled[filled["frame"] == f]
        for _, m in sub.iterrows():
            cv2.circle(vis, (int(m.x), int(m.y)), 12, (0, 0, 255), 2)
            cv2.putText(vis, str(int(m.particle)), (int(m.x) + 14, int(m.y)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(vis, f"frame {f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        panels.append(vis)
    h = max(p.shape[0] for p in panels)
    panels = [cv2.copyMakeBorder(p, 0, h - p.shape[0], 0, 8,
                                 cv2.BORDER_CONSTANT) for p in panels]
    cv2.imwrite(path, np.hstack(panels))


def process_run(run, config):
    t0 = time.time()
    fps, n_frames = video_fps(run["video"])
    features = detect_video(run, progress=True)
    traj = link(features)
    filled, coverage = fill_gaps(traj, n_frames)
    n_markers = filled["particle"].nunique()

    # identity-swap QC: largest frame-to-frame displacement of any marker
    d = filled.sort_values(["particle", "frame"]).groupby("particle")[["x", "y"]].diff()
    max_jump_px = float(np.hypot(d["x"], d["y"]).max())

    ref_frames = reference_window(filled, fps)
    tri, simplices = triangle_strain(filled, ref_frames=ref_frames)  # unsmoothed
    tri["time"] = tri["frame"] / fps

    # empirical noise floor: strain SD over the quiet reference window
    quiet = tri[tri["frame"].isin(list(ref_frames))]
    noise_floor = float(quiet.groupby("triangle")["mean_principal"].std().median())

    # full-waveform alignment onto the pressure record's time base
    pressure = load_pressure(run["pressure_csv"])
    mean_ts = tri.groupby("time")["mean_principal"].mean()
    offset, pair_score = xcorr_offset(mean_ts.index.to_numpy(),
                                      mean_ts.to_numpy(), pressure)
    agreement = phase_agreement(mean_ts.index.to_numpy(), mean_ts.to_numpy(),
                                pressure, offset)
    synced = tri.copy()
    synced["time"] = synced["time"] - offset

    base = os.path.join(OUT, run["name"].replace(" ", "_"))
    filled.assign(time=filled["frame"] / fps).to_csv(base + "_markers.csv", index=False)
    synced.to_csv(base + "_triangles.csv", index=False)
    pressure.to_csv(base + "_pressure.csv", index=False)

    radial_ok = False
    if run.get("inner_circle_cropped"):
        c = run["inner_circle_cropped"]
        rad = radial_strain(filled, center=(c["cx"], c["cy"]),
                            ref_frames=ref_frames)
        rad["time"] = rad["frame"] / fps - offset
        rad.to_csv(base + "_radial.csv", index=False)
        radial_ok = True

    os.makedirs(QC_IMG, exist_ok=True)
    qc_image(run, filled, ref_frames,
             os.path.join(QC_IMG, run["name"].replace(" ", "_") + ".png"))

    qc = {
        "name": run["name"], "regime": run["regime"], "well": run["well"],
        "pressure_mbar": run["pressure_mbar"], "fps": fps, "n_frames": n_frames,
        "n_markers_kept": int(n_markers),
        "n_markers_nominal": run["n_markers_nominal"],
        "n_triangles": int(len(simplices)),
        "n_ref_frames": len(list(ref_frames)),
        "noise_floor_strain_sd": round(noise_floor, 5),
        "max_jump_px_per_frame": round(max_jump_px, 1),
        "coverage_all_markers": {str(k): round(float(v), 4)
                                 for k, v in coverage.items()},
        "sync_offset_s": round(float(offset), 3),
        "sync_pair_score": round(float(pair_score), 3),
        "sync_phase_agreement": round(float(agreement), 3),
        "radial": radial_ok,
        "seconds": round(time.time() - t0, 1),
    }
    print(f"  {run['name']}: {n_markers}/{run['n_markers_nominal']} markers, "
          f"{len(simplices)} tri, ref {qc['n_ref_frames']}f, "
          f"noise {noise_floor:.4f}, jump {max_jump_px:.0f}px, "
          f"offset {offset:.2f}s (score {pair_score:.2f}, "
          f"phase {agreement:.2f}) ({qc['seconds']}s)", flush=True)
    return qc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", choices=["static", "cyclic"])
    ap.add_argument("--only")
    ap.add_argument("--include-excluded", action="store_true")
    args = ap.parse_args()

    config, runs = load_registry(regime=args.regime,
                                 include_excluded=args.include_excluded)
    if args.only:
        runs = [r for r in runs if r["name"] == args.only]
        if not runs:
            sys.exit(f"no run named {args.only}")

    os.makedirs(OUT, exist_ok=True)
    qc_path = os.path.join(OUT, "qc.json")
    all_qc = {}
    if os.path.exists(qc_path):
        with open(qc_path) as f:
            all_qc = json.load(f)

    for run in runs:
        try:
            all_qc[run["name"]] = process_run(run, config)
        except Exception as e:  # keep going; QC records the failure
            print(f"  {run['name']}: FAILED — {e}", flush=True)
            all_qc[run["name"]] = {"name": run["name"], "error": str(e)}
        with open(qc_path, "w") as f:
            json.dump(all_qc, f, indent=1)

    ok = sum(1 for q in all_qc.values() if "error" not in q)
    print(f"\n{ok}/{len(all_qc)} runs processed OK -> {OUT}")


if __name__ == "__main__":
    main()
