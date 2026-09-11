-- Macro context for the monthly series (latest observation per series).
SELECT 'GS10 10y yield %' AS series, date, value FROM gs10
WHERE date = (SELECT MAX(date) FROM gs10)
UNION ALL
SELECT 'DFF fed funds eff %', date, value FROM dff WHERE date = (SELECT MAX(date) FROM dff)
UNION ALL
SELECT 'T10Y3M spread', date, value FROM t10y3m WHERE date = (SELECT MAX(date) FROM t10y3m)
UNION ALL
SELECT 'UNRATE %', date, value FROM unrate WHERE date = (SELECT MAX(date) FROM unrate)
UNION ALL
SELECT 'CPIAUCSL index', date, value FROM cpiaucsl WHERE date = (SELECT MAX(date) FROM cpiaucsl)
UNION ALL
SELECT 'M2SL $bn', date, value FROM m2sl WHERE date = (SELECT MAX(date) FROM m2sl)
UNION ALL
SELECT 'FGEXPND outlays $bn', date, value FROM fgexpnd WHERE date = (SELECT MAX(date) FROM fgexpnd);
