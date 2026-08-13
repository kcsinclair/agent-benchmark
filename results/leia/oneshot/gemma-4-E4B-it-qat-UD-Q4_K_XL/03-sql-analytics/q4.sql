SELECT
  strftime('%Y-%m', T4.ordered_at) AS month,
  ROUND(SUM(T3.quantity * T2.unit_price), 2) AS revenue
FROM orders AS T4
INNER JOIN order_items AS T3
  ON T4.id = T3.order_id
INNER JOIN products AS T2
  ON T3.product_id = T2.id
WHERE
  T4.status = 'completed' AND strftime('%Y', T4.ordered_at) = '2025'
GROUP BY
  month
HAVING
  revenue > 0
ORDER BY
  month ASC
