SELECT
  c.name AS customer_name,
  c.country
FROM customers c
WHERE c.id NOT IN (
  SELECT DISTINCT customer_id FROM orders
)
ORDER BY customer_name ASC;
