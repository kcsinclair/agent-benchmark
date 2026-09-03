SELECT c.name AS customer_name, c.country
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.id IS NULL
ORDER BY customer_name ASC;
