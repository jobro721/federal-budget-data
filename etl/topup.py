#!/usr/bin/env python3
"""Top-up pass: re-fetch any USAspending payload that is empty (or a whole
fiscal year that is missing) from ../data/raw, then stop.

The public API load-sheds under burst traffic — the main pull (pull_usaspending.py)
records exactly what succeeded in ../data/pull_log.md; this script is the
recovery path. Safe to re-run at any time: it only fills gaps, never overwrites
good data.

Usage:  python3 topup.py            (one pass, ~15s between attempts, 4 max)
"""
import json
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = "https://api.usaspending.gov/api/v2"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
LOG = Path(__file__).resolve().parent.parent / "data" / "pull_log.md"

AGENCY_CODES = ["036", "020", "012"]
FISCAL_YEARS = ["2023", "2024", "2025"]


def get(url: str, params: dict | None = None, tries: int = 4, wait: float = 15.0) -> dict | None:
    for a in range(tries):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                with LOG.open("a") as f:
                    f.write(f"- {datetime.now():%Y-%m-%d %H:%M} TOPUP GET {url} -> 200\n")
                return r.json()
        except requests.exceptions.RequestException:
            pass
        print(f"  attempt {a+1}/{tries} failed for {url} — waiting {wait}s")
        time.sleep(wait)
    return None


def main() -> None:
    fixed = 0
    # agency budgetary resources
    br_path = RAW / "budgetary_resources.json"
    br = json.loads(br_path.read_text()) if br_path.exists() else {}
    for code in AGENCY_CODES:
        if not br.get(code, {}).get("agency_data_by_year"):
            print(f"top-up agency {code} budgetary_resources")
            d = get(f"{BASE}/agency/{code}/budgetary_resources/", {"fiscal_year": FISCAL_YEARS[0]})
            if d:
                br[code] = d
                fixed += 1
        time.sleep(10)
    br_path.write_text(json.dumps(br))

    # gov-wide totals
    tb_path = RAW / "total_budgetary_resources.json"
    tb = json.loads(tb_path.read_text()) if tb_path.exists() else {}
    for fy in FISCAL_YEARS:
        if not tb.get(fy, {}).get("results"):
            print(f"top-up gov-wide total_budgetary_resources {fy}")
            d = get(f"{BASE}/references/total_budgetary_resources/", {"fiscal_year": fy})
            if d:
                tb[fy] = d
                fixed += 1
        time.sleep(10)
    tb_path.write_text(json.dumps(tb))

    # TAS list
    fa_path = RAW / "federal_accounts_036.json"
    fa = json.loads(fa_path.read_text()) if fa_path.exists() else {}
    if not fa.get("results"):
        print("top-up federal accounts 036")
        d = get(f"{BASE}/agency/036/federal_account/", {"fiscal_year": "2024", "limit": 100})
        if d:
            fa = d
            fa_path.write_text(json.dumps(d))
            fixed += 1

    print(f"top-up complete: {fixed} payload(s) recovered")


if __name__ == "__main__":
    main()
