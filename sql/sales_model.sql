SELECT s.*, p.product_name, p.category, p.material,
       ROUND(CASE WHEN s.status = 'delivered' THEN s.units * s.unit_price ELSE 0 END, 2) AS revenue,
       ROUND(CASE WHEN s.status = 'delivered' THEN s.units * s.assumed_unit_cost ELSE 0 END, 2) AS item_cost
FROM scenario_orders AS s
JOIN products AS p ON p.sku = s.sku;
