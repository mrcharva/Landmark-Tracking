# Legacy: v1.0 notebook

This folder holds the contents of release v1.0, moved here so the repository
root can carry the v2.0 pipeline. The only omission is `video/pressure.mp4`, a
2-byte placeholder; recordings are distributed through Zenodo, not this
repository. The v1.0 tag and its Zenodo
archive still point at the original layout.

v1.0 is superseded. It is not the code that produced the values reported in
the accompanying manuscript, and it should not be used for new analysis:

- strain is smoothed with a Savitzky-Golay filter (window 150, order 2), which
  distorts the loading transient
- strain components are taken as `strain_xx` / `strain_yy` rather than from the
  per-triangle deformation gradient, so they are not invariant under rotation
- its example video was a 2-byte placeholder, so the notebook could not be run
  on the example as published

The v2.0 pipeline at the repository root replaces it.
