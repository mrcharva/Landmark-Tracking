"""Offline checks for the Zenodo fetcher: no network, a fake record."""

import hashlib

import pytest

from stretcher import data


def _run(regime, well, p, video, csv):
    return {"regime": regime, "well": well, "pressure_mbar": p,
            "video": video, "pressure_csv": csv}


def _entry(key, payload=b""):
    return {"key": key, "checksum": "md5:" + hashlib.md5(payload).hexdigest(),
            "links": {"self": f"https://example.invalid/{key}"}}


def test_record_id_from_doi():
    assert data.record_id("10.5281/zenodo.14856233") == "14856233"
    assert data.record_id("https://doi.org/10.5281/zenodo.14856233 ") == "14856233"
    with pytest.raises(ValueError):
        data.record_id("10.1000/not-zenodo")


def test_deposit_name_follows_regime_well_pressure():
    run = _run("cyclic", 3, 100, "v", "c")
    assert data.deposit_name(run, "video") == "cyclic_3_100 mbar.mp4"
    assert data.deposit_name(run, "pressure_csv") == "cyclic_3_100 mbar.csv"


def test_plan_maps_each_registry_path_to_its_deposit_file():
    runs = [_run("static", 2, 50, "/s/a.mp4", "/s/a.csv")]
    rec = {"files": [_entry("static_2_50 mbar.mp4"), _entry("static_2_50 mbar.csv")]}
    todo = data.plan(rec, runs)
    assert [(e["key"], d) for e, d in todo] == [
        ("static_2_50 mbar.mp4", "/s/a.mp4"), ("static_2_50 mbar.csv", "/s/a.csv")]


def test_plan_names_every_missing_file_instead_of_downloading_a_partial_set():
    runs = [_run("static", 2, 50, "a", "b"), _run("static", 4, 200, "c", "d")]
    rec = {"files": [_entry("static_2_50 mbar.mp4"), _entry("static_2_50 mbar.csv")]}
    with pytest.raises(LookupError) as e:
        data.plan(rec, runs)
    assert "static_4_200 mbar.mp4" in str(e.value) and "static_4_200 mbar.csv" in str(e.value)


def test_fetch_skips_a_file_already_in_place(tmp_path):
    dest = tmp_path / "a.csv"
    dest.write_bytes(b"tracked bytes")
    todo = [(_entry("static_2_50 mbar.csv", b"tracked bytes"), str(dest))]
    assert list(data.fetch(todo)) == [(str(dest), "present")]
