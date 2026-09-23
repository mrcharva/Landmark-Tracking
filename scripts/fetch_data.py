"""Download the recordings from Zenodo into share/, where experiments.yaml expects them.

An access token for a deposit that is not public yet is read from the
ZENODO_TOKEN environment variable, never from the command line, so it does not
end up in shell history.

Run: .venv/bin/python scripts/fetch_data.py [--doi DOI] [--regime static|cyclic]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stretcher import load_registry
from stretcher.data import DATA_DOI, fetch, get_record, plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", default=DATA_DOI)
    ap.add_argument("--regime", choices=["static", "cyclic"])
    args = ap.parse_args()

    token = os.environ.get("ZENODO_TOKEN")
    # excluded runs too: QC and diagnostics need them, and they are in the deposit
    _, runs = load_registry(regime=args.regime, include_excluded=True)
    todo = plan(get_record(args.doi, token), runs)
    counts = {}
    for dest, status in fetch(todo, token):
        counts[status] = counts.get(status, 0) + 1
        print(f"  {status:<10} {os.path.relpath(dest)}", flush=True)
    print(", ".join(f"{n} {s}" for s, n in counts.items()) + f" -> {args.doi}")


if __name__ == "__main__":
    main()
