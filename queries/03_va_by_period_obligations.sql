-- VA (036) cumulative obligated by fiscal period, latest fiscal year available.
SELECT fiscal_year, period, ROUND(obligated/1e9, 1) AS cumulative_obligated_bn
FROM agency_obligation_by_period
WHERE code = '036'
  AND fiscal_year = (SELECT MAX(fiscal_year) FROM agency_obligation_by_period WHERE code = '036')
ORDER BY period;
