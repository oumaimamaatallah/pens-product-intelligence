import base64
import json
import re
import zlib

import pandas as pd
import pytest

from analysis.data import ROOT, load_data, summary
from scripts.scrape_catalog import clean, parse_category, parse_product


def test_public_card_parser_keeps_fact_provenance():
    html = """<div class="product-card"><a data-sku="ABC" data-prod-name="Sample pen"
    data-product-default-price="2.00" data-total-colors-count="3" href="/us/p/sample/prd-abc/"></a>
    <div class="product-card-information__price">$0.90-1.32</div>
    <div aria-label="Average product rating: 4.6"></div><div class="num-of-reviews">4,132</div>
    <div class="minimum_quantity">Order as few as 50</div><div class="ship_msg">Ships within 4 business days</div></div>"""
    row = parse_category(html, "Pens", "https://www.pens.com/us/c/custom-pens", "2026-10-27")[0]
    assert row["unit_price_low"] == .9
    assert row["unit_price_high"] == 1.32
    assert row["rating"] == 4.6
    assert row["review_count"] == 4132
    assert row["minimum_order"] == 50
    assert row["data_origin"] == "scraped_public_catalog"


def test_tiers_are_unit_prices_not_order_subtotals():
    result = parse_product("""<input name="product-quantity" aria-label="Quantity 50,Unit Price $1.32,Subtotal$66.00">
    <input name="product-quantity" aria-label="Quantity 100,Unit Price $1.29,Subtotal$129.00">""")
    assert json.loads(result["price_tiers_json"]) == [{"quantity": 50, "unit_price": 1.32}, {"quantity": 100, "unit_price": 1.29}]


def test_missing_fields_are_not_fabricated():
    row = parse_category('<div class="product-card"><a data-sku="X" data-prod-name="X" href="/us/p/x/"></a></div>', "Pens", "url", "date")[0]
    assert row["rating"] is None
    assert row["minimum_order"] is None
    assert parse_product("<html></html>")["material"] == ""
    assert clean("one\u2014two") == "one - two"


def test_distinct_order_math_excludes_returns():
    lines = pd.DataFrame({"status": ["delivered","delivered","returned","cancelled"],
                          "order_id":["A","A","B","C"],"revenue":[100,50,0,0],
                          "gross_profit":[40,20,0,0],"units":[100,50,20,10]})
    result = summary(lines)
    assert result["orders"] == 1
    assert result["revenue"] == 150
    assert result["aov"] == 150
    assert result["margin"] == .4


def test_real_catalog_and_scenario_have_separate_origins():
    products, sales = load_data()
    assert products.data_origin.eq("scraped_public_catalog").all()
    assert sales.data_origin.eq("simulated_sales").all()
    assert products.product_url.str.startswith("https://www.pens.com/us/p/").all()
    assert len(sales) == len(pd.read_csv(ROOT/"data/scenario_orders.csv"))
    assert sales.groupby("order_id").customer_id.nunique().eq(1).all()


def test_power_bi_embedded_model_is_portable_and_matches_source():
    path = ROOT/"powerbi/PensProductNotebook.SemanticModel/model.bim"
    model = json.loads(path.read_text())["model"]
    products, sales = load_data()
    for table, expected in zip(model["tables"],[len(products),len(sales)]):
        expression = "\n".join(table["partitions"][0]["source"]["expression"])
        encoded = re.search(r'Binary.FromText\("([^"]+)"',expression)[1]
        rows = json.loads(zlib.decompress(base64.b64decode(encoded),wbits=-15))
        assert len(rows)==expected
        assert "File.Contents" not in expression
    assert model["relationships"][0]["toColumn"]=="sku"
