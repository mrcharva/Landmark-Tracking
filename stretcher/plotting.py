"""Shared figure style + helpers (defined once; the notebooks had 5 copies)."""

import os

import matplotlib.pyplot as plt
import numpy as np

STYLE = {
    "font.family": "Arial",
    "font.weight": "bold",
    "axes.labelweight": "bold",
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "font.size": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
}

# Pressure is an ordered variable, so it gets one hue getting darker with
# depth rather than three unrelated hues (which also read the same to a
# protanope, and survive grayscale printing only by their dash pattern).
PRESSURE_PALETTE = {50: "#e8615f", 100: "#c22b2a", 200: "#6e1413"}
PRESSURE_DASHES = {50: "-", 100: "--", 200: "-."}


def apply_style():
    plt.rcParams.update(STYLE)


def save_figure(fig, name, outdir, dpi_png=300, dpi_tiff=600):
    """Save PNG + TIFF pair (manuscript convention)."""
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, name + ".png"), dpi=dpi_png,
                bbox_inches="tight")
    fig.savefig(os.path.join(outdir, name + ".tiff"), dpi=dpi_tiff,
                bbox_inches="tight")


def square_wave(pressure_mbar, period_s=30.0, duration_s=60.0, n=4000):
    """Ideal stimulation waveform: 0 for the first quarter-period, then
    -pressure with 50% duty. Returns (t, p)."""
    t = np.linspace(0.0, duration_s, n)
    phase = ((t - period_s / 4) % period_s) < (period_s / 2)
    p = np.where(phase & (t >= period_s / 4), -float(pressure_mbar), 0.0)
    return t, p
