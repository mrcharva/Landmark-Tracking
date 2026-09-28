"""Marker detection: video frames -> per-frame sub-pixel marker positions.

Streams frames straight from the .mp4 (no tiff dump / rawFrames.pkl caching
like the old pipeline). Detection follows the submission's approach (crop +
adaptive threshold + regionprops filters, parameters from the registry) but
adds an intensity-weighted sub-pixel centroid computed on the inverted
grayscale image inside each blob, instead of the binary-mask centroid whose
position shifts with the threshold.
"""

import cv2
import numpy as np
import pandas as pd
from skimage import measure


ROTATIONS = {"cw": cv2.ROTATE_90_CLOCKWISE, "ccw": cv2.ROTATE_90_COUNTERCLOCKWISE}


def iter_frames(video_path, crop=None, rotate=None):
    """Yield (frame_index, grayscale_frame). crop = registry dict or None.

    rotate: 'cw'/'ccw' for videos stored landscape (some records lack the
    portrait orientation the registry crops assume; the submission pipeline
    silently clipped those to 320 rows).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(video_path)
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if rotate is not None:
            gray = cv2.rotate(gray, ROTATIONS[rotate])
        if crop is not None:
            gray = gray[crop["y_min"]:crop["y_max"], crop["x_min"]:crop["x_max"]]
        yield i, gray
        i += 1
    cap.release()


def video_fps(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return fps, n


def detect_markers(gray, threshold, blob_filter):
    """Detect dark markers in one grayscale frame. Returns list of dicts.

    threshold/blob_filter: registry dicts (block_size/C; min_area..axis_ratio).
    Positions are intensity-weighted centroids (sub-pixel) of the inverted
    grayscale inside each accepted blob.
    """
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        threshold["block_size"], threshold["C"])
    # markers are dark -> 0 in binary; label the dark regions
    labels = measure.label(binary, background=255)
    h, w = gray.shape
    inverted = 255.0 - gray.astype(float)
    out = []
    for region in measure.regionprops(labels, intensity_image=inverted):
        if not (blob_filter["min_area"] <= region.area <= blob_filter["max_area"]):
            continue
        cy, cx = region.centroid
        if not (blob_filter["min_height"] * h <= cy <= blob_filter["max_height"] * h):
            continue
        if not (blob_filter["min_width"] * w <= cx <= blob_filter["max_width"] * w):
            continue
        if region.axis_major_length > 0:
            if region.axis_minor_length / region.axis_major_length < blob_filter["axis_ratio"]:
                continue
        # sub-pixel: intensity-weighted centroid within the blob
        wy, wx = region.centroid_weighted
        out.append({"x": wx, "y": wy, "area": region.area,
                    "eccentricity": region.eccentricity})
    return out


def detect_video(run, progress=False):
    """Run detection over a whole registry run. Returns a features DataFrame
    with columns x, y, area, eccentricity, frame (positions in cropped px)."""
    rows = []
    for i, gray in iter_frames(run["video"], run["crop"], run.get("rotate")):
        for m in detect_markers(gray, run["threshold"], run["blob_filter"]):
            m["frame"] = i
            rows.append(m)
        if progress and i % 500 == 0:
            print(f"  {run['name']}: frame {i}", flush=True)
    return pd.DataFrame(rows)


def read_frame(video_path, index, crop=None, rotate=None):
    """Read a single grayscale (rotated, cropped) frame by index."""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise ValueError(f"cannot read frame {index} of {video_path}")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if rotate is not None:
        gray = cv2.rotate(gray, ROTATIONS[rotate])
    if crop is not None:
        gray = gray[crop["y_min"]:crop["y_max"], crop["x_min"]:crop["x_max"]]
    return gray
