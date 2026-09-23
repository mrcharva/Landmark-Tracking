"""Experiment registry: one YAML replaces dfParams.pkl, syncDict,
finalCircles and the four divergent exclusion lists of the old notebooks."""

import os

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "experiments.yaml")


def load_registry(path=DEFAULT_PATH, regime=None, include_excluded=False):
    """Return (config, runs). Paths in runs are made absolute.

    regime: optional 'static'/'cyclic' filter.
    include_excluded: keep runs marked excluded (for QC/diagnostics).
    """
    with open(path) as f:
        doc = yaml.safe_load(f)
    runs = doc.pop("runs")
    for r in runs:
        r["video"] = os.path.join(ROOT, r["video"])
        r["pressure_csv"] = os.path.join(ROOT, r["pressure_csv"])
    if regime is not None:
        runs = [r for r in runs if r["regime"] == regime]
    if not include_excluded:
        runs = [r for r in runs if not r.get("excluded", False)]
    return doc, runs
