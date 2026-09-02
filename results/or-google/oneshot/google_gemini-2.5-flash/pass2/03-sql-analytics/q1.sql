-- q1.sql
SELECT
  c.name AS customer_name,
  ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM customers AS c
JOIN orders AS o
  ON c.id = o.customer_id
JOIN order_items AS oi
  ON o.id = oi.order_id
JOIN products AS p
  ON oi.product_id = p.id
WHERE
  o.status = 'completed'
GROUP BY
  c.id,
  c.name
ORDER BY
  revenue DESC,
  customer_name ASC;
