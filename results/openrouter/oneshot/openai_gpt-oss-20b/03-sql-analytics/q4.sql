SELECT strftime('%Y-%m', o.ordered_at) AS month,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'completed'
  AND strftime('%Y', o.ordered_at) = '2025'
GROUP BY month
HAVING SUM(oi.quantity * p.unit_price) > 0
ORDER BY month ASC;
