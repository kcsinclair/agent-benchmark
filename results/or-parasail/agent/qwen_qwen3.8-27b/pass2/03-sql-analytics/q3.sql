SELECT
  c.name AS customer_name,
  c.country AS country
FROM customers c
WHERE c.id NOT IN (SELECT customer_id FROM orders)
ORDER BY customer_name ASC;
