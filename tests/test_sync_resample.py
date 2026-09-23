import numpy as np
import pandas as pd
import pytest

from stretcher.resample import mean_then_resample, to_common_grid
from stretcher.sync import align, pressure_onset, strain_onset


def test_pressure_onset_uses_main_step_not_preplateau():
    # -10 mbar pre-plateau (like the real sensors) then the -50 step;
    # half-depth threshold (-25) must anchor on the main step
    p = pd.DataFrame({"time": [0.0, 1.0, 2.0, 3.0, 4.0],
                      "mbar": [0.0, 0.0, -10.0, -50.0, -50.0]})
    assert pressure_onset(p) == pytest.approx(2.375)


def test_pressure_onset_ignores_single_sample_glitch():
    p = pd.DataFrame({"time": np.arange(7.0),
                      "mbar": [0, -30, 0, 0, -10, -50, -50]})
    assert pressure_onset(p) > 3.0


def test_strain_onset_and_align():
    t = np.linspace(0, 30, 901)
    strain = 0.10 * np.clip((t - 4.0) / 2.0, 0, 1)  # ramp 4->6 s
    onset = strain_onset(t, strain)  # 50% of plateau -> 5.0 s
    assert onset == pytest.approx(5.0, abs=0.05)

    p = pd.DataFrame({"time": [0.0, 0.9, 1.0, 2.0, 30.0],
                      "mbar": [0.0, 0.0, -50.0, -50.0, -50.0]})
    df = pd.DataFrame({"time": t, "strain": strain})
    shifted, off = align(df, p)
    # pressure onset 0.95 s, strain onset 5.0 s -> shift ~4.05 s
    assert off == pytest.approx(4.05, abs=0.1)
    assert shifted["time"].iloc[0] == pytest.approx(-off)


def test_resample_refuses_non_monotonic():
    t = np.concatenate([np.linspace(0, 30, 50)] * 3)  # concatenated triangles
    v = np.random.default_rng(0).normal(size=t.size)
    with pytest.raises(ValueError, match="not monotonic"):
        to_common_grid(t, v, np.linspace(0, 30, 100))


def test_mean_then_resample_averages_replicates():
    df = pd.DataFrame({"time": [0.0, 0.0, 1.0, 1.0],
                       "strain": [0.0, 0.2, 0.4, 0.6]})
    out = mean_then_resample(df, np.array([0.0, 0.5, 1.0]))
    assert np.allclose(out, [0.1, 0.3, 0.5])


def test_resample_nan_outside_record():
    out = to_common_grid([1.0, 2.0], [5.0, 6.0], np.array([0.0, 1.5, 3.0]))
    assert np.isnan(out[0]) and out[1] == 5.5 and np.isnan(out[2])


def test_xcorr_offset_recovers_known_shift():
    from stretcher.sync import xcorr_offset
    # pressure: square pulses at 7.5-22.5 s and 37.5-52.5 s (record 0-60 s)
    tp = np.arange(0, 60, 0.2)
    p = np.where(((tp >= 7.5) & (tp < 22.5)) | ((tp >= 37.5) & (tp < 52.5)),
                 -100.0, 0.0)
    press = pd.DataFrame({"time": tp, "mbar": p})
    # strain: same waveform but the video started 3.7 s after the sensor
    ts = np.arange(0, 55, 1 / 30)
    t_abs = ts + 3.7
    s = np.where(((t_abs >= 7.5) & (t_abs < 22.5)) |
                 ((t_abs >= 37.5) & (t_abs < 52.5)), 0.11, 0.0)
    off, r = xcorr_offset(ts, s, press)
    # precision is limited by the pressure record's sampling (0.2 s here)
    assert off == pytest.approx(-3.7, abs=0.25)
    assert r > 0.95
