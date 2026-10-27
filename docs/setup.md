# Setup

Use Python 3.11, 3.12 or 3.13 on Windows, macOS or Linux. On systems that call Python python3, use that name instead. From the extracted project folder, run python run.py. No activation command is needed.

The launcher creates .venv and installs requirements.txt on first use. Internet is needed for installation, then the bundled data works offline. Stop the app with Ctrl+C. Use python run.py --port 8502 if another app uses port 8501.

Direct dependencies: Streamlit 1.66.1, pandas 3.1.0, Plotly 7.1.0 and Beautiful Soup 4.15.0. Tests add pytest 9.1.1. All transitive dependencies and environment markers are pinned in the two requirements files. SQLite, CSV, HTTP requests and data generation use Python's standard library.

Manual setup is also supported:

    python -m venv .venv
    # Windows:
    .venv\Scripts\python -m pip install -r requirements.txt
    .venv\Scripts\python -m streamlit run app.py
    # macOS/Linux:
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python -m streamlit run app.py

## Refresh the snapshot

Inside the prepared environment:

    python scripts/scrape_catalog.py --per-category 24
    python scripts/generate_scenario.py
    python scripts/build_powerbi.py

The scraper checks robots.txt, stays on public US catalog pages and waits at least a second between requests. It records failed pages and leaves unavailable facts blank. It does not log in, buy anything, submit forms or scrape customer information. The default covers a bounded category sample, not every product in the store.

## Power BI

The native report needs Power BI Desktop on Windows. Open powerbi/PensProductNotebook.pbip and click Refresh once. Embedded Power Query snapshots make it portable. Public product facts and simulated sales are separate tables with a one-to-many SKU relationship. Import powerbi/theme.json under View > Themes if you want the browser dashboard's colors.

The browser app is the cross-platform alternative. Power BI Desktop is not required to run or test it.

## Docker

    docker build -t pens-notebook .
    docker run --rm -p 127.0.0.1:8501:8501 pens-notebook

The image runs as a non-root user and includes a health check. CI tests Windows, macOS and Linux, plus container startup. Share a source ZIP or grant repository access so an interviewer can run the same setup.
