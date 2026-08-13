SELECT
  T2.name,
  SUM(T3.quantity) AS units_sold
FROM orders AS T1
INNER JOIN order_items AS T3
  ON T1.id = T3.order_id
INNER JOIN products AS T2
  ON T3.product_id = T2.id
WHERE
  T1.status = 'completed'
GROUP BY
  T2.name
ORDER BY
  units_sold DESC,
  T2.name ASC
LIMIT 3;
