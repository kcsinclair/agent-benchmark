SELECT 
  products.name AS product_name,
  SUM(order_items.quantity) AS units_sold
FROM 
  order_items
  JOIN products ON order_items.product_id = products.id
  JOIN (
    SELECT 
      product_id, 
      SUM(quantity) AS total_units
    FROM 
      order_items
    GROUP BY 
      product_id
    HAVING 
      COUNT(*) >= (
        SELECT 
          COUNT(*)
        FROM 
          order_items
        GROUP BY 
          product_id
        HAVING 
          COUNT(*) >= (
            SELECT 
              COUNT(*)
            FROM 
              order_items
            GROUP BY 
              product_id
            ORDER BY 
              COUNT(*) DESC
            LIMIT 1
          )
      )
  ) AS subquery
GROUP BY 
  product_id
HAVING 
  COUNT(*) >= (
    SELECT 
      COUNT(*)
    FROM 
      order_items
    GROUP BY 
      product_id
    HAVING 
      COUNT(*) >= (
        SELECT 
          COUNT(*)
        FROM 
          order_items
        GROUP BY 
          product_id
        ORDER BY 
          COUNT(*) DESC
        LIMIT 1
      )
ORDER BY 
  units_sold DESC,
         product_name ASC
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No data', 0
UNION ALL
SELECT 
  'No UNION
