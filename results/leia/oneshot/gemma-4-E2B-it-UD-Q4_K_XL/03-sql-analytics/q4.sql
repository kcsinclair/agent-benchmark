SELECT
  strftime('%Y-%m', T1.ordered_at) AS month,
  ROUND(SUM(T3.quantity * T2.unit_price), 2) AS revenue
FROM orders AS T1
INNER JOIN order_items AS T3
  ON T1.id = T3.order_id
INNER JOIN products AS T2
  ON T3.product_id = T2.id
WHERE
  T1.status = 'completed' AND STRFTIME('%Y', T1.ordered_at) = '2025'
GROUP BY
  month
HAVING
  SUM(T3.quantity * T2.unit_price) > 0
ORDER BY
  month ASC;
