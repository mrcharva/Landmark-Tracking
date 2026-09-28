"""Strain from marker trajectories via per-triangle deformation gradients.

Replaces the submission's per-edge engineering strains:
- edge-mean strain kept as `strain_legacy` for comparability,
- proper 2D deformation gradient F per Delaunay triangle giving principal
  strains, areal strain (det F - 1) and true epsilon_xx/yy/xy. The old
  strain_xx/yy divided by signed edge components and blew up for
  near-vertical/horizontal edges; these do not.
- no off-by-one: strain is computed for every frame against the reference
  frame, and the reference frame's strain is exactly 0.

Radial strain: the old code located the deformed ring centre from the two
markers nearest the centre (and measured everything against that guess).
Here the rest->deformed similarity transform is fit to ALL markers by least
squares, and per-marker radial strain / angle change are reported per frame.
"""

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.spatial import Delaunay


def triangulate(points):
    """Delaunay simplices (k,3) on reference-frame marker positions (n,2)."""
    return Delaunay(points).simplices


def _positions(traj, frame):
    sub = traj[traj["frame"] == frame].sort_values("particle")
    return sub[["x", "y"]].to_numpy(), sub["particle"].to_numpy()


def reference_positions(traj, ref_frames):
    """Marker positions averaged over a set of (pre-onset) frames.

    Averaging N quiet frames reduces reference noise by ~sqrt(N); a single
    reference frame bakes its noise into every strain sample as a bias.
    Returns (points (n,2), particle ids) ordered by particle id.
    """
    sub = traj[traj["frame"].isin(list(ref_frames))]
    g = sub.groupby("particle")[["x", "y"]].mean().sort_index()
    return g.to_numpy(), g.index.to_numpy()


def triangle_geometry(points, simplices):
    """Per-triangle reference area (px^2) and minimum interior angle (deg)."""
    areas, min_angles = [], []
    for tri in simplices:
        p = points[tri]
        a = 0.5 * abs(np.cross(p[1] - p[0], p[2] - p[0]))
        angs = []
        for k in range(3):
            u, v = p[(k + 1) % 3] - p[k], p[(k + 2) % 3] - p[k]
            cosang = np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1)
            angs.append(np.degrees(np.arccos(cosang)))
        areas.append(a)
        min_angles.append(min(angs))
    return np.array(areas), np.array(min_angles)


def triangle_strain(traj, ref_frame=0, ref_frames=None, smooth_window=None,
                    fps=None):
    """Per-triangle strain time series.

    Returns (df, simplices). df columns: frame, triangle, strain_legacy,
    e_xx, e_yy, e_xy, principal_1, principal_2, areal, mean_principal,
    area0, min_angle. Engineering measures (principal_i = stretch_i - 1,
    areal = det F - 1). area0/min_angle are reference-frame triangle
    geometry, for quality filtering and area-weighted averaging downstream.

    ref_frames: iterable of frame indices whose AVERAGED positions form the
    reference configuration (preferred: the pre-onset quiet window).
    Falls back to the single ref_frame when None.

    smooth_window: optional Savitzky-Golay window in SECONDS (needs fps).
    Applied per triangle, polyorder 2. Off by default: the submission's
    150-frame (5 s) window manufactured under/overshoot on the transient.
    """
    if ref_frames is not None:
        ref_pts, ref_ids = reference_positions(traj, ref_frames)
    else:
        ref_pts, ref_ids = _positions(traj, ref_frame)
    simplices = triangulate(ref_pts)
    areas0, min_angles = triangle_geometry(ref_pts, simplices)
    frames = np.sort(traj["frame"].unique())

    # (n_frames, n_markers, 2) position array, markers ordered like ref_ids
    pivot_x = traj.pivot(index="frame", columns="particle", values="x")[ref_ids]
    pivot_y = traj.pivot(index="frame", columns="particle", values="y")[ref_ids]
    pos = np.stack([pivot_x.to_numpy(), pivot_y.to_numpy()], axis=-1)

    rows = []
    for t_idx, tri in enumerate(simplices):
        X = ref_pts[tri]                       # (3,2) rest vertices
        dX = np.array([X[1] - X[0], X[2] - X[0]]).T   # (2,2)
        dX_inv = np.linalg.inv(dX)
        L0 = np.array([np.linalg.norm(X[1] - X[0]),
                       np.linalg.norm(X[2] - X[0]),
                       np.linalg.norm(X[2] - X[1])])
        x = pos[:, tri, :]                     # (n_frames, 3, 2)
        dx = np.stack([x[:, 1] - x[:, 0], x[:, 2] - x[:, 0]], axis=-1)  # (nf,2,2)
        F = dx @ dX_inv                        # (nf,2,2)
        C = np.swapaxes(F, 1, 2) @ F           # right Cauchy-Green
        E = 0.5 * (C - np.eye(2))              # Green-Lagrange
        eigval = np.linalg.eigvalsh(C)         # ascending
        stretch = np.sqrt(np.clip(eigval, 0, None))
        areal = np.linalg.det(F) - 1.0
        L = np.stack([np.linalg.norm(x[:, 1] - x[:, 0], axis=1),
                      np.linalg.norm(x[:, 2] - x[:, 0], axis=1),
                      np.linalg.norm(x[:, 2] - x[:, 1], axis=1)], axis=1)
        legacy = ((L - L0) / L0).mean(axis=1)
        rows.append(pd.DataFrame({
            "frame": frames, "triangle": t_idx,
            "strain_legacy": legacy,
            "e_xx": E[:, 0, 0], "e_yy": E[:, 1, 1], "e_xy": E[:, 0, 1],
            "principal_1": stretch[:, 1] - 1.0,   # major
            "principal_2": stretch[:, 0] - 1.0,   # minor
            "areal": areal,
            "mean_principal": 0.5 * (stretch[:, 0] + stretch[:, 1]) - 1.0,
            "area0": areas0[t_idx], "min_angle": min_angles[t_idx],
        }))
    df = pd.concat(rows, ignore_index=True)

    if smooth_window is not None:
        if fps is None:
            raise ValueError("smooth_window needs fps")
        win = max(5, int(round(smooth_window * fps)) | 1)  # odd, >=5
        value_cols = df.columns.difference(["frame", "triangle", "area0", "min_angle"])
        df = df.sort_values(["triangle", "frame"])
        for col in value_cols:
            df[col] = df.groupby("triangle")[col].transform(
                lambda s: savgol_filter(s, min(win, len(s) - (len(s) + 1) % 2), 2,
                                        mode="nearest"))
    return df, simplices


def fit_similarity(X, x):
    """Least-squares similarity transform (scale s, rotation R, translation t)
    mapping rest points X (n,2) to deformed points x (n,2). Returns s, R, t."""
    Xc, xc = X.mean(0), x.mean(0)
    A, B = X - Xc, x - xc
    # Umeyama
    cov = B.T @ A / len(X)
    U, S, Vt = np.linalg.svd(cov)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1.0, d])
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (A ** 2).sum(axis=None) * len(X)
    t = xc - s * R @ Xc
    return s, R, t


def radial_strain(traj, center, ref_frame=0, ref_frames=None, frames=None):
    """Per-marker radial strain and angle change vs the ring centre.

    center: (cx, cy) of the inner ring in the REFERENCE frame (cropped px).
    The deformed-centre position at each frame is the reference centre mapped
    through the similarity transform fit to all markers (not 2 of them).
    Returns df: frame, particle, radial_strain, dtheta_deg.
    """
    if ref_frames is not None:
        ref_pts, ids = reference_positions(traj, ref_frames)
    else:
        ref_pts, ids = _positions(traj, ref_frame)
    c0 = np.asarray(center, float)
    v0 = ref_pts - c0
    r0 = np.linalg.norm(v0, axis=1)
    if frames is None:
        frames = np.sort(traj["frame"].unique())
    rows = []
    for f in frames:
        pts, ids_f = _positions(traj, f)
        assert np.array_equal(ids, ids_f), "trajectories must be gap-filled"
        s, R, t = fit_similarity(ref_pts, pts)
        c = s * R @ c0 + t
        v = pts - c
        r = np.linalg.norm(v, axis=1)
        cosang = np.clip((v0 * v).sum(1) / (r0 * r), -1, 1)
        rows.append(pd.DataFrame({
            "frame": f, "particle": ids,
            "radial_strain": (r - r0) / r0,
            "dtheta_deg": np.degrees(np.arccos(cosang)),
        }))
    return pd.concat(rows, ignore_index=True)
