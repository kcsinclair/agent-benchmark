SELECT
  T1.name AS customer_name,
  ROUND(SUM(T3.quantity * T2.unit_price), 2) AS revenue
FROM customers AS T1
INNER JOIN orders AS T4
  ON T1.id = T4.customer_id
INNER JOIN order_items AS T3
  ON T4.id = T3.order_id
INNER JOIN products AS T2
  ON T3.product_id = T2.id
WHERE
  T4.status = 'completed'
GROUP BY
  T1.id
ORDER BY
  revenue DESC,
  customer_name ASC
