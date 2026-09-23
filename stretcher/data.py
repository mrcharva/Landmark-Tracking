"""Fetch the recordings from their Zenodo deposit into the paths experiments.yaml uses.

The deposit names files by regime, well and pressure (``static_2_50 mbar.mp4``);
the registry names them by recording date (``share/Static/20241003_2_50_cont_HD.mp4``).
The mapping is derived from each run's regime, well and pressure, so nothing per
recording is hard-coded, and every download is checked against the MD5 that
Zenodo publishes for it.
"""

import hashlib
import json
import os
import re
import urllib.error
import urllib.request

API = "https://zenodo.org/api/records/"
DATA_DOI = "10.5281/zenodo.14856233"


def record_id(doi):
    """Numeric Zenodo record id from a DOI such as 10.5281/zenodo.14856233."""
    m = re.search(r"zenodo\.(\d+)\s*$", doi.strip())
    if not m:
        raise ValueError(f"not a Zenodo DOI: {doi!r}")
    return m.group(1)


def _open(url, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(req, timeout=120)


def get_record(doi, token=None):
    """Record metadata, including the file list and checksums.

    A deposit that is not public yet is only reachable through its draft
    endpoint with an access token, so that is tried when a token is given.
    """
    rid = record_id(doi)
    urls = [API + rid] + ([API + rid + "/draft"] if token else [])
    last = None
    for url in urls:
        try:
            with _open(url, token) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (401, 403, 404, 410):
                raise
            last = e
    hint = "" if token else " If the deposit is not public yet, set ZENODO_TOKEN."
    raise LookupError(f"{doi}: no accessible Zenodo record (HTTP {last.code}).{hint}")


def deposit_name(run, key):
    """File name of a run's video or pressure log inside the deposit."""
    ext = ".mp4" if key == "video" else ".csv"
    return f"{run['regime']}_{run['well']}_{run['pressure_mbar']} mbar{ext}"


def plan(record, runs):
    """(deposit file entry, destination path) for every file the registry needs.

    Raises LookupError naming every file the deposit lacks, rather than
    downloading a partial set that would fail later in tracking.
    """
    files = {f["key"]: f for f in record["files"]}
    todo, missing = [], []
    for run in runs:
        for key in ("video", "pressure_csv"):
            name = deposit_name(run, key)
            if name in files:
                todo.append((files[name], run[key]))
            else:
                missing.append(name)
    if missing:
        raise LookupError("not in the deposit: " + ", ".join(sorted(missing)))
    return todo


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(todo, token=None):
    """Download each planned file unless an identical copy is already in place.

    Yields (destination, status). A download is written to a .part file and
    only moved into place once its MD5 matches, so an interrupted or corrupted
    transfer never leaves a file the tracker would silently accept.
    """
    for entry, dest in todo:
        want = entry["checksum"].split(":", 1)[1]
        if os.path.exists(dest) and md5(dest) == want:
            yield dest, "present"
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        part = dest + ".part"
        with _open(entry["links"]["self"], token) as r, open(part, "wb") as out:
            for chunk in iter(lambda: r.read(1 << 20), b""):
                out.write(chunk)
        got = md5(part)
        if got != want:
            os.remove(part)
            raise IOError(f"{os.path.basename(dest)}: MD5 {got} != published {want}")
        os.replace(part, dest)
        yield dest, "downloaded"
