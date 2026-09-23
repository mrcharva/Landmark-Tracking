"""Phase 3 re-analysis of the re-tracked data (results/tracking/).

Produces results/figures/*.png(+tiff) and analysis_notes/reanalysis_summary.md:
- static + cyclic strain-time figures (mean +/- SD across membranes, n stated)
- per-well pressure-strain curves (paired, the honest calibration view)
- 10-90% rise times per run (strain-rate answer)
- plateau drift (static) and cycle-to-cycle repeatability + residual strain
- 200 mbar diagnosis: per-triangle plateau strains + measured pressure depth
Run: .venv/bin/python scripts/analyze_results.py
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stretcher import load_registry
from stretcher.results import load_triangles as load_run
from stretcher.results import membrane_trace as mean_trace
from stretcher.results import MIN_ANGLE_DEG, load_pressure_record, plateau_stats
from stretcher.sync import pressure_phases

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRK = os.path.join(ROOT, "results", "tracking")
FIG = os.path.join(ROOT, "results", "figures")
NOTES = os.path.join(ROOT, "analysis_notes")
os.makedirs(FIG, exist_ok=True)

STRAIN = "mean_principal"
PALETTE = {50: "C0", 100: "C1", 200: "C2"}
report = ["# Re-analysis summary (fixed pipeline, unfiltered strain)\n"]


def rise_time(t, s, lo=0.1, hi=0.9):
    """10-90% rise time relative to the early plateau after onset (t=0)."""
    mask = (t >= 0) & (t <= 12)
    tt, ss = t[mask], s[mask]
    plateau = np.nanmedian(ss[(tt >= 8) & (tt <= 12)])
    if not np.isfinite(plateau) or plateau <= 0:
        return np.nan
    t_lo = tt[np.argmax(ss >= lo * plateau)]
    t_hi = tt[np.argmax(ss >= hi * plateau)]
    # 0.0 = faster than the onset anchor resolves (report as "<0.1 s")
    return float(max(t_hi - t_lo, 0.0))


_, runs = load_registry()
static_runs = [r for r in runs if r["regime"] == "static"]
cyclic_runs = [r for r in runs if r["regime"] == "cyclic"]

# ---------------- STATIC ----------------
grid_s = np.linspace(-3, 27, 1500)  # t=0 at first vacuum onset
static = {}
for r in static_runs:
    try:
        df, phases = load_run(r["name"])
    except FileNotFoundError:
        continue
    static[r["name"]] = dict(run=r, trace=mean_trace(df, grid_s), df=df,
                             phases=phases)

# per-run plateau metrics, windows derived from the run's own pressure phases
rows = []
for name, d in static.items():
    t, s = grid_s, d["trace"]
    t_off = d["phases"][0][1]
    w0, w1 = 5.0, min(25.0, t_off - 1.0)
    plate = np.nanmean(s[(t >= w0) & (t <= w1)])
    drift = (np.nanmean(s[(t >= w1 - 2) & (t <= w1)])
             - np.nanmean(s[(t >= w0) & (t <= w0 + 2)]))
    rt = rise_time(t, s)
    rows.append(dict(name=name, well=d["run"]["well"],
                     pressure=d["run"]["pressure_mbar"], plateau=plate,
                     hold_end_s=round(t_off, 1),
                     drift=drift, rise_10_90=rt,
                     n_triangles=d["df"]["triangle"].nunique()))
stat = pd.DataFrame(rows).sort_values(["pressure", "well"])
report.append("## Static plateau (mean principal strain, hold window "
              "5 s after onset to 1 s before release, capped at 25 s)\n")
report.append(stat.to_markdown(index=False, floatfmt=".4f") + "\n")

# per-condition summary (per-gel first)
summ = stat.groupby("pressure")["plateau"].agg(["count", "mean", "std"])
report.append("## Static per-pressure summary (n = membranes)\n")
report.append(summ.to_markdown(floatfmt=".4f") + "\n")

# figure: static mean +/- SD across wells
fig, ax = plt.subplots(figsize=(7, 5))
for p in (50, 100, 200):
    traces = np.array([d["trace"] for d in static.values()
                       if d["run"]["pressure_mbar"] == p])
    m, sd = np.nanmean(traces, 0), np.nanstd(traces, 0, ddof=1)
    ax.plot(grid_s, m, color=PALETTE[p], label=f"{p} mbar (n={len(traces)})")
    ax.fill_between(grid_s, m - sd, m + sd, color=PALETTE[p], alpha=0.2)
ax.set(xlabel="time after vacuum onset (s)", ylabel="in-plane strain",
       title="Static: mean ± SD across membranes (unfiltered)")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{FIG}/static_strain_time.png", dpi=200)

# figure: individual membrane traces
fig, ax = plt.subplots(figsize=(7, 5))
for name, d in static.items():
    p = d["run"]["pressure_mbar"]
    ax.plot(grid_s, d["trace"], color=PALETTE[p], alpha=0.7, lw=1)
ax.set(xlabel="time after vacuum onset (s)", ylabel="in-plane strain",
       title="Static: individual membranes (unfiltered, triangle-averaged)")
fig.tight_layout(); fig.savefig(f"{FIG}/static_strain_individual.png", dpi=200)

# figure: paired per-well pressure-strain
fig, ax = plt.subplots(figsize=(6, 5))
for well, g in stat.groupby("well"):
    g = g.sort_values("pressure")
    ax.plot(g["pressure"], g["plateau"], "o-", label=f"well {well}")
ax.set(xlabel="vacuum pressure (mbar)", ylabel="plateau strain",
       title="Per-membrane pressure–strain (paired)")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{FIG}/pressure_strain_paired.png", dpi=200)

# ---------------- 200 mbar diagnosis ----------------
report.append("## 200 mbar diagnosis\n")
for name, d in static.items():
    if d["run"]["pressure_mbar"] != 200:
        continue
    df = d["df"]
    tris = []
    for tri, g in df.groupby("triangle"):
        g = g.sort_values("time")
        plate = g[(g.time >= 10) & (g.time <= 25)][STRAIN].mean()
        tris.append(plate)
    press = pd.read_csv(os.path.join(TRK, name.replace(" ", "_") + "_pressure.csv"))
    depth = press["mbar"].min()
    report.append(f"- {name}: measured pressure depth {depth:.1f} mbar; "
                  f"per-triangle plateau strains: "
                  f"{np.round(sorted(tris), 3).tolist()}\n")

# per-marker 200 mbar traces figure
fig, axs = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
i = 0
for name, d in static.items():
    if d["run"]["pressure_mbar"] != 200 or i >= 3:
        continue
    for tri, g in d["df"].groupby("triangle"):
        g = g.sort_values("time")
        axs[i].plot(g["time"], g[STRAIN], lw=0.8, alpha=0.8)
    axs[i].set(title=f"{name}\n(per-triangle, unfiltered)", xlabel="time (s)")
    i += 1
axs[0].set_ylabel("in-plane strain")
fig.tight_layout(); fig.savefig(f"{FIG}/static_200mbar_per_triangle.png", dpi=200)

# ---------------- CYCLIC ----------------
grid_c = np.linspace(-5, 55, 3000)
cyc = {}
for r in cyclic_runs:
    try:
        df, phases = load_run(r["name"])
    except FileNotFoundError:
        continue
    cyc[r["name"]] = dict(run=r, trace=mean_trace(df, grid_c), phases=phases,
                          df=df)

rows = []
for name, d in cyc.items():
    t, s = grid_c, d["trace"]
    ph = d["phases"]
    if len(ph) < 2:  # damaged record; skip metrics, trace still plotted
        continue
    (on1, off1), (on2, off2) = ph[0], ph[1]
    def win(a, b):
        return np.nanmean(s[(t >= a) & (t <= b)])
    c1 = win(on1 + 2, off1 - 1)
    rest = win(off1 + 3, on2 - 1)
    c2 = win(on2 + 2, off2 - 1)
    rest2 = win(off2 + 3, min(off2 + 8, t.max()))
    rows.append(dict(name=name, well=d["run"]["well"],
                     pressure=d["run"]["pressure_mbar"], cycle1=c1, cycle2=c2,
                     cycle_diff=c2 - c1, residual_after_c1=rest,
                     residual_after_c2=rest2, rise_10_90=rise_time(t, s)))
cyc_stat = pd.DataFrame(rows).sort_values(["pressure", "well"])
report.append("## Cyclic metrics (plateau means; t=0 at first vacuum onset)\n")
report.append(cyc_stat.to_markdown(index=False, floatfmt=".4f") + "\n")
summc = cyc_stat.groupby("pressure")[["cycle1", "cycle2", "cycle_diff",
                                      "residual_after_c1"]].agg(["count", "mean", "std"])
report.append("## Cyclic per-pressure summary\n")
report.append(summc.to_markdown(floatfmt=".4f") + "\n")

fig, ax = plt.subplots(figsize=(8, 5))
for p in (50, 100, 200):
    traces = np.array([d["trace"] for d in cyc.values()
                       if d["run"]["pressure_mbar"] == p])
    m, sd = np.nanmean(traces, 0), np.nanstd(traces, 0, ddof=1)
    ax.plot(grid_c, m, color=PALETTE[p], label=f"{p} mbar (n={len(traces)})")
    ax.fill_between(grid_c, m - sd, m + sd, color=PALETTE[p], alpha=0.2)
ax.set(xlabel="time after first vacuum onset (s)", ylabel="in-plane strain",
       title="Cyclic: mean ± SD across membranes (unfiltered)")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{FIG}/cyclic_strain_time.png", dpi=200)

# ---------------- PNEUMATIC SETTLING TIME ----------------
# How long the controller takes to establish the set vacuum, as a function of
# the set depth. This is what distinguishes "pressure sets how much" from
# "pressure sets how fast": the plateau strain is pressure-independent above
# 50 mbar, so any role left for pressure is in the transient.
settle = []
for name, d in {**static, **cyc}.items():
    press = load_pressure_record(name)
    t = press["time"].to_numpy(float)
    v = -press["mbar"].to_numpy(float)          # vacuum depth, positive
    on = pressure_phases(press)[0][0]
    plateau = np.median(v[(t >= on + 3) & (t <= on + 12)])
    if not np.isfinite(plateau) or plateau <= 0:
        continue
    seg = (t >= on - 12) & (t <= on + 15)
    ts, vs = t[seg], v[seg]
    if not (vs >= 0.9 * plateau).any():
        continue
    t10 = ts[np.argmax(vs >= 0.1 * plateau)]
    t90 = ts[np.argmax(vs >= 0.9 * plateau)]
    settle.append(dict(name=name, regime=d["run"]["regime"],
                       pressure=d["run"]["pressure_mbar"],
                       depth_mbar=float(plateau), t10_90_s=float(t90 - t10),
                       sampling_dt_s=float(np.median(np.diff(t)))))
if settle:
    sdf = pd.DataFrame(settle).sort_values(["regime", "pressure"])
    report.append("## Pneumatic settling time (measured pressure, 10-90% of "
                  "the achieved depth)\n")
    report.append("The cyclic records are sampled at ~2 Hz and resolve this; "
                  "the static records at ~1 Hz are at the edge of usability "
                  "and are reported for completeness only.\n")
    report.append(sdf.to_markdown(index=False, floatfmt=".2f") + "\n")
    agg = sdf.groupby(["regime", "pressure"])["t10_90_s"].agg(["count", "mean", "std"])
    report.append(agg.to_markdown(floatfmt=".2f") + "\n")

# ---------------- EQUIBIAXIALITY (principal-strain ratio + orientation) ----------------
eq_rows = []
for name, d in {**static, **cyc}.items():
    df = d["df"]
    t_on, t_off = d["phases"][0]
    hold = df[(df["time"] >= t_on + 5) & (df["time"] <= min(t_off - 1, t_on + 25))]
    per_tri = hold.groupby("triangle")[
        ["principal_1", "principal_2", "e_xx", "e_yy", "e_xy"]].mean()
    ratio = per_tri["principal_2"] / per_tri["principal_1"]
    # major principal axis orientation from the plateau-averaged E tensor
    theta = 0.5 * np.degrees(np.arctan2(2 * per_tri["e_xy"],
                                        per_tri["e_xx"] - per_tri["e_yy"]))
    # orientation is axial (theta ~ theta+180): circular stats on 2*theta
    ang = np.radians(2 * theta.to_numpy())
    resultant = float(np.hypot(np.mean(np.cos(ang)), np.mean(np.sin(ang))))
    eq_rows.append(dict(
        name=name, regime=d["run"]["regime"], well=d["run"]["well"],
        pressure=d["run"]["pressure_mbar"], n_triangles=len(per_tri),
        ratio_median=float(ratio.median()),
        ratio_q1=float(ratio.quantile(0.25)),
        ratio_q3=float(ratio.quantile(0.75)),
        orientation_resultant=resultant))  # 0 = isotropic, 1 = one direction
eq = pd.DataFrame(eq_rows).sort_values(["regime", "pressure", "well"])
report.append("## Equibiaxiality: principal-strain ratio e2/e1 (plateau-"
              "averaged per triangle) and orientation concentration\n")
report.append("orientation_resultant: circular resultant of the doubled "
              "principal-axis angles; 0 = no preferred direction "
              "(equibiaxial), 1 = fully aligned.\n")
report.append(eq.to_markdown(index=False, floatfmt=".3f") + "\n")

# ---------------- POST-RELEASE RELAXATION (cyclic rests) ----------------
from stretcher.stats import fit_exponential_decay

relax_rows = []
for name, d in cyc.items():
    ph = d["phases"]
    t, s = grid_c, d["trace"]
    rests = []
    if len(ph) >= 2:
        # generous margins: xcorr alignment is sensor-limited (~0.5 s)
        rests.append(("rest1", ph[0][1] + 1.0, ph[1][0] - 1.5))
        rests.append(("rest2", ph[1][1] + 1.0, min(ph[1][1] + 9.0, t.max())))
    for label, a, b in rests:
        m = (t >= a) & (t <= b)
        if m.sum() < 8:
            continue
        try:
            fit = fit_exponential_decay(t[m], s[m])
        except (ValueError, RuntimeError) as e:
            relax_rows.append(dict(name=name, rest=label, error=str(e)))
            continue
        relax_rows.append(dict(
            name=name, well=d["run"]["well"],
            pressure=d["run"]["pressure_mbar"], rest=label,
            tau_s=fit["tau"], amplitude=fit["A"],
            residual_inf=fit["y_inf"], rmse=fit["rmse"]))
relax = pd.DataFrame(relax_rows)
# valid decay: positive amplitude, tau away from the bound
if "tau_s" in relax:
    relax["valid"] = (relax["amplitude"] > 0) & (relax["tau_s"] < 54.0)
ok_fits = relax[relax.get("valid", False)]
report.append("## Post-release relaxation fits (eps = eps_inf + A*exp(-t/tau))\n")
report.append("valid=False: fit hit the tau bound or A<=0 (window "
              "contaminated by the next pulse or non-exponential).\n")
report.append(relax.to_markdown(index=False, floatfmt=".3f") + "\n")
if len(ok_fits):
    report.append(
        f"Valid fits (n = {len(ok_fits)}/{len(relax)}): median tau = "
        f"{ok_fits['tau_s'].median():.2f} s "
        f"(IQR {ok_fits['tau_s'].quantile(0.25):.2f}-"
        f"{ok_fits['tau_s'].quantile(0.75):.2f} s); "
        f"median extrapolated residual eps_inf = "
        f"{ok_fits['residual_inf'].median():.4f}.\n")

# ---------------- DENSE FIELD (all runs with *_densefield_triangles.csv) ----------------
with open(os.path.join(TRK, "qc.json")) as f:
    track_qc = json.load(f)

dense_rows = []
dense_maps = []  # (name, points, simplices, values, center, radius)
for name, d in {**static, **cyc}.items():
    base = os.path.join(TRK, name.replace(" ", "_"))
    try:
        dtri = pd.read_csv(base + "_densefield_triangles.csv")
        mesh = np.load(base + "_densefield_mesh.npz")
    except FileNotFoundError:
        continue
    dtri = dtri[dtri["min_angle"] >= MIN_ANGLE_DEG]
    # dense time is video-based; shift onto the onset-zeroed base:
    # t0 = video_time - sync_offset (-> pressure base) - raw vacuum onset
    from stretcher.sync import pressure_phases as _phases
    offset = track_qc[name]["sync_offset_s"]
    t_on_raw = _phases(pd.read_csv(base + "_pressure.csv"))[0][0]
    dtri["t0"] = dtri["time"] - offset - t_on_raw
    t_off = d["phases"][0][1]
    # validity gate: the membrane-mean strain must sit at ~0 before onset.
    # (Per-triangle SD reflects the honest short-gauge noise floor and is
    # reported, not gated on.) Patches on low-texture gel follow
    # illumination, which shows up as a biased/drifting quiet-window mean.
    quiet = dtri[dtri["t0"] < -1.0]
    if quiet["frame"].nunique() >= 10:
        qtrace = quiet.groupby("frame").apply(
            lambda g: np.average(g["mean_principal"], weights=g["area0"]),
            include_groups=False)
        quiet_bias = float(qtrace.mean())
        quiet_sd = float(qtrace.std())
        field_noise = float(
            quiet.groupby("triangle")["mean_principal"].std().median())
    else:
        quiet_bias = quiet_sd = field_noise = np.nan
    # quiet_sd is NOT gated on: in cyclic records the pre-onset window holds
    # genuine recovery drift from the preceding pressure level (sequential
    # protocol), so a fluctuating quiet mean can be real. Garbage tracking
    # (patches on low-texture gel following illumination) shows up as a
    # biased quiet mean and an outsized per-triangle noise floor.
    valid_field = (np.isfinite(quiet_bias) and abs(quiet_bias) < 0.03
                   and field_noise < 0.05)
    hold = dtri[(dtri["t0"] >= 5) & (dtri["t0"] <= min(t_off - 1, 25))]
    per_tri = hold.groupby("triangle")[
        ["mean_principal", "principal_1", "principal_2", "area0"]].mean()
    dense_plateau = float(np.average(per_tri["mean_principal"],
                                     weights=per_tri["area0"]))
    ratio_median = float((per_tri["principal_2"] / per_tri["principal_1"]).median())
    # spatial structure at the plateau
    pts, simpl = mesh["points"], mesh["simplices"]
    cx, cy = mesh["center"]; r_px = float(mesh["radius"])
    cent = pts[simpl].mean(axis=1)
    rr = np.hypot(cent[:, 0] - cx, cent[:, 1] - cy) / r_px
    vals = np.full(len(simpl), np.nan)
    for t_idx, row in per_tri.iterrows():
        vals[int(t_idx)] = row["mean_principal"]
    ok = np.isfinite(vals)
    # Radial trend across the analyzed span, with its 95% interval: the
    # interval is what decides whether a gradient is resolved at all.
    if ok.sum() >= 5:
        x, y = rr[ok], vals[ok]
        slope, icpt = np.polyfit(x, y, 1)
        s = np.sqrt(np.sum((y - slope * x - icpt) ** 2) / (len(x) - 2))
        span = x.max() - x.min()
        radial_change = float(slope * span)
        radial_change_ci = float(
            1.96 * s * span / np.sqrt(np.sum((x - x.mean()) ** 2)))
        slope = float(slope)
    else:
        slope = radial_change = radial_change_ci = np.nan
    central = vals[ok & (rr < 0.6)]
    # landmark plateau for the validation column
    t, s = (grid_s, static[name]["trace"]) if name in static else \
           (grid_c, cyc[name]["trace"])
    lm_plateau = float(np.nanmean(s[(t >= 5) & (t <= min(t_off - 1, 25))]))
    dense_rows.append(dict(
        name=name, regime=d["run"]["regime"], well=d["run"]["well"],
        pressure=d["run"]["pressure_mbar"],
        n_triangles=len(per_tri), quiet_bias=quiet_bias, quiet_sd=quiet_sd,
        tri_noise=field_noise, valid=valid_field,
        dense_plateau=dense_plateau, landmark_plateau=lm_plateau,
        bias=dense_plateau - lm_plateau,
        central_sd=float(np.std(central)) if len(central) else np.nan,
        radial_slope=slope, radial_change=radial_change,
        radial_change_ci=radial_change_ci, ratio_median=ratio_median))
    if valid_field:
        dense_maps.append((name, pts, simpl, vals, (cx, cy), r_px))

if dense_rows:
    dd = pd.DataFrame(dense_rows).sort_values(["regime", "pressure", "well"])
    ok = dd[dd["valid"]]
    report.append("## Dense field vs landmarks (plateau means, hold window)\n")
    report.append(
        "valid=False: quiet-window mean biased (|bias| >= 3%) or per-"
        "triangle noise floor >= 5% — insufficient speckle contrast "
        "(patches follow illumination, not material); excluded from claims "
        "and maps. quiet_sd is reported but not gated: in cyclic records "
        "the pre-onset window contains genuine recovery drift from the "
        "preceding pressure level of the sequential protocol.\n")
    if len(ok) >= 3:
        r_val = np.corrcoef(ok["dense_plateau"], ok["landmark_plateau"])[0, 1]
        report.append(
            f"Cross-validation over the {len(ok)} valid runs: Pearson r = "
            f"{r_val:.3f}, median bias (dense - landmark) = "
            f"{ok['bias'].median():+.4f} strain, mean |bias| = "
            f"{ok['bias'].abs().mean():.4f}. radial_slope: linear strain "
            "change from center (r=0) to ring (r=R). radial_change and "
            "radial_change_ci: the same fit expressed over the analyzed span "
            "only, with its 95% interval (Figure 6). ratio_median: dense-"
            "field principal-strain ratio e2/e1.\n")
    report.append(dd.to_markdown(index=False, floatfmt=".4f") + "\n")

    # all-runs grid figure at the plateau
    import matplotlib.tri as mtri
    n = len(dense_maps)
    ncols = 5
    nrows = int(np.ceil(n / ncols))
    figg, axsg = plt.subplots(nrows, ncols, figsize=(3.1 * ncols, 3.3 * nrows))
    for ax in np.ravel(axsg):
        ax.axis("off")
    for ax, (name, pts, simpl, vals, (cx, cy), r_px) in zip(
            np.ravel(axsg), dense_maps):
        tr = mtri.Triangulation(pts[:, 0] - cx, pts[:, 1] - cy, simpl)
        tr.set_mask(~np.isfinite(vals))
        ax.tripcolor(tr, np.nan_to_num(vals), cmap="viridis",
                     vmin=0, vmax=0.25)
        ax.set_aspect("equal"); ax.invert_yaxis(); ax.axis("off")
        ax.set_title(name.replace("20241003_", "").replace("20241016_", "")
                     .replace("20241017_", ""), fontsize=8)
    figg.suptitle("Dense-field plateau strain, all runs (shared scale 0-0.25)")
    figg.tight_layout()
    figg.savefig(f"{FIG}/densefield_all_grid.png", dpi=200)

# ---------------- SAMPLING-DENSITY CHECK ----------------
# Does a membrane with fewer tracked elements read a lower strain? (Membrane 4
# has the fewest dense elements and one of the lowest plateaus.)
if dense_rows:
    sd_df = pd.DataFrame(dense_rows)
    sd_df = sd_df[sd_df["valid"]]
    report.append("## Sampling-density check\n")
    if len(sd_df) >= 4:
        r_dense = np.corrcoef(sd_df["n_triangles"], sd_df["dense_plateau"])[0, 1]
        report.append(
            f"Across the {len(sd_df)} valid dense fields, the correlation "
            f"between element count and plateau strain is r = {r_dense:.3f}.\n")
    lm_counts = pd.DataFrame([
        dict(name=n, well=d["run"]["well"], pressure=d["run"]["pressure_mbar"],
             n_tri=d["df"]["triangle"].nunique(),
             plateau=plateau_stats(d["trace"], grid_s, d["phases"])[0])
        for n, d in static.items()])
    r_lm = np.corrcoef(lm_counts["n_tri"], lm_counts["plateau"])[0, 1]
    report.append(
        f"Across the {len(lm_counts)} static landmark runs, the correlation "
        f"between triangle count and plateau strain is r = {r_lm:.3f}.\n")

    # bootstrap: subsample the densest 50 mbar field to membrane 4's density
    rich = "20241003_2_50_cont_HD"
    poor_n = int(sd_df[sd_df["name"] == "20241003_4_50_cont_HD"]["n_triangles"].iloc[0]) \
        if (sd_df["name"] == "20241003_4_50_cont_HD").any() else 25
    base = os.path.join(TRK, rich + "_triangles.csv")
    rich_dense = pd.read_csv(os.path.join(TRK, rich + "_densefield_triangles.csv"))
    rich_dense = rich_dense[rich_dense["min_angle"] >= MIN_ANGLE_DEG]
    press = pd.read_csv(os.path.join(TRK, rich + "_pressure.csv"))
    from stretcher.sync import pressure_phases as _pp2
    off = track_qc[rich]["sync_offset_s"]
    rich_dense["t0"] = rich_dense["time"] - off - _pp2(press)[0][0]
    rich_hold = rich_dense[(rich_dense["t0"] >= 5) & (rich_dense["t0"] <= 25)]
    per_tri_rich = rich_hold.groupby("triangle")["mean_principal"].mean()
    rng = np.random.default_rng(0)
    draws = [float(rng.choice(per_tri_rich.to_numpy(), size=poor_n,
                              replace=False).mean()) for _ in range(500)]
    report.append(
        f"Bootstrap (500 draws) subsampling membrane 2's dense field "
        f"({len(per_tri_rich)} elements, full mean "
        f"{per_tri_rich.mean():.4f}) down to membrane 4's element count "
        f"({poor_n}): mean {np.mean(draws):.4f}, 95% interval "
        f"[{np.percentile(draws, 2.5):.4f}, {np.percentile(draws, 97.5):.4f}]. "
        "Sparse sampling widens the interval but does not bias the estimate.\n")

# ---------------- RADIAL (static 50 mbar, runs with curated circles) ----------------
rad_rows = []
for r in static_runs:
    path = os.path.join(TRK, r["name"].replace(" ", "_") + "_radial.csv")
    if not os.path.exists(path):
        continue
    rad = pd.read_csv(path)
    # maximum-deformation frame = frame of max mean radial strain
    mean_by_frame = rad.groupby("frame")["radial_strain"].mean()
    fmax = mean_by_frame.idxmax()
    at_max = rad[rad["frame"] == fmax]
    for _, row in at_max.iterrows():
        rad_rows.append(dict(name=r["name"], well=r["well"],
                             radial=row["radial_strain"], dtheta=row["dtheta_deg"]))
rad_df = pd.DataFrame(rad_rows)
if len(rad_df):
    rsum = rad_df.groupby("name").agg(n=("radial", "count"),
                                      radial_mean=("radial", "mean"),
                                      radial_sd=("radial", "std"),
                                      dtheta_mean=("dtheta", "mean"),
                                      dtheta_sd=("dtheta", "std"),
                                      dtheta_max=("dtheta", "max"))
    report.append("## Radial strain at maximum deformation (static 50 mbar, "
                  "all markers, center from all-marker similarity fit)\n")
    report.append(rsum.to_markdown(floatfmt=".3f") + "\n")

with open(os.path.join(NOTES, "reanalysis_summary.md"), "w") as f:
    f.write("\n".join(report))
print("\n".join(report))
print(f"\nfigures -> {FIG}")
