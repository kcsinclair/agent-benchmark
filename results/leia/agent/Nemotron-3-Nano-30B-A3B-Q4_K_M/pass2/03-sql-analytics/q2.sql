SELECT p.name AS product_name,
       SUM(oi.quantity) AS units_sold
FROM order_items oi
JOIN orders o ON o.id = oi.order_id AND o.status = 'completed'
JOIN products p ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY units_sold DESC, p.name ASC
LIMIT 3;
