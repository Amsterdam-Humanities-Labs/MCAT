"""Phase 4 verification: the full async batch pipeline end-to-end —
BatchProcessor.process_csv_async (run via asyncio.run, as the worker thread
does) over the FB verified fixture, checking ProcessingResult + the written
results.csv.

  backend/venv/bin/python tests/experiments/zd_phase4_verify.py
"""
import asyncio
import csv
import sys
import tempfile
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.batch_processor import BatchProcessor  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "fixtures/live/verified/facebook_verified_urls.csv"


def main():
    bp = BatchProcessor()
    out = tempfile.mkdtemp(prefix="mcat_p4_")
    result = asyncio.run(bp.process_csv_async(
        csv_path=str(DATA), platform="facebook",
        column_mapping={'post': 'url'}, output_folder=out,
        save_screenshots=False, cookies=None, auth_user="anonymous",
    ))

    print("success      :", result.success)
    print("processed    :", result.processed_count)
    print("stats        :", dict(result.stats))

    rows = list(csv.DictReader((Path(out) / "results.csv").open()))
    expected = {r["url"]: r["status"] for r in csv.DictReader(DATA.open())}
    correct = sum(1 for r in rows if r.get("mcat_status") == expected.get(r["url"]))
    has_cols = rows and all(c in rows[0] for c in ("mcat_status", "mcat_user", "mcat_timestamp"))
    print(f"output rows  : {len(rows)} (mcat_ cols: {'PASS' if has_cols else 'FAIL'})")
    print(f"parity       : {correct}/{len(rows)}")
    print("RESULT       :", "PASS" if (result.success and correct == len(rows) == 5) else "FAIL")


if __name__ == "__main__":
    main()
