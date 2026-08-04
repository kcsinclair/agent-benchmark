SELECT name AS customer_name, country
FROM customers
WHERE id NOT IN (SELECT DISTINCT customer_id FROM orders)
ORDER BY customer_name ASC
