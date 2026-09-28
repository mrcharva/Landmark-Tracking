import numpy as np
import pytest

from stretcher.stats import fit_exponential_decay


def test_recovers_known_tau():
    rng = np.random.default_rng(1)
    t = np.arange(0, 8, 1 / 30)
    y = 0.03 + 0.09 * np.exp(-t / 2.5) + rng.normal(0, 0.004, t.size)
    fit = fit_exponential_decay(t, y)
    assert fit["tau"] == pytest.approx(2.5, rel=0.15)
    assert fit["y_inf"] == pytest.approx(0.03, abs=0.01)
    assert fit["A"] == pytest.approx(0.09, abs=0.02)


def test_refuses_too_few_samples():
    with pytest.raises(ValueError):
        fit_exponential_decay([0, 1, 2], [1, 0.5, 0.2])
