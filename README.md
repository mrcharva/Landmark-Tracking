# Landmark-Tracking

Landmark tracking and in-plane strain analysis for a pneumatic cell-stretching
insert. This pipeline produced every strain value reported in the manuscript
*A pneumatic insert for parallel biaxial substrate stretching in standard
6-well culture plates* (Carvalho et al., submitted).

Video frames are segmented into sub-pixel landmark positions, linked into
trajectories, triangulated, and converted to strain through the deformation
gradient of each triangle. A dense correlation-patch field tracked from the
same recordings serves as an independent check on the landmark result.

## Versions

| Version | Contents | Status |
|---|---|---|
| **v2.0** | the `stretcher` package and scripts in this directory | produced the reported results |
| v1.0 | a single notebook, now in [`legacy/`](legacy/) | superseded; see its README |

## Requirements

Python 3.11. Install the pinned environment the results were produced with:

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Data

The recordings and pressure logs are in the Zenodo data deposit that
accompanies the manuscript (DOI to be added on publication of the deposit).
Place them under `share/`, keeping the file names listed in
`experiments.yaml`:

```
share/Static/20241003_<well>_<mbar>_cont_HD.mp4
share/Static/20241003_<well>_<mbar>_cont.csv
share/Cyclic/...
```

`experiments.yaml` is the single source of truth for every recording: crop,
threshold and blob filters, rotation (several videos are stored landscape),
the curated inner-ring circle used for pixel calibration, and each exclusion
with its reason. No per-recording value is hard-coded anywhere else.

## Running

```
.venv/bin/python scripts/run_tracking.py        # landmarks -> results/tracking/
.venv/bin/python scripts/run_densefield.py      # dense field -> results/tracking/
.venv/bin/python scripts/analyze_results.py     # summary -> analysis_notes/
.venv/bin/python scripts/sweep_parameters.py    # parameter sensitivity -> results/sweeps/
```

`run_tracking.py` accepts `--regime static|cyclic` and `--only <recording>`.
Each script writes a QC record next to its outputs.

## Verifying a run

```
.venv/bin/python -m pytest tests/
```

The tests check strain, synchronization, resampling and fitting against
synthetic cases with known answers.

`analysis_notes/reanalysis_summary.md` is committed as the reference output.
After running the pipeline on the deposited data, `git diff analysis_notes/`
should show no change.

## Package layout

| Module | Role |
|---|---|
| `registry` | loads `experiments.yaml` |
| `detect` | frames to sub-pixel landmark positions |
| `track` | linking into trajectories, with an explicit gap policy |
| `ring` | inner-ring segmentation and pixel-size calibration |
| `strain` | per-triangle deformation gradient and principal strains |
| `sync` | strain-to-pressure alignment from the pressure record |
| `resample` | resampling onto a common time grid |
| `densefield` | dense correlation-patch displacement field |
| `stats` | aggregation from triangles to membrane to condition |
| `results` | loaders for the tracked outputs |
| `plotting` | shared figure style |

Statistics are aggregated triangle to membrane to condition. Values from
different vacuum pressures are never pooled.

## License

GPL-3.0. See [LICENSE](LICENSE).
