#!/usr/bin/env python3
"""Pull FRED series via the KEYLESS CSV endpoint (no account needed).

  https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>

Outputs (CSV) to ../data/raw/fred_<SERIES>.csv

Series (all verified live 2026-09-11):
  FGEXPND  federal outlays, monthly ($B, SA)
  M2SL     M2 money stock, monthly ($B)
  GS10     10-year Treasury yield (%)
  DFF      federal funds effective rate, daily (%)  [replaces retired FEDFUNS]
  T10Y3M   10Y-3M spread (%)
  UNRATE   unemployment rate (%)
  CPIAUCSL CPI-U, monthly index

Note: FEDFUNS, GFED01, GFED02 are RETIRED (404) — do not re-add them.
Use Treasury MTS (pull_treasury.py) for receipts/outlays detail.
"""
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
SERIES = ["FGEXPND", "M2SL", "GS10", "DFF", "T10Y3M", "UNRATE", "CPIAUCSL"]
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for sid in SERIES:
        r = requests.get(URL.format(sid=sid), timeout=60)
        r.raise_for_status()
        text = r.text
        if "<html" in text[:200].lower() or not text.strip().startswith(("observation_date", "DATE", "date")):
            print(f"   {sid}: UNEXPECTED RESPONSE (series retired or endpoint change?) — first 120 chars: {text[:120]!r}")
            continue
        (RAW / f"fred_{sid}.csv").write_text(text)
        first = text.splitlines()[0]
        last = text.strip().splitlines()[-1]
        print(f"   {sid}: {first}  ...  {last}")
    print("done")


if __name__ == "__main__":
    main()
