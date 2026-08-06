SELECT
  c.name AS customer_name,
  c.country
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id
HAVING COUNT(o.id) = 0
ORDER BY customer_name ASC;

--
