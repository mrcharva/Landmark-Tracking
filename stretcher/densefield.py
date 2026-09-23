"""Dense displacement field by normalized cross-correlation patch tracking
(DIC-style), using the painted speckle itself instead of ~10 segmented blobs.

Each grid point is a small template cut from the (pre-onset-averaged)
reference frame and located in every frame by ZNCC (cv2.TM_CCOEFF_NORMED,
contrast-invariant - robust to the landmark fading seen at 200 mbar), with
sub-pixel refinement by parabolic fit of the correlation peak. The search is
incremental (window around the previous position), so large cumulative
deformations are tracked with a small window.

Output is a trajectory DataFrame compatible with stretcher.strain, so the
same deformation-gradient machinery yields a strain FIELD over hundreds of
points rather than ~10 landmarks.

# ponytail: pure-translation patch model; at 15% strain a 21 px template
# distorts by ~3 px which ZNCC tolerates - switch to affine subset matching
# (classic DIC) only if peak correlations degrade.
"""

import cv2
import numpy as np
import pandas as pd

from stretcher.detect import iter_frames


def reference_image(video, crop=None, rotate=None, ref_frames=range(30)):
    """Average of the quiet pre-onset frames as float32 grayscale."""
    acc, n = None, 0
    ref_set = set(ref_frames)
    for i, gray in iter_frames(video, crop, rotate):
        if i in ref_set:
            g = gray.astype(np.float32)
            acc = g if acc is None else acc + g
            n += 1
        if i > max(ref_set):
            break
    return acc / n


def select_grid(ref_img, center, radius, spacing=22, patch=21, min_std=None):
    """Grid points inside the membrane circle whose patch has speckle texture.

    min_std: minimum grayscale SD inside the template - blank gel patches
    carry no signal and are excluded rather than tracked badly. When None
    (default), the threshold adapts to the video's own contrast:
    max(4, 0.35 * 95th percentile of candidate patch SDs), so low-contrast
    recordings (faded landmarks) still yield their best-textured patches.
    """
    h, w = ref_img.shape
    half = patch // 2
    cands = []
    for y in np.arange(half + 1, h - half - 1, spacing):
        for x in np.arange(half + 1, w - half - 1, spacing):
            if np.hypot(x - center[0], y - center[1]) > radius:
                continue
            tpl = ref_img[int(y) - half:int(y) + half + 1,
                          int(x) - half:int(x) + half + 1]
            cands.append((float(x), float(y), float(tpl.std())))
    if not cands:
        return np.empty((0, 2))
    stds = np.array([s for _, _, s in cands])
    if min_std is None:
        min_std = max(4.0, 0.35 * float(np.percentile(stds, 95)))
    return np.array([(x, y) for x, y, s in cands if s >= min_std])


FIXED_MIN_STD = 12.0  # grayscale SD a patch needs to count as textured
MIN_POINTS = 6  # fewest grid points that still triangulate usefully


def select_textured_grid(ref_img, center, radius, spacing=24, patch=27):
    """Grid points for the dense field, and which texture threshold chose them.

    The fixed threshold is applied first. A low-contrast recording (faded
    landmarks) that leaves fewer than MIN_POINTS patches falls back to the
    adaptive threshold of select_grid, so it still yields its best-textured
    patches instead of no field at all. This is the rule the reported dense
    fields were produced with: 14 recordings used the fixed threshold and 8
    needed the fallback.

    Returns (points, "fixed" | "adaptive").
    """
    pts = select_grid(ref_img, center, radius, spacing=spacing, patch=patch,
                      min_std=FIXED_MIN_STD)
    if len(pts) >= MIN_POINTS:
        return pts, "fixed"
    return select_grid(ref_img, center, radius, spacing=spacing, patch=patch), "adaptive"


def _subpixel(res, loc):
    """Parabolic sub-pixel refinement of a correlation peak."""
    x, y = loc
    dx = dy = 0.0
    if 0 < x < res.shape[1] - 1:
        c0, c1, c2 = res[y, x - 1], res[y, x], res[y, x + 1]
        d = c0 - 2 * c1 + c2
        if d < 0:
            dx = 0.5 * (c0 - c2) / d
    if 0 < y < res.shape[0] - 1:
        c0, c1, c2 = res[y - 1, x], res[y, x], res[y + 1, x]
        d = c0 - 2 * c1 + c2
        if d < 0:
            dy = 0.5 * (c0 - c2) / d
    return dx, dy


def track_field(video, points, ref_img, crop=None, rotate=None,
                patch=21, search=12, min_corr=0.5, progress=False):
    """Track reference patches through the video.

    Returns (traj DataFrame [frame, particle, x, y, corr], qc dict).
    A point whose correlation drops below min_corr keeps its last position
    for that frame (and the low corr is recorded for QC/filtering).
    """
    half = patch // 2
    templates = []
    for x, y in points:
        templates.append(np.ascontiguousarray(
            ref_img[int(round(y)) - half:int(round(y)) + half + 1,
                    int(round(x)) - half:int(round(x)) + half + 1]))
    pos = points.astype(np.float64).copy()
    rows = []
    for i, gray in iter_frames(video, crop, rotate):
        g = gray.astype(np.float32)
        h, w = g.shape
        for j, tpl in enumerate(templates):
            cx, cy = pos[j]
            x0 = int(round(cx)) - half - search
            y0 = int(round(cy)) - half - search
            x1 = int(round(cx)) + half + search + 1
            y1 = int(round(cy)) + half + search + 1
            x0c, y0c = max(0, x0), max(0, y0)
            win = g[y0c:min(h, y1), x0c:min(w, x1)]
            if win.shape[0] < patch or win.shape[1] < patch:
                rows.append((i, j, cx, cy, 0.0))
                continue
            res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
            _, corr, _, loc = cv2.minMaxLoc(res)
            if corr >= min_corr:
                dx, dy = _subpixel(res, loc)
                cx = x0c + loc[0] + half + dx
                cy = y0c + loc[1] + half + dy
                pos[j] = (cx, cy)
            rows.append((i, j, cx, cy, float(corr)))
        if progress and i % 300 == 0:
            print(f"  field: frame {i}", flush=True)
    traj = pd.DataFrame(rows, columns=["frame", "particle", "x", "y", "corr"])
    qc = {
        "n_points": len(points),
        "median_corr": float(traj["corr"].median()),
        "frac_frames_below_min_corr": float((traj["corr"] < min_corr).mean()),
    }
    return traj, qc
