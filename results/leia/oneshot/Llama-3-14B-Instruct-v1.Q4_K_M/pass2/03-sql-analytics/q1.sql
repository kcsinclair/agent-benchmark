SELECT 
  substr(name, 1, instr(quote(' ', name) + ' ' - 1) + 1) AS customer_name,
  ROUND(SUM(order_items.quantity * products.unit_price), 2) AS revenue
FROM 
  orders
  JOIN customers ON orders.customer_id = customers.id
  JOIN order_items ON order_items.order_id = orders.id
  JOIN products ON order_items.product_id = products.id
WHERE 
  orders.status = 'completed'
GROUP BY 
  orders.customer_id
HAVING 
  COUNT(*) > 0
ORDER BY 
  SUM(order_items.quantity * products.unit_price) DESC,
         customer_name ASC
