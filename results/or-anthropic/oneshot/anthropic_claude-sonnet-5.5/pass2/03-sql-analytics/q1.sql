SELECT c.name AS customer_name,
       ROUND(COALESCE(SUM(oi.quantity * p.unit_price), 0), 2) AS revenue
FROM customers c
JOIN orders o              ON o.customer_id = c.id AND o.status = 'completed'
LEFT JOIN order_items oi   ON oi.order_id = o.id
LEFT JOIN products p       ON p.id = oi.product_id
GROUP BY c.id, c.name
ORDER BY revenue DESC, customer_name ASC;
