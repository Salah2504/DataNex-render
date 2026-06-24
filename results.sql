You:
table prod_tbl columns factory_id,prod_id,prod_date,qty table prod_desc columns prod_id,prod_name

DataNex AI:
Schema received successfully.
You:
show production today

DataNex AI:
SELECT
  pt.factory_id,
  pt.prod_id,
  pt.prod_date,
  pt.qty
FROM prod_tbl pt
WHERE pt.prod_date = TODAY
You:
show production this year

DataNex AI:
SELECT
  pt.factory_id,
  pt.prod_id,
  pt.prod_date,
  pt.qty
FROM prod_tbl pt
WHERE pt.prod_date >= TODAY - 365

ORDER BY pt.prod_date DESC
You:
total production

DataNex AI:
SELECT
  SUM(pt.qty) AS total_qty
FROM prod_tbl pt
You:
total production by factory

DataNex AI:
SELECT
  pt.factory_id,
  SUM(pt.qty) AS total_qty
FROM prod_tbl pt

GROUP BY
  pt.factory_id
ORDER BY total_qty DESC
You:
average production by product

DataNex AI:
SELECT
  pt.prod_id,
  AVG(pt.qty) AS average_qty
FROM prod_tbl pt

GROUP BY
  pt.prod_id
ORDER BY average_qty DESC
You:
count products

DataNex AI:
SELECT
  COUNT(DISTINCT pt.prod_id) AS prod_count
FROM prod_tbl pt
You:
count factories

DataNex AI:
SELECT
  COUNT(DISTINCT pt.factory_id) AS factory_count
FROM prod_tbl pt
You:
count rows

DataNex AI:
SELECT
  COUNT(*) AS row_count
FROM prod_tbl pt
You:
show product name production today

DataNex AI:
SELECT
  pt.prod_id,
  pd.prod_name,
  pt.factory_id,
  pt.prod_date,
  pt.qty
FROM prod_tbl pt
JOIN prod_desc pd
ON pt.prod_id
= pd.prod_id
WHERE pt.prod_date = TODAY
