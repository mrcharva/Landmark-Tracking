"""Inner-ring segmentation + pixel size calibration (single implementation;
the notebooks carried five divergent Hough variants plus hand-picked
`finalCircles`). Registry circles are used as the authoritative fallback."""

import cv2
import numpy as np


def find_inner_circle(gray, r_range=(0.15, 0.45)):
    """Detect the device's inner ring in a grayscale (cropped) frame.

    Runs HoughCircles over a small parameter sweep and returns the median
    consensus circle (cx, cy, r) in pixels, or None. r_range is the radius
    search window as a fraction of min(image size).
    """
    blur = cv2.GaussianBlur(gray, (7, 7), 2)
    lim = min(gray.shape)
    r_min, r_max = int(r_range[0] * lim), int(r_range[1] * lim)
    candidates = []
    for p1 in (60, 100, 140):
        for p2 in (40, 60, 80):
            circles = cv2.HoughCircles(
                blur, cv2.HOUGH_GRADIENT, dp=1, minDist=lim,
                param1=p1, param2=p2, minRadius=r_min, maxRadius=r_max)
            if circles is not None and len(circles[0]) == 1:
                candidates.append(circles[0][0])
    if not candidates:
        return None
    c = np.median(np.array(candidates), axis=0)
    return float(c[0]), float(c[1]), float(c[2])


def circle_from_run(run, gray=None):
    """Ring circle for a registry run: detected if possible, else the
    curated `inner_circle_cropped` entry. Returns ((cx, cy), r)."""
    if gray is not None:
        found = find_inner_circle(gray)
        if found is not None:
            return (found[0], found[1]), found[2]
    manual = run.get("inner_circle_cropped")
    if manual is None:
        raise ValueError(f"no circle for {run['name']}")
    return (manual["cx"], manual["cy"]), manual["r"]


def um_per_px(ring_radius_px, ring_diameter_mm=16.0):
    return ring_diameter_mm * 1000.0 / (2.0 * ring_radius_px)
