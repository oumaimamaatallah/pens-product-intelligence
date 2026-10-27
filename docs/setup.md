# Setup

Use Python 3.11, 3.12 or 3.13 and a modern browser on Windows, macOS or Linux. From this folder:

    python run.py

Use python3 if that is your installed command name. The launcher creates .venv, installs the pinned requirements on first use and starts the local server at http://localhost:8501. Internet is required for installation; the bundled dataset and frontend then work offline. No activation command is needed. Stop with Ctrl+C.

Use python run.py --port 8502 to run another project at the same time. python run.py --test runs the Python tests; python run.py --export creates the analysis exports.

## Dependencies

The backend uses FastAPI 0.162.0, Uvicorn 0.54.0 and pandas 3.1.0. The exact direct requirements are in requirements.in; requirements.txt pins the complete runtime dependency tree. Test dependencies are pinned in requirements-dev.txt.

The frontend uses React 19.3.1, Vite 8.3.5, Tailwind CSS 4.3.3, shadcn/ui components with Radix UI primitives, Lucide icons and Recharts 3.10.1. web/package.json lists the exact package versions and web/package-lock.json locks the full tree.

## Frontend development

Node.js 24 LTS is needed only to edit or rebuild the React interface. Start the Python app in one terminal, then:

    cd web
    npm ci
    npm run dev

The Vite server proxies API calls to the Python app on port 8501. To rebuild the bundled interface:

    npm run build

The output is written to static/ and is included in the repository and source ZIP. Commit source and bundle updates together.

## Tests

Python tests check the data model and API. Playwright tests exercise desktop and mobile interactions and run axe accessibility checks. To run browser tests with the local app already serving on port 8501:

    cd web
    npm ci
    npx playwright install chromium

Set PLAYWRIGHT_BASE_URL to http://localhost:8501, then run npm test. Without that variable, Playwright starts a server using the Python command on PATH; APP_PYTHON can point to the project's virtual-environment Python. CI installs the Python environment and browser automatically.

## Docker

    docker build -t local-analysis .
    docker run --rm -p 127.0.0.1:8501:8501 local-analysis

The multi-stage build compiles the frontend with Node.js, then serves it with Python as a non-root user. Node.js is not part of the runtime image. CI checks Windows, macOS, Linux, browser interactions and container startup.

## Product data and Power BI

Beautiful Soup 4.15.0 is the extra Python dependency for public-page extraction. Product thumbnails are cached locally; the source URLs remain in the catalog. No API key is required.

To rebuild the observed snapshot and its scenario, use the virtual-environment Python:

    python scripts/scrape_catalog.py --per-category 24
    python scripts/cache_product_images.py
    python scripts/generate_scenario.py
    python scripts/build_powerbi.py

The scraper checks robots.txt, reads public catalog pages and waits between requests. Failed pages are logged; unavailable facts stay blank. The default is a bounded sample, not the whole store.

The native report requires Power BI Desktop on Windows. Download its ZIP from the app or open powerbi/PensProductNotebook.pbip and select Refresh. Its import snapshots are embedded, so no source paths need changing. The React app is the cross-platform alternative.
