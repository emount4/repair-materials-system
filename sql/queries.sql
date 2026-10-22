-- name: materials_list
-- 1. List of warehouse materials, sorted by name.
SELECT id, name, category, price, quantity, unit
FROM materials
ORDER BY name, id;

-- name: operations_list
-- 2. Movement journal: list and JOIN with material names and units.
SELECT o.id, o.material_id, o.kind, o.quantity, o.date, o.note, o.cancelled,
       m.name AS material_name, m.unit AS material_unit
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
ORDER BY o.date DESC, o.id DESC;

-- name: materials_search
-- 3. WHERE: material name and minimum current stock, user parameters.
SELECT id, name, category, price, quantity, unit
FROM materials
WHERE name LIKE ? ESCAPE '\' AND quantity >= ?
ORDER BY name, id;

-- name: materials_in_stock
-- 4. WHERE: enough current stock for the requested quantity.
SELECT id, name, category, price, quantity, unit
FROM materials
WHERE quantity >= ? AND quantity > 0
ORDER BY quantity DESC, id;

-- name: active_operations
-- 5. WHERE + JOIN: non-cancelled movements.
SELECT o.id, o.material_id, o.kind, o.quantity, o.date, o.note, o.cancelled,
       m.name AS material_name, m.unit AS material_unit
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
WHERE o.cancelled = 0
ORDER BY o.date DESC, o.id DESC;

-- name: operations_filter
-- 6. WHERE + JOIN: date, movement kind and cancellation state.
SELECT o.id, o.material_id, o.kind, o.quantity, o.date, o.note, o.cancelled,
       m.name AS material_name, m.unit AS material_unit
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
WHERE (? = '' OR o.kind = ?)
  AND (? = '' OR o.date = ?)
  AND (? = '' OR o.cancelled = ?)
ORDER BY o.date DESC, o.id DESC;

-- name: materials_without_expense
-- 7. Date search: enough CURRENT stock and no active expense on that date.
-- This does not reconstruct historical stock or reserve materials.
SELECT m.id, m.name, m.category, m.price, m.quantity, m.unit
FROM materials AS m
WHERE m.quantity >= ? AND m.quantity > 0
  AND NOT EXISTS (
      SELECT 1 FROM operations AS o
      WHERE o.material_id = m.id AND o.date = ?
        AND o.kind = 'expense' AND o.cancelled = 0
  )
ORDER BY m.name, m.id;

-- name: stock_summary
-- 8. Aggregate: warehouse totals, including an empty warehouse.
SELECT COUNT(*) AS count, COUNT(DISTINCT category) AS categories,
       COALESCE(SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END), 0)
           AS out_of_stock,
       COALESCE(SUM(price * quantity), 0.0) AS total_cost
FROM materials;

-- name: operation_summary
-- 9. Aggregate: total, active, cancelled movements and financial turnover.
SELECT COUNT(*) AS operations_count,
       COUNT(CASE WHEN cancelled = 0 THEN 1 END) AS active_count,
       COUNT(CASE WHEN cancelled = 1 THEN 1 END) AS cancelled_count,
       COALESCE(SUM(CASE WHEN o.cancelled = 0 AND o.kind = 'receipt'
                        THEN o.quantity * m.price ELSE 0 END), 0.0)
           AS receipt_value,
       COALESCE(SUM(CASE WHEN o.cancelled = 0 AND o.kind = 'expense'
                        THEN o.quantity * m.price ELSE 0 END), 0.0)
           AS expense_value
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id;

-- name: category_statistics
-- 10. GROUP BY: category size, current stock value and unit price range.
SELECT category, COUNT(*) AS materials_count,
       SUM(price * quantity) AS stock_value,
       MIN(price) AS min_price, MAX(price) AS max_price,
       AVG(price) AS average_price
FROM materials
GROUP BY category
ORDER BY stock_value DESC, category;

-- name: material_activity
-- 11. GROUP BY + LEFT JOIN: include materials with zero active movements.
SELECT m.id, m.name, m.unit, COUNT(o.id) AS operations_count,
       COALESCE(SUM(CASE WHEN o.kind = 'receipt' THEN o.quantity END), 0.0)
           AS received,
       COALESCE(SUM(CASE WHEN o.kind = 'expense' THEN o.quantity END), 0.0)
           AS spent,
       MAX(o.date) AS last_date
FROM materials AS m
LEFT JOIN operations AS o ON o.material_id = m.id AND o.cancelled = 0
GROUP BY m.id, m.name, m.unit
ORDER BY operations_count DESC, m.id;

-- name: frequent_materials
-- 12. GROUP BY + HAVING: materials with more active movements than a threshold.
SELECT m.id, m.name, COUNT(o.id) AS operations_count
FROM materials AS m
JOIN operations AS o ON o.material_id = m.id
WHERE o.cancelled = 0
GROUP BY m.id, m.name
HAVING COUNT(o.id) > ?
ORDER BY operations_count DESC, m.id;

-- name: material_detail
-- 13. One material and the cost of its current stock.
SELECT id, name, category, price, quantity, unit, price * quantity AS total_cost
FROM materials
WHERE id = ?;

-- name: operation_detail
-- 14. JOIN: one operation with its related material.
SELECT o.id, o.material_id, o.kind, o.quantity, o.date, o.note, o.cancelled,
       m.name AS material_name, m.unit AS material_unit
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
WHERE o.id = ?;
