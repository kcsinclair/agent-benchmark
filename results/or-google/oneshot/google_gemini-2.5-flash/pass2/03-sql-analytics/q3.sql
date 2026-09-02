-- q4.sql
SELECT
  strftime('%Y-%m', o.ordered_at) AS month,
  ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM orders AS o
JOIN order_items AS oi
  ON o.id = oi.order_id
JOIN products AS p
  ON oi.product_id = p.id
WHERE
  o.status = 'completed' AND strftime('%Y', o.ordered_at) = '2025'
GROUP BY
  month
HAVING
  revenue > 0
ORDER BY
  month ASC;
