SELECT c.name AS customer_name,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.id AND o.status = 'completed'
JOIN order_items oi ON oi.order_id = o.id
JOIN products p ON p.id = oi.product_id
GROUP BY c.id, c.name
ORDER BY revenue DESC, customer_name ASC
