You:
table prod_tbl columns factory_id,prod_id,prod_date,qty table prod_desc columns prod_id,prod_name

DataNex AI:
Schema received successfully.
You:
total production today

DataNex AI:
SELECT
  SUM(pt.qty) AS total_qty

FROM prod_tbl pt

WHERE pt.prod_date = TODAY
You:
production by factory

DataNex AI:
SELECT
  pt.factory_id,
  SUM(pt.qty) AS total_qty

FROM prod_tbl pt

GROUP BY 
  pt.factory_id

ORDER BY
  total_qty DESC
You:
count products by factory

DataNex AI:
SELECT
  pt.factory_id,
  COUNT(DISTINCT pt.prod_id) AS prod_count

FROM prod_tbl pt

GROUP BY 
  pt.factory_id

ORDER BY
  prod_count DESC
You:
top 5 products by production

DataNex AI:
SELECT FIRST 5 
  pt.prod_id,
  SUM(pt.qty) AS total_qty

FROM prod_tbl pt

GROUP BY 
  pt.prod_id

ORDER BY
  total_qty DESC
You:
highest production product today

DataNex AI:
SELECT FIRST 1 
  pt.prod_id,
  MAX(pt.qty) AS maximum_qty

FROM prod_tbl pt

WHERE pt.prod_date = TODAY

GROUP BY 
  pt.prod_id

ORDER BY
  maximum_qty DESC
You:
factories with sum production > 1000

DataNex AI:
SELECT
  pt.factory_id,
  SUM(pt.qty) AS total_qty

FROM prod_tbl pt

GROUP BY 
  pt.factory_id

HAVING
  SUM(pt.qty) > 1000

ORDER BY
  total_qty DESC
You:
products with sum production > 500

DataNex AI:
SELECT
  pt.prod_id,
  SUM(pt.qty) AS total_qty

FROM prod_tbl pt

GROUP BY 
  pt.prod_id

HAVING
  SUM(pt.qty) > 500

ORDER BY
  total_qty DESC
You:
products with sum production > 500 in this month

DataNex AI:
SELECT
  pt.prod_id,
  SUM(pt.qty) AS total_qty

FROM prod_tbl pt

WHERE pt.prod_date >= TODAY - 30

GROUP BY 
  pt.prod_id

HAVING
  SUM(pt.qty) > 500

ORDER BY
  total_qty DESC
You:
factories with average production > 100

DataNex AI:
SELECT
  pt.factory_id,
  AVG(pt.qty) AS average_qty

FROM prod_tbl pt

GROUP BY 
  pt.factory_id

HAVING
  AVG(pt.qty) > 100

ORDER BY
  average_qty DESC
You:
factories with average production > 100 today

DataNex AI:
SELECT
  pt.factory_id,
  AVG(pt.qty) AS average_qty

FROM prod_tbl pt

WHERE pt.prod_date = TODAY

GROUP BY 
  pt.factory_id

HAVING
  AVG(pt.qty) > 100

ORDER BY
  average_qty DESC