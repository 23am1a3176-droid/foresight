# Project FORESIGHT — Demand & Inventory Intelligence

Client: NorthBay Living · Zidio Data Science Engagement

## Problem

NorthBay Living (a D2C home & lifestyle brand, ~50 actively sold SKUs) plans
inventory on gut feel. They stock out of best-sellers and sit on slow movers.
This project builds a weekly SKU-level demand forecast, a stockout/overstock
risk score, a planning dashboard, and a deployed scoring service.

## Data

Four raw extracts in `data/raw/`: `sales_daily.csv`, `sku_master.csv`,
`calendar.csv`, `inventory_snapshots.csv`. See
`reports/data_quality_report.md` for cleaning decisions — most importantly,
`inventory_snapshots.csv` contains 150 SKUs with no matching sales history or
product master record; these are excluded from forecasting and logged in
`data/processed/excluded_skus.csv`.

## Setup

```bash
pip install -r requirements.txt
```

## Run the pipeline

```bash
python src/pipeline.py
```

This ingests the four raw extracts and writes:
- `data/processed/sales_panel.csv` — analysis-ready daily SKU-level panel
- `data/processed/inventory_clean.csv` — cleaned monthly inventory snapshots
- `data/processed/excluded_skus.csv` — orphan inventory SKUs, documented not dropped
- `reports/data_quality_report.md` — full data-quality findings

## Status

- [x] D1 — Data pipeline
- [ ] D2 — EDA & data-quality memo
- [ ] D3 — Demand forecast model (baseline + backtested model)
- [ ] D4 — Risk scoring
- [ ] D5 — Planning dashboard
- [ ] D6 — Deployed scoring service
- [ ] D7 — Executive readout

## Repository structure

```
foresight/
  data/
    raw/            # the four original extracts
    processed/      # pipeline output (regenerated, not hand-edited)
  notebooks/        # 01_eda.ipynb, 02_baseline.ipynb, 03_model.ipynb
  src/
    pipeline.py     # ingest + clean + join (this is done)
    forecast.py      # model train / predict / backtest (next)
    risk.py           # stockout / overstock scoring (next)
  app/              # Streamlit dashboard
  service/          # FastAPI scoring endpoint
  reports/          # EDA memo, executive readout
```
### 8. Model Performance

The models were evaluated using WAPE
(Weighted Absolute Percentage Error).

The project used rolling-origin validation to compare
the Random Forest model with the Seasonal-Naive baseline.

The detailed validation results are available in:

- `reports/rolling_origin_validation.csv`
- `reports/average_model_performance.csv`

The average WAPE values should be taken directly from
`reports/average_model_performance.csv`.

> Note: Model performance may vary across validation periods.
> The reported values should be interpreted together with the
> validation results and project limitations.
"# foresight" 
