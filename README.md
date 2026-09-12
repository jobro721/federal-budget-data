# federal-budget-data — a frozen SQLite spine of public federal budget data

**Pull, load, query.** The canonical ETL for this portfolio: pull public federal
budget data (USAspending, Treasury FiscalData, FRED — all keyless), land it in
`data/raw/`, load it into a 15-table SQLite database (`data/budget.db`,
**46,042 rows**, frozen 2026-09-12), and keep a set of ten reference queries on
top. Every API call is logged with its exact URL and parameters in
`data/pull_log.md`, so every number is reproducible to the call.

```
internet (keyless, CC0/public)
  └─ etl/pull_*.py        → data/raw/*.json|csv   (+ data/pull_log.md audit trail)
etl/topup.py              → gap recovery (only fills empties, never overwrites)
  └─ etl/load_sqlite.py   → data/budget.db        (15 tables, idempotent)
queries/01…10_*.sql       → reference analyses
```

## The pipeline

```sh
# requirements: requests (ETL); the queries need only sqlite3
python3 etl/pull_usaspending.py   # USAspending API v2 (no key, CC0 1.0)
python3 etl/pull_treasury.py      # Treasury FiscalData API (no key)
python3 etl/pull_fred.py          # FRED keyless CSV endpoint (fredgraph.csv)
python3 etl/topup.py              # optional: re-fetch empty/missing payloads only
python3 etl/load_sqlite.py        # raw/ → budget.db (DELETE+INSERT per table)
```

- `pull_usaspending.py` retries 3× with backoff (the public API rate-limits
  bursts) and logs every request; `topup.py` is the recovery path for
  load-shed endpoints — safe to re-run any time, it only fills gaps.
- `load_sqlite.py` is idempotent (small datasets, full reload). Schema below.

## The database (15 tables, 46,042 rows at the freeze)

| Table | Rows | Contents |
|---|---:|---|
| `toptier_agencies` | 111 | all top-tier agencies + latest snapshot amounts (BA / obligated / outlay) |
| `agency_budgetary_resources` | 30 | tracked agencies × fiscal year: budgetary resources, obligated, outlayed |
| `agency_obligation_by_period` | 216 | cumulative obligated by agency × fiscal year × fiscal period |
| `gov_budgetary_resources` | 33 | government-wide budgetary resources by fiscal period |
| `va_federal_accounts` | 44 | VA (036) federal accounts (TAS): obligated + gross outlay |
| `debt_to_penny` | 2,935 | daily total public debt (2015-01-01 → freeze), held-public + intragov split |
| `mts_receipts` | 1,221 | Monthly Treasury Statement receipts (Table 9), ~3 years of monthly snapshots |
| `file_d` | 0 | **empty by design** — File D (VA FY2024) endpoint was server-broken (HTTP 500) on several periods at freeze; the table exists for schema completeness, `topup.py` is the recovery path |
| `cpiaucsl` / `dff` / `fgexpnd` / `gs10` / `m2sl` / `t10y3m` / `unrate` | 955 / 26,369 / 318 / 881 / 811 / 11,175 / 943 | one table per FRED series (date, value) |

Column-level schema is in the `load_sqlite.py` docstring (verbatim `CREATE`
statements live there and are the source of truth).

## Sources (all public, all keyless)

- **USAspending API v2** (`api.usaspending.gov/api/v2`, CC0 1.0): top-tier
  reference; agency budgetary resources for **036 (VA), 020 (US Treasury),
  012 (USDA)** — FY2023–2025 requested, the endpoint returns its full history;
  government-wide total budgetary resources; VA federal accounts; File D
  account balances (best-effort, see `file_d` above).
- **Treasury FiscalData API** (`api.fiscaldata.treasury.gov/…/fiscal_service`):
  Debt to the Penny (daily) and MTS Table 9 receipts. (The
  `…/fiscal/service/…` URL variant 404s — this base is the verified one.)
- **FRED keyless CSV endpoint** (`fred.stlouisfed.org/graph/fredgraph.csv?id=`):
  `FGEXPND` (outlays), `M2SL`, `GS10`, `DFF` (eff. fed funds, daily — replaced
  the retired `FEDFUNS`), `T10Y3M`, `UNRATE`, `CPIAUCSL`. `FEDFUNS`/`GFED01`/
  `GFED02` are **retired (404) — do not re-add them.**

**Agency-code ground truth (verified against the frozen top-tier reference
2026-09-12):** `036 = VA`, `020 = US Treasury`, `012 = USDA` are the *only*
codes in the per-period tables. The other agencies (DoD 097, HHS 075, NASA 080,
…) appear only in `toptier_agencies` — the sibling repos rely on that
distinction by design.

## The ten reference queries

| # | Query | What it answers |
|---|---|---|
| 01 | `agency_fy_over_fy` | FY-over-FY execution (BA / obligated / outlay) for the three tracked agencies |
| 02 | `govwide_by_period` | government-wide budgetary resources by fiscal period |
| 03 | `va_by_period_obligations` | VA cumulative obligated by period, latest FY |
| 04 | `va_tas_top` | VA's top federal accounts (TAS) by obligation |
| 05 | `debt_trajectory` | total public debt, one observation per month |
| 06 | `debt_monthly_growth` | month-over-month debt growth (note: the CTE reference must be `t.record_date` — a bare name resolves to the innermost scope and breaks the correlation) |
| 07 | `mts_receipts_latest` | latest MTS receipts snapshot by source, current month / FYTD / prior FYTD |
| 08 | `fred_macro_context` | latest value of all seven macro series |
| 09 | `outlays_vs_receipts_pacing` | FGEXPND outlays vs their trailing 12-month average |
| 10 | `top_agencies_by_ba` | top 15 agencies by budget authority (toptier snapshot) |

Run any of them:

```sh
sqlite3 data/budget.db < queries/01_agency_fy_over_fy.sql
# or: python3 -c "import sqlite3,sys;print(sqlite3.connect('data/budget.db').executescript(sys.stdin.read()).fetchall())" < queries/01_agency_fy_over_fy.sql
```

## How the sibling repos use this

- **`nl-to-sql`** ships a SHA-256-pinned copy of `data/budget.db` and its
  40-query grid derives from exactly these tables; its `F` template documents
  a deliberate `ORDER BY` deviation from query 06 (pinned, not drift).
- **`budget-workbench`**'s `LoadFileD_CSV.bas` ingests File D-shaped CSVs
  (the column layout of `file_d` / `data/synthetic/filed_sample.csv`) — the
  bridge between this pipeline and the Excel toolkit.
- **`dbt-budget`**, **`cbo-validator`**, **`power-bi-dashboard`**, and the
  **`budget-training`** program all build on the same public sources through
  their own frozen snapshots (one-directional source → build → artifact).

## Reproducibility

- `data/pull_log.md` is the full audit trail: timestamp, exact URL,
  parameters, HTTP status, and a note for every call (including the two HTTP
  500s that left `file_d` empty).
- `etl/topup.py` re-runs at any time and only fills gaps.
- `etl/load_sqlite.py` rebuilds the database from `data/raw/` exactly.
- The frozen database's SHA-256 is pinned by the consumer repos, so a stale or
  tampered copy fails their build gates.

## Layout

```
data/
  budget.db               the frozen 15-table database (this repo's artifact)
  pull_log.md             per-call audit trail (URL + params + status)
  raw/                    raw API payloads (13 JSON/CSV files)
etl/
  pull_usaspending.py     USAspending puller (retry + logging)
  pull_treasury.py        Treasury FiscalData puller (paginated)
  pull_fred.py            FRED keyless CSV puller (7 series)
  topup.py                gap-only recovery pass
  load_sqlite.py          raw → SQLite (schema = its docstring)
queries/01…10_*.sql       the ten reference analyses
```

All data is public (USAspending CC0 1.0; Treasury and FRED public releases).
No CUI, no internal systems, no agency-internal figures.

A personal project by a federal budget analyst — not affiliated with my
employer, built on public data only.
