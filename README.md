# Pens.com product notebook

A catalog study inspired by my internship at Pens.com. It combines public product pages with a separate, fictional sales scenario to explore pricing, order sizes and product mix.

![Product dashboard](docs/dashboard.png)

## Run

Python 3.11-3.13:

    python run.py

Open http://localhost:8501. The first run creates an environment and installs the pinned dependencies.

    python run.py --test
    python run.py --export

## Power BI

Open powerbi/PensProductNotebook.pbip in Power BI Desktop and select **Refresh**. The source snapshots are embedded, so there are no file paths to change. The report has separate pages for observed catalog facts and simulated sales.

The snapshot contains 93 products from four US-storefront categories. Prices, ratings and specifications were scraped; orders and costs are simulated. This is an independent portfolio project, not an internal Pens.com report.

[Setup and dependencies](docs/setup.md) / [Sources and calculations](docs/model.md)

[Watch the walkthrough](docs/demo.gif)
