SELECT 
  p.name AS product_name,
  SUM(oi.quantity) AS units_sold
FROM 
  products p
  JOIN order_items oi ON p.id = oi.product_id
  JOIN orders o ON oi.order_id = o.id
WHERE 
  o.status = 'completed'
GROUP BY 
  p.name
ORDER BY 
  units_sold DESC, p.name ASC
LIMIT 3;
