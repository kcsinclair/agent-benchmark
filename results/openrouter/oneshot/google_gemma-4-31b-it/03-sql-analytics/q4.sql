SELECT 
    strftime('%Y-%m', o.ordered_at) AS month, 
    ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed' 
  AND o.ordered_at >= '2025-01-01' 
  AND o.ordered_at <= '2025-12-31'
GROUP BY month
ORDER BY month ASC;
