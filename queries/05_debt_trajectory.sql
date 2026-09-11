-- Total public debt, sampled to one observation per month (first business day of each month).
SELECT record_date,
       ROUND(tot_pub_debt_out_amt/1e12, 3)   AS total_debt_tn,
       ROUND(debt_held_public_amt/1e12, 3)   AS held_public_tn,
       ROUND(intragov_hold_amt/1e12, 3)      AS intragov_tn
FROM debt_to_penny d
WHERE record_date = (
    SELECT MIN(d2.record_date) FROM debt_to_penny d2
    WHERE strftime('%Y-%m', d2.record_date) = strftime('%Y-%m', d.record_date)
)
ORDER BY record_date;
