SELECT 
  substr(name, 1, instr(quote(' ', name) + ' ' - 1) || ' ') AS customer_name,
  ROUND(SUM(order_items.quantity * products.unit_price), 2) AS revenue
FROM 
  customers
  JOIN orders
  JOIN order_items
  JOIN products
  JOIN (
    SELECT 
      order_id, 
      MAX(ordered_at) AS ordered_at
    FROM 
      orders
    WHERE 
      status = 'completed'
    GROUP BY 
      order_id
  ) AS completed_orders
WHERE 
  customers.id = order_items.customer_id
  AND order_items.order_id IN (
    SELECT 
      order_id
    FROM 
      completed_orders
  )
GROUP BY 
  customer_name
ORDER BY 
  SUM(order_items.quantity * products.unit_price) DESC,
         customer_name ASC
LIMIT 1;
