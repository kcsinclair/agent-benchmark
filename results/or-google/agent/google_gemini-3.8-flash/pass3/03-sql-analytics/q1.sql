SELECT
  c.name AS customer_name,
  ROUND(COALESCE(SUM(oi.quantity * p.unit_price), 0), 2) AS revenue
FROM customers c
JOIN orders o ON c.id = o.customer_id AND o.status = 'completed'
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
GROUP BY c.id, c.name
ORDER BY revenue DESC, customer_name ASC;
