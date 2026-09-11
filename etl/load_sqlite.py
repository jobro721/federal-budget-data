#!/usr/bin/env python3
"""Load ../data/raw/*.{json,csv} into ../data/budget.db (SQLite).

Schema is documented in README (data/README.md). Idempotent: DELETE + INSERT
per table (the datasets are small enough; the ETL is re-runnable).

Tables:
  toptier_agencies(code PK, name, abbreviation, agency_id, active_fy,
                   outlay_amount, obligated_amount, budget_authority_amount)
  agency_budgetary_resources(code, fiscal_year, agency_budgetary_resources,
                             agency_total_obligated, agency_total_outlayed,
                             total_budgetary_resources, PRIMARY KEY(code, fiscal_year))
  agency_obligation_by_period(code, fiscal_year, period, obligated,
                             PRIMARY KEY(code, fiscal_year, period))
  gov_budgetary_resources(fiscal_year, fiscal_period, total_budgetary_resources,
                          PRIMARY KEY(fiscal_year, fiscal_period))
  va_federal_accounts(code PK, name, obligated_amount, gross_outlay_amount)
  debt_to_penny(record_date PK, tot_pub_debt_out_amt, debt_held_public_amt, intragov_hold_amt)
  mts_receipts(rowid PK auto, record_date, classification_id, classification_desc,
               current_month_amt, fytd_amt, prior_fytd_amt, line_code_nbr)
  file_d(code, object_class, period, obligated, outlay, uob)  -- if File D downloaded
  fred_<SID>(date PK, value)   -- one table per series
"""
import csv
import json
import re
from pathlib import Path

import sqlite3

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "budget.db"


def num(x):
    if x in (None, "", "null", "None"):
        return None
    try:
        f = float(x)
        return int(f) if f == int(f) and abs(f) < 1e15 else f
    except (TypeError, ValueError):
        return None


def main() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    c = con.cursor()
    c.executescript(
        """
        CREATE TABLE toptier_agencies(code TEXT PRIMARY KEY, name TEXT, abbreviation TEXT,
            agency_id INTEGER, active_fy TEXT, outlay_amount REAL, obligated_amount REAL,
            budget_authority_amount REAL);
        CREATE TABLE agency_budgetary_resources(code TEXT, fiscal_year INTEGER,
            agency_budgetary_resources REAL, agency_total_obligated REAL,
            agency_total_outlayed REAL, total_budgetary_resources REAL,
            PRIMARY KEY(code, fiscal_year));
        CREATE TABLE agency_obligation_by_period(code TEXT, fiscal_year INTEGER, period INTEGER,
            obligated REAL, PRIMARY KEY(code, fiscal_year, period));
        CREATE TABLE gov_budgetary_resources(fiscal_year INTEGER, fiscal_period INTEGER,
            total_budgetary_resources REAL, PRIMARY KEY(fiscal_year, fiscal_period));
        CREATE TABLE va_federal_accounts(code TEXT PRIMARY KEY, name TEXT,
            obligated_amount REAL, gross_outlay_amount REAL);
        CREATE TABLE debt_to_penny(record_date TEXT PRIMARY KEY, tot_pub_debt_out_amt REAL,
            debt_held_public_amt REAL, intragov_hold_amt REAL);
        CREATE TABLE mts_receipts(id INTEGER PRIMARY KEY AUTOINCREMENT, record_date TEXT,
            classification_id TEXT, classification_desc TEXT, current_month_amt REAL,
            fytd_amt REAL, prior_fytd_amt REAL, line_code_nbr TEXT);
        CREATE TABLE file_d(code TEXT, object_class TEXT, period INTEGER, obligated REAL,
            outlay REAL, uob REAL);
        """
    )

    # 1. toptier agencies
    d = json.loads((RAW / "toptier_agencies.json").read_text())
    res = d.get("results", d if isinstance(d, list) else [])
    c.executemany(
        "INSERT INTO toptier_agencies VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                r.get("toptier_code"), r.get("agency_name"), r.get("abbreviation"),
                r.get("agency_id"), str(r.get("active_fy")), num(r.get("outlay_amount")),
                num(r.get("obligated_amount")), num(r.get("budget_authority_amount")),
            )
            for r in res
        ],
    )
    print(f"toptier_agencies: {len(res)}")

    # 2. agency budgetary resources + by-period
    d = json.loads((RAW / "budgetary_resources.json").read_text())
    n = np = 0
    for code, payload in d.items():
        for y in payload.get("agency_data_by_year", []):
            c.execute(
                "INSERT OR REPLACE INTO agency_budgetary_resources VALUES (?,?,?,?,?,?)",
                (
                    code, y.get("fiscal_year"), num(y.get("agency_budgetary_resources")),
                    num(y.get("agency_total_obligated")), num(y.get("agency_total_outlayed")),
                    num(y.get("total_budgetary_resources")),
                ),
            )
            n += 1
            for p in y.get("agency_obligation_by_period", []):
                c.execute(
                    "INSERT OR REPLACE INTO agency_obligation_by_period VALUES (?,?,?,?)",
                    (code, y.get("fiscal_year"), p.get("period"), num(p.get("obligated"))),
                )
                np += 1
    print(f"agency_budgetary_resources: {n} rows; by_period: {np} rows")

    # 3. gov-wide
    d = json.loads((RAW / "total_budgetary_resources.json").read_text())
    n = 0
    for fy, payload in d.items():
        for r in payload.get("results", []):
            c.execute("INSERT OR REPLACE INTO gov_budgetary_resources VALUES (?,?,?)",
                      (r.get("fiscal_year"), r.get("fiscal_period"), num(r.get("total_budgetary_resources"))))
            n += 1
    print(f"gov_budgetary_resources: {n} rows")

    # 4. VA TAS
    d = json.loads((RAW / "federal_accounts_036.json").read_text())
    res = d.get("results", d if isinstance(d, list) else [])
    c.executemany(
        "INSERT OR REPLACE INTO va_federal_accounts VALUES (?,?,?,?)",
        [(r.get("code"), r.get("name"), num(r.get("obligated_amount")), num(r.get("gross_outlay_amount"))) for r in res],
    )
    print(f"va_federal_accounts: {len(res)}")

    # 5. debt
    rows = json.loads((RAW / "debt_to_penny.json").read_text())
    c.executemany(
        "INSERT OR REPLACE INTO debt_to_penny VALUES (?,?,?,?)",
        [(r["record_date"], num(r.get("tot_pub_debt_out_amt")), num(r.get("debt_held_public_amt")),
          num(r.get("intragov_hold_amt"))) for r in rows],
    )
    print(f"debt_to_penny: {len(rows)}")

    # 6. MTS receipts
    rows = json.loads((RAW / "mts_table_9.json").read_text())
    c.executemany(
        "INSERT INTO mts_receipts (record_date, classification_id, classification_desc, current_month_amt, fytd_amt, prior_fytd_amt, line_code_nbr) VALUES (?,?,?,?,?,?,?)",
        [
            (
                r.get("record_date"), str(r.get("classification_id")), r.get("classification_desc"),
                num(r.get("current_month_rcpt_outly_amt")), num(r.get("current_fytd_rcpt_outly_amt")),
                num(r.get("prior_fytd_rcpt_outly_amt")), str(r.get("line_code_nbr")),
            )
            for r in rows
        ],
    )
    print(f"mts_receipts: {len(rows)}")

    # 7. File D (best-effort)
    fd = RAW / "filed_account_balances.csv"
    if fd.exists():
        with fd.open() as f:
            rows = list(csv.DictReader(f))
        n = 0
        for r in rows:
            code = r.get("federal_account_code") or r.get("account_code") or r.get("tas") or ""
            oc = r.get("object_class_code") or r.get("object_class") or ""
            if not code:
                continue
            c.execute("INSERT INTO file_d VALUES (?,?,?,?,?,?)",
                      (code, oc, num(r.get("fiscal_period")),
                       num(r.get("obligated_amt")) or num(r.get("gross_obligated_amt")),
                       num(r.get("outlay_amt")) or num(r.get("gross_outlay_amt")),
                       num(r.get("unliquidated_balance_amt")) or num(r.get("unliquidated_adjments_amt"))))
            n += 1
        print(f"file_d: {n} rows")
    else:
        print("file_d: no CSV this run (endpoint errors) — table empty")

    # 8. FRED series
    for p in sorted(RAW.glob("fred_*.csv")):
        sid = p.stem.split("_", 1)[1]
        table = re.sub(r"[^A-Za-z0-9]", "", sid).lower()
        c.execute(f"CREATE TABLE IF NOT EXISTS {table}(date TEXT PRIMARY KEY, value REAL)")
        with p.open() as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].strip() and row[0] != "observation_date":
                    v = num(row[1])
                    if v is not None:
                        c.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?)", (row[0], v))
        print(f"fred {sid}: loaded")

    con.commit()
    size = DB.stat().st_size // 1024
    print(f"OK -> {DB} ({size} KB)")


if __name__ == "__main__":
    main()
