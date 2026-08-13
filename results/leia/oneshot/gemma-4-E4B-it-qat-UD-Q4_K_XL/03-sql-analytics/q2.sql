SELECT
  T2.name AS product_name,
  SUM(T1.quantity) AS units_sold
FROM order_items AS T1
INNER JOIN products AS T2
  ON T1.product_id = T2.id
INNER JOIN orders AS T3
  ON T1.order_id = T3.id
WHERE
  T3.status = 'completed'
GROUP BY
  T2.id
ORDER BY
  units_sold DESC,
  product_name ASC
LIMIT 3
