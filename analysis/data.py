import json
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_data():
    products = pd.read_csv(ROOT / "data/products.csv", keep_default_na=False)
    sales = pd.read_csv(ROOT / "data/scenario_orders.csv")
    if products.empty or products.sku.duplicated().any() or products.sku.eq("").any():
        raise ValueError("Catalog SKUs must be present and unique")
    for field in ["unit_price_low", "unit_price_high", "regular_price", "minimum_order", "rating", "review_count", "ship_days"]:
        products[field] = pd.to_numeric(products[field], errors="coerce")
    if (products.unit_price_low > products.unit_price_high).any():
        raise ValueError("Invalid catalog price range")
    if sales.line_id.duplicated().any() or not sales.sku.isin(products.sku).all():
        raise ValueError("Scenario has duplicate lines or unknown SKUs")
    if not sales.status.isin(["delivered", "returned", "cancelled"]).all():
        raise ValueError("Unknown scenario status")
    if sales.units.le(0).any() or sales.unit_price.lt(0).any() or sales.assumed_unit_cost.lt(0).any():
        raise ValueError("Scenario quantities and amounts must be valid")
    with sqlite3.connect(":memory:") as db:
        products.to_sql("products", db, index=False)
        sales.to_sql("scenario_orders", db, index=False)
        model = pd.read_sql_query((ROOT / "sql/sales_model.sql").read_text(), db)
    model["order_date"] = pd.to_datetime(model.order_date)
    model["gross_profit"] = (model.revenue - model.item_cost).round(2)
    products["discount_pct"] = ((1 - products.unit_price_high / products.regular_price.where(products.regular_price.gt(0))) * 100).round(1)
    return products, model


def summary(lines):
    delivered = lines[lines.status.eq("delivered")]
    orders = delivered.order_id.nunique()
    revenue, profit = delivered.revenue.sum(), delivered.gross_profit.sum()
    return {"revenue": round(float(revenue), 2), "gross_profit": round(float(profit), 2),
            "orders": int(orders), "units": int(delivered.units.sum()),
            "aov": float(revenue / orders) if orders else 0,
            "margin": float(profit / revenue) if revenue else 0}


def manifests():
    return {name: json.loads((ROOT / f"data/{name}_manifest.json").read_text())
            for name in ["scrape", "scenario"]}
