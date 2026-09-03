SELECT
  p.name AS product_name,
  SUM(oi.quantity) AS units_sold
FROM products AS p
JOIN order_items AS oi
  ON p.id = oi.product_id
JOIN orders AS o
  ON oi.order_id = o.id
WHERE
  o.status = 'completed'
GROUP BY
  p.id,
  p.name
ORDER BY
  units_sold DESC,
  product_name ASC
LIMIT 3;
