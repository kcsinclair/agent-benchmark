SELECT c.name AS customer_name, c.country
FROM customers c
WHERE c.id NOT IN (SELECT o.customer_id FROM orders o)
ORDER BY customer_name ASC;
