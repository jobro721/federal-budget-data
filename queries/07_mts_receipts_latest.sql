-- Latest MTS receipts snapshot by source (Table 9), with FY-to-date vs prior year.
-- (table column names differ from the API names — see etl/load_sqlite.py)
SELECT classification_desc,
       ROUND(current_month_amt/1e9, 1)  AS current_month_bn,
       ROUND(fytd_amt/1e9, 1)           AS fytd_bn,
       ROUND(prior_fytd_amt/1e9, 1)     AS prior_fytd_bn
FROM mts_receipts
WHERE record_date = (SELECT MAX(record_date) FROM mts_receipts)
ORDER BY classification_desc;
