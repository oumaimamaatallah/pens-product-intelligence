from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/"app.py"


def test_catalog_dashboard_and_filter():
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    assert not app.exception
    initial=int(app.metric[0].value)
    app.multiselect(key="categories").set_value(["Pens"]).run()
    assert not app.exception
    assert 0 < int(app.metric[0].value) < initial


def test_empty_search_is_a_useful_empty_state():
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.text_input(key="query").set_value("thereisnosuchproduct").run()
    assert not app.exception
    assert any("No products match" in info.value for info in app.info)
