"""Write a native PBIP report and an embedded import model."""

import base64
import json
from pathlib import Path
import sys
import uuid
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.data import ROOT, load_data

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def literal(value):
    if isinstance(value, bool):
        text = str(value).lower()
    elif isinstance(value, (float, int)):
        text = f"{value}D"
    else:
        text = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": text}}}


def projection(table, field, measure=False):
    return {"field": {"Measure" if measure else "Column": {
        "Expression": {"SourceRef": {"Entity": table}}, "Property": field}},
        "queryRef": table + "." + field, "nativeQueryRef": field, **({} if measure else {"active": True})}


def visual(page, name, kind, x, y, width, height, roles, title):
    value = {
        "$schema": SCHEMA + "item/report/definition/visualContainer/2.4.0/schema.json",
        "name": name, "position": {"x": x, "y": y, "z": 1000, "width": width, "height": height},
        "visual": {"visualType": kind, "query": {"queryState": {
            role: {"projections": bindings} for role, bindings in roles.items()}},
            "visualContainerObjects": {
                "title": [{"properties": {"show": literal(True), "text": literal(title), "fontSize": literal(12)}}],
                "background": [{"properties": {"show": literal(True), "color": {"solid": {"color": literal("#FFFFFF")}}, "transparency": literal(0)}}],
            },
            "drillFilterOtherVisuals": True,
        },
    }
    write(page / "visuals" / name / "visual.json", value)


def table(name, frame, types, measures=None):
    frame = frame[list(types)].copy()
    for column, data_type in types.items():
        if data_type == "dateTime":
            frame[column] = frame[column].dt.strftime("%Y-%m-%d")
    values = frame.to_json(orient="values", force_ascii=False)
    compressor = zlib.compressobj(wbits=-15)
    encoded = base64.b64encode(compressor.compress(values.encode()) + compressor.flush()).decode()
    m_types = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type date"}
    conversions = ", ".join('{"' + field + '", ' + m_types[kind] + '}' for field, kind in types.items())
    expression = [
        "let",
        f'    Rows = Json.Document(Binary.Decompress(Binary.FromText("{encoded}", BinaryEncoding.Base64), Compression.Deflate)),',
        "    Source = Table.FromRows(Rows, " + json.dumps(list(types)) .replace("[", "{").replace("]", "}") + "),",
        "    Typed = Table.TransformColumnTypes(Source, {" + conversions + '}, "en-US")',
        "in Typed",
    ]
    result = {"name": name, "lineageTag": str(uuid.uuid5(uuid.NAMESPACE_DNS, "pens." + name)),
              "columns": [{"name": field, "dataType": kind, "sourceColumn": field, "summarizeBy": "none"}
                          for field, kind in types.items()],
              "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": expression}}]}
    if measures:
        result["measures"] = [{"name": field, "expression": expression, "formatString": fmt}
                              for field, (expression, fmt) in measures.items()]
    return result


def build():
    products, sales = load_data()
    output = ROOT / "powerbi"
    report = output / "PensProductNotebook.Report"
    semantic = output / "PensProductNotebook.SemanticModel"
    write(output / "PensProductNotebook.pbip", {
        "$schema": SCHEMA + "pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": report.name}}],
        "settings": {"enableAutoRecovery": True}})
    write(report / "definition.pbir", {
        "$schema": SCHEMA + "item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": "../" + semantic.name}}})
    write(semantic / "definition.pbism", {
        "$schema": SCHEMA + "item/semanticModel/definitionProperties/1.0.0/schema.json", "version": "1.0",
        "settings": {"qnaEnabled": False}})
    product_measures = {
        "Products observed": ("DISTINCTCOUNT(Products[sku])", "#,0"),
        "Median starting price": ("MEDIAN(Products[unit_price_low])", "$#,0.00"),
        "Average product rating": ("AVERAGE(Products[rating])", "0.0"),
        "Median order minimum": ("MEDIAN(Products[minimum_order])", "#,0"),
    }
    sales_measures = {
        "Simulated net sales": ("SUM(Scenario[revenue])", "$#,0"),
        "Assumed gross profit": ("SUM(Scenario[gross_profit])", "$#,0"),
        "Assumed gross margin": ("DIVIDE([Assumed gross profit], [Simulated net sales], 0)", "0.0%"),
        "Delivered orders": ('CALCULATE(DISTINCTCOUNT(Scenario[order_id]), Scenario[status] = "delivered")', "#,0"),
        "Delivered units": ('CALCULATE(SUM(Scenario[units]), Scenario[status] = "delivered")', "#,0"),
    }
    product_types = {field: "string" for field in ["sku", "product_name", "category", "material", "imprint_process", "product_url", "observed_at", "data_origin"]}
    product_types.update({field: "double" for field in ["unit_price_low", "unit_price_high", "rating", "minimum_order", "review_count", "ship_days"]})
    sales_types = {field: "string" for field in ["line_id", "order_id", "sku", "customer_segment", "channel", "status", "data_origin"]}
    sales_types.update({"order_date": "dateTime", "units": "int64", "revenue": "double", "item_cost": "double", "gross_profit": "double"})
    write(semantic / "model.bim", {
        "name": "PensProductNotebook", "compatibilityLevel": 1600,
        "model": {"culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
                  "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
                  "tables": [table("Products", products, product_types, product_measures),
                             table("Scenario", sales, sales_types, sales_measures)],
                  "relationships": [{"name": "Scenario_Products", "fromTable": "Scenario", "fromColumn": "sku",
                                     "toTable": "Products", "toColumn": "sku", "crossFilteringBehavior": "oneDirection"}]}})
    write(report / "definition/version.json", {
        "$schema": SCHEMA + "item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write(report / "definition/report.json", {
        "$schema": SCHEMA + "item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {}, "settings": {"useStylableVisualContainerHeader": True}})
    write(report / "definition/pages/pages.json", {
        "$schema": SCHEMA + "item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": ["catalog", "scenario"], "activePageName": "catalog"})
    for key, label in [("catalog", "Observed catalog / public prices"), ("scenario", "Simulated sales / assumed costs")]:
        page = report / "definition/pages" / key
        write(page / "page.json", {
            "$schema": SCHEMA + "item/report/definition/page/2.0.0/schema.json",
            "name": key, "displayName": label, "displayOption": "FitToPage", "width": 1280, "height": 800,
            "objects": {"background": [{"properties": {"color": {"solid": {"color": literal("#F4F5F8")}}, "transparency": literal(0)}}]}})
        metrics = list(product_measures) if key == "catalog" else list(sales_measures)[:4]
        entity = "Products" if key == "catalog" else "Scenario"
        for i, metric in enumerate(metrics):
            visual(page, f"{key}_metric_{i}", "card", 24+i*310, 25, 290, 120,
                   {"Values": [projection(entity, metric, True)]}, metric)
        visual(page, f"{key}_slicer", "slicer", 24, 165, 1215, 70,
               {"Values": [projection("Products", "category")]}, "Product category")
        if key == "catalog":
            visual(page, "category_prices", "clusteredColumnChart", 24, 255, 600, 295,
                   {"Category": [projection("Products", "category")], "Y": [projection("Products", "Median starting price", True)]}, "Median starting price / USD")
            visual(page, "catalog_counts", "barChart", 645, 255, 595, 295,
                   {"Category": [projection("Products", "category")], "Y": [projection("Products", "Products observed", True)]}, "Observed products by category")
            visual(page, "product_table", "tableEx", 24, 570, 1215, 205,
                   {"Values": [projection("Products", col) for col in ["sku", "product_name", "category", "unit_price_low", "unit_price_high", "minimum_order", "rating"]]}, "Public catalog snapshot / USD / 27 October 2026")
        else:
            visual(page, "monthly_scenario", "lineChart", 24, 255, 740, 310,
                   {"Category": [projection("Scenario", "order_date")], "Y": [projection("Scenario", "Simulated net sales", True), projection("Scenario", "Assumed gross profit", True)]}, "Simulated sales and assumed profit")
            visual(page, "segment_scenario", "barChart", 785, 255, 455, 310,
                   {"Category": [projection("Scenario", "customer_segment")], "Y": [projection("Scenario", "Simulated net sales", True)]}, "Simulated sales by customer group")
            visual(page, "scenario_table", "tableEx", 24, 585, 1215, 190,
                   {"Values": [projection("Scenario", col) for col in ["order_id", "sku", "status", "units", "revenue", "item_cost"]]}, "Entirely simulated / not Pens.com internal sales")
    write(output / "theme.json", {
        "name": "Product notebook", "dataColors": ["#213DB7", "#0D938A", "#E4A848", "#9B9BC6", "#C97870"],
        "background": "#F4F5F8", "foreground": "#192442", "tableAccent": "#213DB7"})
    print(f"Wrote native Power BI project to {output}")


if __name__ == "__main__":
    build()
