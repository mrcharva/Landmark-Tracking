import numpy as np
import pandas as pd
import pytest

from stretcher.strain import fit_similarity, radial_strain, triangle_strain


def make_traj(points, transforms):
    """Trajectory df from rest points (n,2) and per-frame 2x2 transforms."""
    rows = []
    for f, A in enumerate(transforms):
        moved = points @ A.T
        for pid, (x, y) in enumerate(moved):
            rows.append({"frame": f, "particle": pid, "x": x, "y": y})
    return pd.DataFrame(rows)


RNG = np.random.default_rng(42)
POINTS = RNG.uniform(0, 500, (12, 2))


def test_recovers_known_biaxial_strain():
    exx, eyy = 0.10, 0.05
    A = np.diag([1 + exx, 1 + eyy])
    traj = make_traj(POINTS, [np.eye(2), A])
    df, _ = triangle_strain(traj)
    ref = df[df.frame == 0]
    deformed = df[df.frame == 1]
    # reference frame is exactly zero strain
    assert np.allclose(ref[["e_xx", "e_yy", "e_xy", "areal"]], 0, atol=1e-12)
    # Green-Lagrange E_xx = exx + exx^2/2 for a pure stretch
    assert np.allclose(deformed["e_xx"], exx + exx**2 / 2, atol=1e-9)
    assert np.allclose(deformed["e_yy"], eyy + eyy**2 / 2, atol=1e-9)
    assert np.allclose(deformed["e_xy"], 0, atol=1e-9)
    # engineering principal strains recover the stretches
    assert np.allclose(deformed["principal_1"], exx, atol=1e-9)
    assert np.allclose(deformed["principal_2"], eyy, atol=1e-9)
    # areal strain = det F - 1
    assert np.allclose(deformed["areal"], (1 + exx) * (1 + eyy) - 1, atol=1e-9)


def test_equibiaxial_matches_legacy_edge_strain():
    e = 0.08
    traj = make_traj(POINTS, [np.eye(2), (1 + e) * np.eye(2)])
    df, _ = triangle_strain(traj)
    deformed = df[df.frame == 1]
    # for equibiaxial stretch every measure agrees
    assert np.allclose(deformed["strain_legacy"], e, atol=1e-9)
    assert np.allclose(deformed["mean_principal"], e, atol=1e-9)


def test_rotation_gives_zero_strain():
    th = np.radians(10)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    traj = make_traj(POINTS, [np.eye(2), R])
    df, _ = triangle_strain(traj)
    deformed = df[df.frame == 1]
    # rigid rotation is not strain (the old edge-component ratios failed this)
    assert np.allclose(deformed[["e_xx", "e_yy", "e_xy", "areal"]], 0, atol=1e-9)


def test_fit_similarity_recovers_transform():
    s_true, th = 1.07, np.radians(4)
    R_true = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    t_true = np.array([3.0, -2.0])
    moved = s_true * POINTS @ R_true.T + t_true
    s, R, t = fit_similarity(POINTS, moved)
    assert s == pytest.approx(s_true, abs=1e-9)
    assert np.allclose(R, R_true, atol=1e-9)
    assert np.allclose(t, t_true, atol=1e-6)


def test_radial_strain_pure_dilation():
    e = 0.10
    center = POINTS.mean(0)  # dilation about the centroid
    moved = center + (1 + e) * (POINTS - center)
    traj = pd.concat([
        pd.DataFrame({"frame": 0, "particle": range(len(POINTS)),
                      "x": POINTS[:, 0], "y": POINTS[:, 1]}),
        pd.DataFrame({"frame": 1, "particle": range(len(POINTS)),
                      "x": moved[:, 0], "y": moved[:, 1]}),
    ], ignore_index=True)
    df = radial_strain(traj, center=center, frames=[1])
    assert np.allclose(df["radial_strain"], e, atol=1e-9)
    assert np.allclose(df["dtheta_deg"], 0, atol=1e-4)  # arccos precision floor


def test_dense_grid_uses_fixed_threshold_and_falls_back_on_low_contrast():
    """The reported dense fields used a fixed texture threshold, with the adaptive
    one only for recordings too faded to give MIN_POINTS textured patches."""
    from stretcher.densefield import MIN_POINTS, select_textured_grid

    rng = np.random.default_rng(0)
    speckled = rng.normal(128, 40, (300, 300)).clip(0, 255)
    pts, how = select_textured_grid(speckled, (150, 150), 120)
    assert how == "fixed" and len(pts) >= MIN_POINTS

    faded = rng.normal(128, 6, (300, 300)).clip(0, 255)  # patch SD well below 12
    pts, how = select_textured_grid(faded, (150, 150), 120)
    assert how == "adaptive" and len(pts) >= MIN_POINTS
