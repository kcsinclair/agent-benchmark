SELECT 
  c.name AS customer_name,
  ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM 
  customers c
  JOIN orders o ON c.id = o.customer_id
  JOIN order_items oi ON o.id = oi.order_id
  JOIN products p ON oi.product_id = p.id
WHERE 
  o.status = 'completed'
GROUP BY 
  c.name
ORDER BY 
  revenue DESC, c.name ASC;
