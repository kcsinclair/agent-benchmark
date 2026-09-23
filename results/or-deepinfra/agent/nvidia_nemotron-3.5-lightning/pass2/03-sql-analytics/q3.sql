SELECT c.name, c.country
FROM customers c
WHERE c.id NOT IN (SELECT DISTINCT customer_id FROM orders)
ORDER BY c.name ASC;
