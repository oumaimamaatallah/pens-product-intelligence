"""Snapshot public Pens.com category and product pages, without logging in."""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.pens.com"
AGENT = "PortfolioCatalogResearch/1.0 (public product catalog)"
CATEGORIES = {
    "Pens": "/us/c/custom-pens",
    "Drinkware": "/us/c/promotional-custom-drinkware",
    "Bags": "/us/c/custom-bags",
    "Notebooks": "/us/c/custom-notebooks-journals",
}


def clean(value):
    return " ".join(str(value or "").replace("\u2014", " - ").replace("\ufffd", "").split())


def number(value):
    match = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match[0]) if match else None


def parse_category(html, category, source_url, observed_at):
    soup = BeautifulSoup(html, "html.parser")
    rows, seen = [], set()
    for card in soup.select("div.product-card"):
        anchor = card.select_one("a[data-sku][data-prod-name]")
        if not anchor or anchor["data-sku"] in seen:
            continue
        seen.add(anchor["data-sku"])
        price_node = card.select_one(".product-card-information__price")
        prices = re.findall(r"\d+(?:\.\d+)?", price_node.get_text() if price_node else "")
        low = float(prices[0]) if prices else number(anchor.get("data-product-price"))
        high = float(prices[-1]) if prices else number(anchor.get("data-product-price"))
        rating = card.select_one("[aria-label^='Average product rating']")
        reviews = card.select_one(".num-of-reviews")
        minimum = card.select_one(".minimum_quantity")
        shipping = card.select_one(".ship_msg")
        image = card.select_one("picture[data-src]")
        rows.append({
            "sku": anchor["data-sku"], "product_name": clean(anchor["data-prod-name"]),
            "category": category, "currency": "USD", "unit_price_low": low, "unit_price_high": high,
            "regular_price": number(anchor.get("data-product-default-price")),
            "minimum_order": int(number(minimum.get_text()) or 1) if minimum else None,
            "rating": number(rating.get("aria-label")) if rating else None,
            "review_count": int(number(reviews.get_text()) or 0) if reviews else None,
            "ship_days": int(number(shipping.get_text()) or 0) if shipping else None,
            "color_count": int(number(anchor.get("data-total-colors-count")) or 0),
            "colors": " | ".join(dict.fromkeys(clean(x.get("data-english-color")) for x in card.select("[data-english-color]"))),
            "product_url": urljoin(BASE, anchor["href"]), "image_url": image.get("data-src", "") if image else "",
            "source_url": source_url, "observed_at": observed_at, "data_origin": "scraped_public_catalog",
        })
    return rows


def parse_product(html):
    soup = BeautifulSoup(html, "html.parser")
    specs = {}
    for item in soup.select(".specification__item"):
        label, detail = item.select_one(".spec-title"), item.select_one(".spec-details")
        if label and detail:
            specs[clean(label.get_text()).rstrip(":")] = clean(detail.get_text(" "))
    tiers = []
    for choice in soup.select('input[name="product-quantity"][aria-label]'):
        label = choice.get("aria-label", "")
        match = re.search(r"Quantity\s+([\d,]+),\s*Unit Price\s*\$([\d,.]+)", label)
        if match:
            tiers.append({"quantity": int(match[1].replace(",", "")),
                          "unit_price": float(match[2].replace(",", ""))})
    for row in soup.select("tr"):
        text = clean(row.get_text(" "))
        if "$" not in text:
            continue
        quantities = re.findall(r"(?:^|\s)(\d[\d,]*)\s", text)
        prices = re.findall(r"\$([\d,]+\.\d{2})", text)
        if quantities and prices and not tiers:
            tiers.append({"quantity": int(quantities[0].replace(",", "")),
                          "unit_price": float(prices[-2 if len(prices) >= 2 else 0].replace(",", ""))})
    return {
        "material": specs.get("Material", ""), "imprint_process": specs.get("Imprint Process", ""),
        "ink_color": specs.get("Ink Color", ""),
        "specifications_json": json.dumps(specs, ensure_ascii=False),
        "price_tiers_json": json.dumps(tiers), "detail_scraped": bool(specs),
    }


def scrape(output, per_category=24, delay=1.1, details=True):
    output.mkdir(parents=True, exist_ok=True)
    parser = RobotFileParser()
    with urlopen(Request(BASE + "/robots.txt", headers={"User-Agent": AGENT}), timeout=30) as response:
        robots = response.read().decode("utf-8", errors="replace")
    parser.parse(robots.splitlines())
    fetched, errors, products = [], [], {}
    observed = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def fetch(url):
        if urlparse(url).netloc != "www.pens.com" or not parser.can_fetch(AGENT, url):
            raise ValueError(f"URL is outside the permitted public catalog: {url}")
        time.sleep(max(delay, 1))
        with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=35) as response:
            html = response.read().decode("utf-8", errors="replace")
        fetched.append({"url": url, "observed_at": observed})
        return html

    for category, path in CATEGORIES.items():
        url = BASE + path
        try:
            rows = parse_category(fetch(url), category, url, observed)[:per_category]
            if not rows:
                raise ValueError("No product cards found; the storefront markup may have changed")
            for row in rows:
                if row["sku"] in products:
                    continue
                row.update({"material": "", "imprint_process": "", "ink_color": "",
                            "specifications_json": "{}", "price_tiers_json": "[]", "detail_scraped": False})
                if details:
                    try:
                        row.update(parse_product(fetch(row["product_url"])))
                    except (HTTPError, OSError, ValueError) as error:
                        errors.append({"url": row["product_url"], "error": str(error)})
                products[row["sku"]] = row
            print(f"{category}: {len(rows)} product cards read", flush=True)
        except (HTTPError, OSError, ValueError) as error:
            errors.append({"url": url, "error": str(error)})
    if not products:
        raise RuntimeError("No pages could be parsed. Existing snapshots have not been replaced.")
    with (output / "products.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(next(iter(products.values()))), lineterminator="\n")
        writer.writeheader()
        writer.writerows(products.values())
    manifest = {"source": BASE + "/us/", "market": "US", "currency": "USD", "observed_at": observed,
                "scope": f"First {per_category} products from each of four public categories; not the full store",
                "products": len(products), "pages_fetched": fetched, "errors": errors,
                "missing_fields": "Left blank, never presented as scraped facts",
                "robots_checked": True, "request_delay_seconds": max(delay, 1)}
    (output / "scrape_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved {len(products)} products; {len(errors)} page errors", flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, default=ROOT / "data")
    cli.add_argument("--per-category", type=int, default=24)
    cli.add_argument("--delay", type=float, default=1.1)
    cli.add_argument("--skip-details", action="store_true")
    args = cli.parse_args()
    if not 1 <= args.per_category <= 100:
        cli.error("--per-category must be between 1 and 100")
    scrape(args.output, args.per_category, args.delay, not args.skip_details)
