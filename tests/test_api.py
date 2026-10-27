import io
import zipfile
from fastapi.testclient import TestClient
from server import app

client=TestClient(app)


def test_catalog_dto_preserves_product_details_and_tiers():
    data=client.get("/api/catalog").json()
    assert data["count"]==93
    product=next(item for item in data["products"] if item["sku"]=="LNS")
    assert product["specifications"]["Material"]=="Metal"
    assert product["tiers"][0]=={"quantity":50,"unit_price":1.32}
    assert product["image"].startswith("/product-images/")


def test_catalog_search_empty_state_and_price_filter():
    assert client.get("/api/catalog",params={"q":"doesnotexist"}).json()["count"]==0
    data=client.get("/api/catalog",params={"category":"Pens","max_price":1}).json()
    assert data["count"]>0
    assert all(item["category"]=="Pens" and item["unit_price_low"]<=1 for item in data["products"])


def test_native_report_download_contains_portable_model():
    response=client.get("/api/powerbi")
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "PensProductNotebook.pbip" in archive.namelist()
        assert any(name.endswith("model.bim") for name in archive.namelist())
        assert not any(".pbi/" in name for name in archive.namelist())


def test_scenario_is_separate_and_filterable():
    all_data=client.get("/api/scenario").json()
    pens=client.get("/api/scenario",params={"category":"Pens"}).json()
    assert 0 < pens["summary"]["revenue"] < all_data["summary"]["revenue"]
    sources=client.get("/api/sources").json()
    assert "simulated" in sources["scenario"]["source"].lower()
    assert client.get("/health").json()["status"]=="ok"
    assert client.get("/").status_code==200
