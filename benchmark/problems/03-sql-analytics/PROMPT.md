# Problem 3 — SQL Analytics (SQLite, medium)

You are given a SQLite database with this schema:

```sql
CREATE TABLE customers (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  country    TEXT NOT NULL,
  created_at TEXT NOT NULL              -- ISO date, e.g. '2025-03-14'
);

CREATE TABLE products (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  unit_price REAL NOT NULL              -- price per unit in dollars
);

CREATE TABLE orders (
  id          INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  status      TEXT NOT NULL,            -- 'completed', 'pending', or 'cancelled'
  ordered_at  TEXT NOT NULL             -- ISO date
);

CREATE TABLE order_items (
  order_id   INTEGER NOT NULL REFERENCES orders(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity   INTEGER NOT NULL
);
```

Line revenue for an order item is `quantity * products.unit_price` (use the
current product price; there is no historical price table). Only orders with
`status = 'completed'` count toward revenue or units sold.

Write **four SQL files**, each containing exactly one `SELECT` statement
(no comments required, trailing semicolon optional):

### `q1.sql` — Revenue per customer
Columns: `customer_name`, `revenue` (REAL, rounded to 2 decimal places with
`ROUND`). One row per customer **that has at least one completed order**.
Order by `revenue` descending, then `customer_name` ascending.

### `q2.sql` — Top 3 products by units sold
Columns: `product_name`, `units_sold` (total quantity across completed
orders). Order by `units_sold` descending, then `product_name` ascending.
Return at most 3 rows. Products with no completed sales must not appear.

### `q3.sql` — Customers with no orders at all
Columns: `customer_name`, `country`. Customers that have **zero rows** in
`orders` (any status). Order by `customer_name` ascending.

### `q4.sql` — Monthly revenue for 2025
Columns: `month` (format `'2025-01'` … `'2025-12'`, i.e. `strftime('%Y-%m', ...)`),
`revenue` (rounded to 2 decimals). Only months of 2025 that have non-zero
revenue from completed orders. Order by `month` ascending.

## Constraints

- Plain SQLite SQL (no extensions). Each file must run as-is against the
  schema above.
- Do not modify data; `SELECT` only.
- Your queries will be run against a hidden dataset using this schema — do
  not hard-code values from any example data.

**Deliverables: exactly four files — `q1.sql`, `q2.sql`, `q3.sql`, `q4.sql`.**
