# Local API and CSV exports

Start the app with `python run.py`. The API uses the same bundled snapshot as the notebook; requests do not scrape the live store.

Open [interactive API documentation](http://localhost:8501/api/docs) to inspect response schemas and try requests.

| Endpoint | Result |
| --- | --- |
| `/health` | Local server status |
| `/api/catalog` | Products, captured specifications, quantity-price tiers and catalog summaries |
| `/api/scenario` | Aggregates from the separate fictional sales scenario |
| `/api/sources` | Capture metadata, scenario assumptions and field coverage |
| `/api/export` | Filtered product catalog as `pens_catalog.csv` |
| `/api/powerbi` | Portable native report as `PensProductNotebook.zip` |

## Find products

The catalog and CSV export accept the same filters:

| Parameter | Meaning | Example |
| --- | --- | --- |
| `q` | Case-insensitive text in the product name, SKU or material; surrounding spaces are ignored | `Metal` |
| `category` | Exact category name, or `all` | `Pens` |
| `rated` | Only include products with a captured public rating | `true` |
| `max_price` | Maximum captured starting unit price, in USD | `2` |

For example, view [metal pens with a starting price up to $2](http://localhost:8501/api/catalog?category=Pens&q=Metal&max_price=2), or [download the same selection as CSV](http://localhost:8501/api/export?category=Pens&q=Metal&max_price=2).

An empty search result is a valid response: the catalog contains an empty `products` list and the CSV retains its column headers. Prices describe the captured US catalog, not a current quote or a complete order total.

## Explore the sales scenario

`/api/scenario` accepts `category` and `q`, plus inclusive `start` and `end` dates in `YYYY-MM-DD` format and an exact `channel` value. Its unfiltered response lists the available channels and date range.

View [the first half of the fictional 2025 pens scenario](http://localhost:8501/api/scenario?category=Pens&start=2025-01-01&end=2025-06-30). These transactions are simulated and separate from observed product data. Revenue and margin summaries are not Pens.com business results.

The catalog's `rated` and `max_price` filters do not apply to scenario requests. Catalog sorting and pagination happen in the browser; the API and CSV return the full filtered selection in catalog order.
