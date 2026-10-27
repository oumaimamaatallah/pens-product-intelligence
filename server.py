from datetime import date
from functools import lru_cache
import io
import json
import zipfile

from fastapi import FastAPI, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import pandas as pd

from analysis.data import ROOT, load_data, manifests, summary

app = FastAPI(title="Pens.com / Product notebook", docs_url="/api/docs")


@lru_cache(maxsize=1)
def dataset():
    return load_data()


def records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def selected_products(category="all", q="", rated=False, max_price: float | None = None):
    products, _ = dataset()
    selected = products.copy()
    if category != "all":
        selected = selected[selected.category.eq(category)]
    if q:
        selected = selected[selected.product_name.str.contains(q, case=False, regex=False) |
                            selected.sku.str.contains(q, case=False, regex=False)]
    if rated:
        selected = selected[selected.rating.notna()]
    if max_price is not None:
        selected = selected[selected.unit_price_low.le(max_price)]
    return selected


def product_records(frame):
    items = records(frame)
    for item in items:
        item["specifications"] = json.loads(item.pop("specifications_json", "{}"))
        item["tiers"] = json.loads(item.pop("price_tiers_json", "[]"))
        image = ROOT / "assets" / f"{item['sku']}.jpg"
        item["image"] = f"/product-images/{item['sku']}.jpg" if image.exists() else item.get("image_url", "")
    return items


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/catalog")
def catalog(category: str = "all", q: str = "", rated: bool = False,
            max_price: float | None = Query(default=None, ge=0)):
    full, _ = dataset()
    frame = selected_products(category, q, rated, max_price)
    groups = frame.groupby("category", as_index=False).agg(
        products=("sku", "size"), median=("unit_price_low", "median"),
        low=("unit_price_low", "min"), high=("unit_price_high", "max"))
    return {"products": product_records(frame), "count": len(frame), "total": len(full),
            "categories": sorted(full.category.unique()), "groups": records(groups),
            "median_price": float(frame.unit_price_low.median()) if len(frame) else None,
            "median_minimum": float(frame.minimum_order.median()) if len(frame) else None,
            "average_rating": float(frame.rating.mean()) if frame.rating.notna().any() else None,
            "snapshot": manifests()["scrape"]["observed_at"][:10], "currency": "USD"}


@app.get("/api/scenario")
def scenario(category: str = "all", q: str = "", start: date | None = None,
             end: date | None = None, channel: str = "all"):
    _, sales = dataset()
    frame = sales[sales.sku.isin(selected_products(category, q).sku)].copy()
    if start:
        frame = frame[frame.order_date.ge(pd.Timestamp(start))]
    if end:
        frame = frame[frame.order_date.le(pd.Timestamp(end))]
    if channel != "all":
        frame = frame[frame.channel.eq(channel)]
    monthly = frame.assign(month=frame.order_date.dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False)[["revenue", "gross_profit"]].sum()
    segments = frame.groupby("customer_segment", as_index=False).revenue.sum()
    return {"summary": summary(frame), "monthly": records(monthly), "segments": records(segments),
            "channels": sorted(sales.channel.unique()), "count": len(frame),
            "start": str(sales.order_date.min().date()), "end": str(sales.order_date.max().date())}


@app.get("/api/sources")
def sources():
    products, _ = dataset()
    return {**manifests(), "coverage": [
        {"field": field, "percent": float(products[field].replace("", pd.NA).notna().mean() * 100)}
        for field in ["rating", "minimum_order", "ship_days", "material", "imprint_process"]]}


@app.get("/api/export")
def export(category: str = "all", q: str = "", rated: bool = False,
           max_price: float | None = None):
    frame = selected_products(category, q, rated, max_price)
    return Response(frame.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="pens_catalog.csv"'})


@app.get("/api/powerbi")
def powerbi():
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in (ROOT / "powerbi").rglob("*"):
            if path.is_file() and ".pbi" not in path.parts:
                archive.write(path, str(path.relative_to(ROOT / "powerbi")))
    return Response(content.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="PensProductNotebook.zip"'})


app.mount("/product-images", StaticFiles(directory=ROOT / "assets"), name="product-images")
if (ROOT / "static/index.html").exists():
    app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="frontend")
