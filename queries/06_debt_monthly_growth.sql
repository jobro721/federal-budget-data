-- Month-over-month change in total public debt (first observation of each month).
-- Note: the CTE row must be referenced explicitly (t.record_date) — a bare
-- record_date resolves to the innermost scope and breaks the correlation.
WITH monthly AS (
    SELECT strftime('%Y-%m', t.record_date) AS ym,
           (SELECT d2.tot_pub_debt_out_amt FROM debt_to_penny d2
            WHERE d2.record_date = (SELECT MIN(d3.record_date) FROM debt_to_penny d3
                                    WHERE strftime('%Y-%m', d3.record_date)
                                           = strftime('%Y-%m', t.record_date))) AS debt
    FROM debt_to_penny t
    GROUP BY strftime('%Y-%m', t.record_date)
)
SELECT m.ym,
       ROUND((m.debt - LAG(m.debt) OVER (ORDER BY m.ym))/1e9, 1) AS change_bn
FROM monthly m
ORDER BY m.ym
LIMIT 24;
