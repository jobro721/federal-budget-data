-- Federal outlays pacing (FRED FGEXPND, monthly $bn) vs the 12-month average.
WITH m AS (
    SELECT date, value,
           AVG(value) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS avg12
    FROM fgexpnd
)
SELECT date, ROUND(value, 1) AS outlays_bn, ROUND(avg12, 1) AS avg12_bn,
       ROUND((value/avg12 - 1)*100, 1) AS vs_avg12_pct
FROM m
ORDER BY date DESC
LIMIT 13;
