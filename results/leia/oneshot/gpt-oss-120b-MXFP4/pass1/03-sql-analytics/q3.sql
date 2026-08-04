SELECT
    c.name AS customer_name,
    c.country
FROM customers c
LEFT JOIN orders o
       ON o.customer_id = c.id
WHERE o.id IS NULL
ORDER BY customer_name ASC;
