-- Top 15 agencies by budget authority (latest snapshot from the toptier reference).
SELECT abbreviation, name,
       ROUND(budget_authority_amount/1e9, 1) AS ba_bn,
       ROUND(obligated_amount/1e9, 1)       AS obligated_bn,
       ROUND(outlay_amount/1e9, 1)           AS outlay_bn
FROM toptier_agencies
WHERE budget_authority_amount IS NOT NULL
ORDER BY budget_authority_amount DESC
LIMIT 15;
