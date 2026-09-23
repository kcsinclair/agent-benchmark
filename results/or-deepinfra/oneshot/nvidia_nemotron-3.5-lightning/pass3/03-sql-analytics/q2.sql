SELECT p.name AS product_name,
       SUM(oi.quantity) AS units_sold
FROM products p
JOIN order_items oi ON oi.product_id = p.id
JOIN orders o ON o.id = oi.order_id
WHERE o.status = 'completed'
GROUP BY p.id
ORDER BY units_sold DESC, p.name ASC
LIMIT 3;
