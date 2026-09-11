-- Government-wide budgetary resources by fiscal period (fiscal_year, period 1-12).
SELECT fiscal_year, fiscal_period,
       ROUND(total_budgetary_resources/1e12, 3) AS br_tn
FROM gov_budgetary_resources
ORDER BY fiscal_year, fiscal_period;
