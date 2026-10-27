import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis.data import ROOT, load_data, manifests, summary
from analysis.ui import BLUE, COLORS, chart, metrics, setup

setup()
st.markdown('<p class="eyebrow">PRODUCT NOTEBOOK / PENS.COM</p><div class="motion-rule"></div>', unsafe_allow_html=True)
st.title("What does the catalog tell us?")
st.caption("Public products, pricing and merchandising. A separate sales scenario shows how the same model could support a commercial team.")
try:
    products, sales = load_data()
    sources = manifests()
except (ValueError, FileNotFoundError) as error:
    st.error(f"The data could not be loaded: {error}")
    st.stop()

with st.sidebar:
    st.subheader("Product notebook")
    st.caption("Independent follow-up to my Pens.com internship.")
    st.divider()
    categories = st.multiselect("Product categories", sorted(products.category.unique()), default=sorted(products.category.unique()), key="categories")
    query = st.text_input("Find a product", placeholder="Try stylus, recycled, tote...", key="query")
    rated_only = st.checkbox("Only products with ratings", key="rated")
    st.divider()
    st.caption(f"US storefront / USD\n\nSnapshot: {sources['scrape']['observed_at'][:10]}")
    st.caption("A bounded catalog sample. Internal Pens.com sales data is not used.")

selected = products[products.category.isin(categories)].copy()
if query:
    selected = selected[selected.product_name.str.contains(query, case=False, regex=False)]
if rated_only:
    selected = selected[selected.rating.notna()]
if selected.empty:
    st.info("No products match. Clear the search or add a category.")
    st.stop()
metrics([
    ("Products in view", str(len(selected)), "Unique observed SKUs in this snapshot."),
    ("Median starting price", f"{selected.unit_price_low.median():.2f} USD", "Median of observed lowest advertised unit prices; bulk tiers differ."),
    ("Median minimum order", f"{selected.minimum_order.median():,.0f}", "Public minimum order quantities, in units."),
    ("Average rating", f"{selected.rating.mean():.1f} / 5" if selected.rating.notna().any() else "Not listed", "Unweighted mean across rated products, not across individual customer reviews."),
])
catalog_tab, scenario_tab, source_tab = st.tabs(["Catalog & pricing", "Sales scenario", "Sources & Power BI"])
with catalog_tab:
    left, right = st.columns([1.2,1])
    with left:
        categories_frame = selected.groupby("category", as_index=False).agg(products=("sku","size"), median_starting_price=("unit_price_low","median"))
        chart(px.bar(categories_frame, x="category", y="median_starting_price", color="category", color_discrete_sequence=COLORS, title="How entry prices compare").update_layout(showlegend=False,xaxis_title=None,yaxis_title="Median starting price / USD"), "prices")
    with right:
        plotted = selected[selected.rating.notna() & selected.minimum_order.notna()]
        chart(px.scatter(plotted, x="unit_price_low", y="rating", color="category", size="minimum_order", size_max=28,
                         hover_name="product_name", hover_data=["sku","review_count"], title="Price, rating and order size", color_discrete_sequence=COLORS).update_layout(xaxis_title="Starting unit price / USD",yaxis_title="Public product rating", legend={"orientation":"h","y":-.25}), "rating")
    st.subheader("The products behind the numbers")
    show = selected[["sku","product_name","category","unit_price_low","unit_price_high","minimum_order","rating","review_count","ship_days","material","product_url"]]
    st.dataframe(show, hide_index=True, width="stretch", height=320,
                 column_config={"product_url":st.column_config.LinkColumn("Source", display_text="View product"),
                                "unit_price_low":st.column_config.NumberColumn("From / USD",format="$%.2f"),
                                "unit_price_high":st.column_config.NumberColumn("To / USD",format="$%.2f")})
    st.download_button("Download selected products", selected.to_csv(index=False).encode(), "pens_catalog.csv","text/csv")
    with st.expander("Inspect one product"):
        sku = st.selectbox("SKU", selected.sku.tolist(), format_func=lambda value: f"{value} / {selected.set_index('sku').loc[value,'product_name']}")
        item = selected.set_index("sku").loc[sku]
        detail, specification = st.columns([1,2])
        with detail:
            thumbnail = ROOT / "assets" / f"{sku}.jpg"
            if thumbnail.exists():
                st.image(str(thumbnail), width=220)
            st.link_button("Open on Pens.com", item.product_url)
        with specification:
            st.json(json.loads(item.specifications_json))
            st.caption("Blank details mean they were not available in the snapshot.")

with scenario_tab:
    st.info("Simulated orders and assumed costs. These are not Pens.com sales, margins or customer records.")
    dates = st.date_input("Scenario dates", (sales.order_date.min().date(),sales.order_date.max().date()), key="scenario_dates")
    channel = st.selectbox("Sales channel", ["All"] + sorted(sales.channel.unique()), key="channel")
    view = sales[sales.sku.isin(selected.sku)].copy()
    if len(dates)==2:
        view = view[view.order_date.between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1]))]
    if channel != "All":
        view = view[view.channel.eq(channel)]
    totals = summary(view)
    metrics([
        ("Scenario net sales", f"{totals['revenue']:,.0f} USD", "Delivered order-line value. Tax, shipping and setup charges excluded."),
        ("Delivered orders", f"{totals['orders']:,}", "Distinct order IDs, not product lines."),
        ("Units delivered", f"{totals['units']:,}", "Delivered quantities in the current selection."),
        ("Assumed gross margin", f"{totals['margin']:.1%}", "Uses fictional unit costs, before overhead."),
    ])
    left,right = st.columns([1.4,1])
    with left:
        monthly = view.assign(month=view.order_date.dt.to_period("M").dt.to_timestamp()).groupby("month",as_index=False)[["revenue","gross_profit"]].sum()
        fig=go.Figure()
        for name,label,color in [("revenue","Scenario sales",BLUE),("gross_profit","Assumed gross profit","#0D938A")]:
            fig.add_trace(go.Scatter(x=monthly.month,y=monthly[name],name=label,mode="lines+markers",line={"color":color,"width":3}))
        chart(fig.update_layout(title="Seasonality in the scenario",yaxis_tickprefix="$",legend={"orientation":"h","y":-.2}),"sales")
    with right:
        segments=view.groupby("customer_segment",as_index=False).revenue.sum()
        chart(px.bar(segments,x="revenue",y="customer_segment",orientation="h",title="Which customer groups drive the scenario?",color_discrete_sequence=["#0D938A"]).update_layout(xaxis_title="Simulated USD",yaxis_title=None),"segments")
    st.download_button("Download scenario lines",view.to_csv(index=False).encode(),"simulated_sales.csv","text/csv")

with source_tab:
    st.subheader("What is observed, and what is assumed?")
    st.write("Product names, advertised price ranges, ratings, order minimums and page specifications come from public pages. Orders, quantities, channels, customer IDs and costs are generated separately.")
    coverage=pd.DataFrame([{"field":field,"present_pct":selected[field].replace("",pd.NA).notna().mean()*100} for field in ["rating","review_count","minimum_order","ship_days","material","imprint_process"]])
    chart(px.bar(coverage,x="field",y="present_pct",title="Field coverage in the selected catalog",color_discrete_sequence=[BLUE]).update_layout(yaxis_range=[0,100],yaxis_title="Products with a value / %",xaxis_title=None),"coverage")
    st.subheader("Open the Power BI report")
    st.write("Open powerbi/PensProductNotebook.pbip in Power BI Desktop, then select Refresh. It contains embedded snapshots, DAX measures and two report pages. No local path or account setup is needed.")
    st.download_button("Download the Power BI theme",(ROOT/"powerbi/theme.json").read_bytes(),"pens-theme.json","application/json")
    with st.expander("Capture log and scenario assumptions"):
        st.json(sources)
