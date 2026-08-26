SELECT c.name AS customer_name,
       c.country AS country
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
)
ORDER BY customer_name ASC;
