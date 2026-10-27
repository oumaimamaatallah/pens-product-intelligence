# Sources and calculations

The public snapshot was captured from the [Pens.com US storefront](https://www.pens.com/us/). It covers the first category-page products in [pens](https://www.pens.com/us/c/custom-pens), [drinkware](https://www.pens.com/us/c/promotional-custom-drinkware), [bags](https://www.pens.com/us/c/custom-bags) and [notebooks](https://www.pens.com/us/c/custom-notebooks-journals). It is not an exhaustive or random sample.

data/products.csv has one row per SKU. It contains product name, category, advertised unit-price range, regular minimum-quantity price, order minimum, average rating, review count, shipping estimate, colors, material, ink color, printing process, page specifications, price tiers and image/source URLs. observed_at gives the capture time. Missing fields are blank; source metadata is never invented. Trademarks with broken source encoding are stripped, and long dashes are normalized.

Advertised lowest prices often require large quantities. unit_price_low and unit_price_high describe the displayed range, not an arbitrary order quote. Rating averages are unweighted across rated products. Shipping estimates depend on artwork approval and are not delivery promises. Product imagery remains Pens.com's; a few thumbnails are cached for this study.

## Sales scenario

data/scenario_orders.csv is generated with seed 83. It contains 1,600 fictional orders during 2025. Customer IDs, segments, channels, dates, volumes, statuses and costs are simulated. These rows are not reconstructed from the internship, and no business impact is claimed.

The scenario uses multiples of the public order minimum and interpolates unit prices within the observed range. Costs are assumed at 42-70% of scenario price. Prices captured later are used for an illustrative scenario, not as historical 2025 prices. Seasonal sampling weights are deliberate assumptions.

The SQL model joins order lines to the observed SKU table. Delivered revenue is units multiplied by scenario unit price; returned and cancelled lines produce zero revenue and cost. Gross profit subtracts assumed item cost. Gross margin is gross profit divided by delivered revenue, with zero for an empty denominator. Order counts use distinct delivered order IDs. Category filters measure selected-item spending within those orders.

Tax, setup fees, shipping, partial refunds, customer acquisition costs and overhead are outside the model. Review counts are not sales counts. The capture log and generation assumptions are included as JSON files.

## Native report

scripts/build_powerbi.py creates a Power BI project with embedded import snapshots, DAX measures, category filtering and two pages. Public catalog and simulated sales are visibly separated. Its JSON definitions are validated against Microsoft's published schemas, and the embedded model can be rebuilt from the CSV inputs.

This project is an independent follow-up to my Pens.com internship. It does not describe an assignment delivered for the company.
