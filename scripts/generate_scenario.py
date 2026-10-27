"""Build fictional wholesale orders around observed catalog prices."""

import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def generate(directory=ROOT / "data", seed=83, orders=1600):
    with (directory / "products.csv").open(encoding="utf-8") as handle:
        products = list(csv.DictReader(handle))
    usable = [p for p in products if p["unit_price_low"] and p["unit_price_high"]]
    if not usable:
        raise ValueError("No products have an observed price range")
    rng = random.Random(seed)
    rows = []
    for index in range(1, orders + 1):
        month = rng.choices(range(1, 13), [6, 7, 9, 11, 12, 10, 8, 8, 13, 15, 12, 9])[0]
        order_date = date(2025, month, 1) + timedelta(days=rng.randrange(28))
        status = rng.choices(["delivered", "returned", "cancelled"], [91, 5, 4])[0]
        segment = rng.choice(["Small business", "Education", "Events", "Hospitality", "Professional services"])
        customer_id = f"B{rng.randrange(1, 401):04d}"
        for product in rng.sample(usable, rng.choice([1, 1, 2, 3])):
            minimum = int(float(product["minimum_order"] or 50))
            units = minimum * rng.choice([1, 2, 3, 5, 10])
            low, high = float(product["unit_price_low"]), float(product["unit_price_high"])
            # A scenario interpolates a volume price; this is not an observed quote.
            unit_price = round(high - (high - low) * min((units / minimum - 1) / 9, 1), 2)
            cost = round(unit_price * rng.uniform(.42, .7), 2)
            rows.append({"line_id": f"L{len(rows)+1:05d}", "order_id": f"SIM-{index:05d}",
                         "order_date": order_date.isoformat(), "sku": product["sku"],
                         "customer_id": customer_id, "customer_segment": segment,
                         "channel": rng.choice(["Website", "Account manager", "Reorder email"]),
                         "status": status, "units": units, "unit_price": unit_price,
                         "assumed_unit_cost": cost, "data_origin": "simulated_sales"})
    with (directory / "scenario_orders.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (directory / "scenario_manifest.json").write_text(json.dumps({
        "seed": seed, "orders": orders, "lines": len(rows), "period": "2025-01 to 2025-12",
        "source": "Entirely simulated, not Pens.com internal data",
        "assumptions": ["Seasonal sampling weights", "Order quantities are multiples of public minimums",
                        "Prices interpolated inside the observed public range", "Unit cost is 42-70% of scenario price",
                        "Full returns only; no tax, shipping, setup charges or overhead"]
    }, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} simulated order lines")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--seed", type=int, default=83)
    args = cli.parse_args()
    generate(seed=args.seed)
