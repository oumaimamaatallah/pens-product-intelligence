"""Cache public product thumbnails so the catalog also works offline."""
import csv
from pathlib import Path
import time
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
with (ROOT/"data/products.csv").open(encoding="utf-8") as handle:
    products=list(csv.DictReader(handle))
saved=0
for product in products:
    target=ROOT/"assets"/(product["sku"]+".jpg")
    if target.exists() or not product["image_url"]:
        continue
    time.sleep(.3)
    try:
        url=product["image_url"].replace("width=450","width=300").replace("height=450","height=300")
        with urlopen(Request(url,headers={"User-Agent":"PortfolioCatalogResearch/1.0"}),timeout=25) as response:
            target.write_bytes(response.read())
        saved+=1
    except OSError as error:
        print(product["sku"],str(error),flush=True)
print(f"Cached {saved} additional public thumbnails.")
