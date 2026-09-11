# USAspending pull log
Started 2026-09-11 13:25 by pull_usaspending.py
Base: https://api.usaspending.gov/api/v2 (no key; CC0 1.0 data).
- 2026-09-11 13:25 GET https://api.usaspending.gov/api/v2/references/toptier_agencies/ -> 200
  note: all top-tier agencies
- 2026-09-11 13:25 GET https://api.usaspending.gov/api/v2/agency/036/budgetary_resources/ -> 200
  note: agency 036 (endpoint returns multiple years)
- 2026-09-11 13:25 GET https://api.usaspending.gov/api/v2/agency/020/budgetary_resources/ -> 200
  note: agency 020 (endpoint returns multiple years)
  note: agency 012 (endpoint returns multiple years)
- 2026-09-11 13:26 GET https://api.usaspending.gov/api/v2/references/total_budgetary_resources/ -> 200
  note: gov-wide 2023
  note: gov-wide 2024
- 2026-09-11 13:26 GET https://api.usaspending.gov/api/v2/references/total_budgetary_resources/ -> 200
  note: gov-wide 2025
- 2026-09-11 13:26 GET https://api.usaspending.gov/api/v2/agency/036/federal_account/ -> 200
  note: VA TAS list FY2024
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P02
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P03
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P04
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P05
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P06
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P07
- 2026-09-11 13:26 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 500
  note: File D account_balances VA FY2024 P08
  note: File D account_balances VA FY2024 P09
- 2026-09-11 13:28 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P10
- 2026-09-11 13:28 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 200
  note: File D account_balances VA FY2024 P11
- 2026-09-11 13:28 POST https://api.usaspending.gov/api/v2/download/accounts/ -> 500
  note: File D account_balances VA FY2024 P12
- 2026-09-11 13:33 TOPUP GET https://api.usaspending.gov/api/v2/agency/012/budgetary_resources/ -> 200
- 2026-09-11 13:33 TOPUP GET https://api.usaspending.gov/api/v2/references/total_budgetary_resources/ -> 200
