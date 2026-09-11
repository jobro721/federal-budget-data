-- Top federal accounts (TAS) for VA by obligation, FY2024.
SELECT code, name,
       ROUND(obligated_amount/1e9, 1)   AS obligated_bn,
       ROUND(gross_outlay_amount/1e9, 1) AS outlay_bn,
       ROUND((obligated_amount - gross_outlay_amount)/1e9, 1) AS uob_bn
FROM va_federal_accounts
ORDER BY obligated_amount DESC
LIMIT 10;
