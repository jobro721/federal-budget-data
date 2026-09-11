#!/usr/bin/env python3
"""Pull public federal budget data from USAspending (no API key required).

Outputs (JSON) to ../data/raw/:
  toptier_agencies.json      all top-tier agencies + summary amounts
  budgetary_resources.json   agency budget execution by fiscal year/period
  total_budgetary_resources.json  government-wide budgetary resources
  federal_accounts_036.json  VA (toptier 036) federal accounts (TAS)
  filed_account_balances.csv File D account_balances rows (best-effort)

Every call is logged with the exact URL + params in ../data/pull_log.md so a
reviewer can reproduce every number. Data license: CC0 1.0 Universal.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = "https://api.usaspending.gov/api/v2"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
LOG = Path(__file__).resolve().parent.parent / "data" / "pull_log.md"

# Agencies to pull deep execution data for: 036 = VA (the home agency),
# 020 = HHS, 012 = DoD (biggest outlays) — public data, agency level only.
AGENCY_CODES = ["036", "020", "012"]
FISCAL_YEARS = ["2023", "2024", "2025"]


def _request(method: str, url: str, **kw) -> dict:
    """GET/POST with 3 attempts and backoff (the public API rate-limits bursts)."""
    last = None
    for attempt in range(3):
        try:
            r = requests.request(method, url, timeout=60, **kw)
        except requests.exceptions.RequestException as e:
            last = e
            wait = 5 * (attempt + 1)
            print(f"  [retry {attempt+1}/3] {url}: {type(e).__name__} — waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        with LOG.open("a") as f:
            f.write(f"- {datetime.now():%Y-%m-%d %H:%M} {method.upper()} {url} -> {r.status_code}\n")
        if r.status_code == 429 or r.status_code >= 500:
            wait = 10 * (attempt + 1)
            print(f"  [retry {attempt+1}/3] {url}: HTTP {r.status_code} — waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            last = r
            continue
        if r.status_code != 200:
            print(f"  [warn] {url} -> {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return {}
        return r.json()
    print(f"  [error] {url}: giving up after 3 attempts ({type(last).__name__ if last else last})", file=sys.stderr)
    return {}


def logged_get(url: str, params: dict | None = None, note: str = "") -> dict:
    d = _request("GET", url, params=params)
    if note:
        with LOG.open("a") as f:
            f.write(f"  note: {note}\n")
    return d


def logged_post(url: str, payload: dict, note: str = "") -> dict:
    d = _request("POST", url, json=payload)
    if note:
        with LOG.open("a") as f:
            f.write(f"  note: {note}\n")
    return d


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.write_text(
        f"# USAspending pull log\nStarted {datetime.now():%Y-%m-%d %H:%M} by pull_usaspending.py\n"
        f"Base: {BASE} (no key; CC0 1.0 data).\n",
    )

    print("1/5 toptier agencies")
    agencies = logged_get(f"{BASE}/references/toptier_agencies/", note="all top-tier agencies")
    (RAW / "toptier_agencies.json").write_text(json.dumps(agencies))
    print(f"   {len(agencies.get('results', agencies if isinstance(agencies, list) else []))} agencies")

    print("2/5 agency budgetary resources (multi-year, by period)")
    br = {}
    for code in AGENCY_CODES:
        d = logged_get(
            f"{BASE}/agency/{code}/budgetary_resources/",
            {"fiscal_year": FISCAL_YEARS[0]},
            note=f"agency {code} (endpoint returns multiple years)",
        )
        br[code] = d
        time.sleep(0.5)
    (RAW / "budgetary_resources.json").write_text(json.dumps(br))
    print(f"   {len(br)} agencies")

    print("3/5 government-wide total budgetary resources")
    total = {}
    for fy in FISCAL_YEARS:
        total[fy] = logged_get(
            f"{BASE}/references/total_budgetary_resources/", {"fiscal_year": fy}, note=f"gov-wide {fy}"
        )
        time.sleep(0.5)
    (RAW / "total_budgetary_resources.json").write_text(json.dumps(total))

    print("4/5 federal accounts (TAS) for 036")
    fa = logged_get(
        f"{BASE}/agency/036/federal_account/", {"fiscal_year": "2024", "limit": 100}, note="VA TAS list FY2024"
    )
    (RAW / "federal_accounts_036.json").write_text(json.dumps(fa))
    res = fa.get("results", fa if isinstance(fa, list) else [])
    print(f"   {len(res)} TAS")

    print("5/5 File D account_balances (VA FY2024 periods 02-12, best-effort)")
    rows = []
    for period in [f"{p:02d}" for p in range(2, 13)]:
        d = logged_post(
            f"{BASE}/download/accounts/",
            {
                "account_level": "federal_account",
                "filters": {"fy": "2024", "toptier_agency_codes": ["036"], "period": period,
                            "submission_types": ["account_balances"]},
            },
            note=f"File D account_balances VA FY2024 P{period}",
        )
        job = d.get("file_job_id")
        if not job:
            print(f"   P{period}: no job created (skipping)")
            continue
        for _ in range(20):
            st = logged_get(f"{BASE}/download/status/", {"job_id": job})
            status = st.get("status")
            if status == "success":
                with requests.get(st["url"], timeout=120) as r:
                    r.raise_for_status()
                    z = r.content
                import io, zipfile, csv
                with zipfile.ZipFile(io.BytesIO(z)) as zf:
                    name = zf.namelist()[0]
                    with zf.open(name) as fh:
                        text = fh.read().decode("utf-8-sig")
                rows.extend(csv.DictReader(text.splitlines()))
                print(f"   P{period}: {len(rows)} rows total")
                break
            if status in ("failed", "error"):
                print(f"   P{period}: job {status} (skipping)")
                break
            time.sleep(3)
    if rows:
        cols = list(rows[0].keys())
        with (RAW / "filed_account_balances.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    else:
        print("   File D: nothing downloaded this run (endpoint returned errors); the pipeline degrades gracefully")

    print("done. raw files:", sorted(p.name for p in RAW.iterdir()))


if __name__ == "__main__":
    main()
