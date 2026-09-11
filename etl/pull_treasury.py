#!/usr/bin/env python3
"""Pull public Treasury fiscal data (no API key required).

Outputs (JSON) to ../data/raw/:
  debt_to_penny.json   daily total public debt (2015-01-01 onward, ~3.5k rows)
  mts_table_9.json     Monthly Treasury Statement receipts (last ~3 years)

Base: https://api.fiscaldata.treasury.gov/services/api/fiscal_service
(Note: the '.../fiscal/service/...' variant 404s — this base is verified.)
"""
import json
from datetime import datetime
from pathlib import Path

import requests

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
LOG = Path(__file__).resolve().parent.parent / "data" / "pull_log.md"


def get_all(path: str, params: dict, note: str) -> list:
    """Follow page[number] until the API returns fewer rows than the page size."""
    out, page, size = [], 1, 1000
    while True:
        p = {**params, "page[number]": page, "page[size]": size}
        r = requests.get(f"{BASE}/{path}", params=p, timeout=120)
        r.raise_for_status()
        with LOG.open("a") as f:
            f.write(f"- {datetime.now():%Y-%m-%d %H:%M} GET /{path} page={page} {json.dumps(params)} -> {r.status_code}\n")
            if note:
                f.write(f"  note: {note}\n")
        batch = r.json().get("data", [])
        out.extend(batch)
        if len(batch) < size:
            return out
        page += 1


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.write_text(
        f"# Treasury pull log\nStarted {datetime.now():%Y-%m-%d %H:%M} by pull_treasury.py\n"
        f"Base: {BASE} (no key).\n",
    )

    print("1/2 debt_to_penny (daily, 2015-01-01 onward)")
    debt = get_all(
        "v2/accounting/od/debt_to_penny",
        {"filter": "record_date:gte:2015-01-01", "sort": "record_date"},
        "daily total public debt",
    )
    (RAW / "debt_to_penny.json").write_text(json.dumps(debt))
    print(f"   {len(debt)} rows; latest: {debt[-1]['record_date']} tot_pub_debt_out_amt={debt[-1]['tot_pub_debt_out_amt']}")

    print("2/2 MTS table 9 (receipts, 2023-07 onward)")
    mts = get_all(
        "v1/accounting/mts/mts_table_9",
        {"filter": "record_date:gte:2023-07-01", "sort": "-record_date"},
        "MTS receipts by source (monthly)",
    )
    (RAW / "mts_table_9.json").write_text(json.dumps(mts))
    print(f"   {len(mts)} rows")

    print("done")


if __name__ == "__main__":
    main()
