SELECT
  T1.name,
  T1.country
FROM customers AS T1
LEFT JOIN orders AS T2
  ON T1.id = T2.customer_id
WHERE
  T2.id IS NULL
ORDER BY
  T1.name ASC;
