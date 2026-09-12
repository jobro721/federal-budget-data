-- FY-over-FY budget execution for the tracked agencies (036 VA, 020 US Treasury, 012 USDA).
SELECT code, fiscal_year,
       ROUND(agency_budgetary_resources/1e9, 1) AS ba_bn,
       ROUND(agency_total_obligated/1e9, 1)     AS obligated_bn,
       ROUND(agency_total_outlayed/1e9, 1)      AS outlay_bn,
       ROUND(agency_total_obligated/agency_budgetary_resources*100, 1) AS obligation_pacing_pct
FROM agency_budgetary_resources
WHERE fiscal_year IN (2023, 2024, 2025)
ORDER BY code, fiscal_year;
