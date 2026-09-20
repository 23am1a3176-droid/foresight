from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS = PROJECT_ROOT / "reports"

RISK_FILE = REPORTS / "inventory_risk_report.csv"
FORECAST_FILE = REPORTS / "forecast_results.csv"


# Create API
app = FastAPI(
    title="Project FORESIGHT API",
    description="Demand forecasting and inventory risk scoring service",
    version="1.0.0"
)


# Load reports
def load_data():

    if not RISK_FILE.exists():
        raise FileNotFoundError(
            "inventory_risk_report.csv not found."
        )

    if not FORECAST_FILE.exists():
        raise FileNotFoundError(
            "forecast_results.csv not found."
        )

    risk = pd.read_csv(RISK_FILE)
    forecast = pd.read_csv(FORECAST_FILE)

    return risk, forecast


# Home endpoint
@app.get("/")
def home():

    return {
        "project": "FORESIGHT",
        "status": "API is running",
        "message": "Demand forecasting and inventory risk service"
    }


# SKU scoring endpoint
@app.get("/score/{sku}")
def score_sku(sku: str):

    risk, forecast = load_data()

    sku = sku.upper().strip()

    risk_row = risk[
        risk["SKU"].astype(str).str.upper() == sku
    ]

    forecast_row = forecast[
        forecast["SKU"].astype(str).str.upper() == sku
    ]

    # Invalid SKU
    if risk_row.empty:
        raise HTTPException(
            status_code=404,
            detail=f"SKU '{sku}' not found."
        )

    risk_data = risk_row.iloc[0]

    result = {
        "SKU": sku,
        "stockout_risk": risk_data.get(
            "Stockout_Risk",
            "Unknown"
        ),
        "overstock_risk": risk_data.get(
            "Overstock_Risk",
            "Unknown"
        ),
        "recommended_action": risk_data.get(
            "Recommended_Action",
            "Unknown"
        )
    }

    # Add forecast information
    if not forecast_row.empty:

        forecast_data = forecast_row.iloc[0]

        result["forecast_week"] = str(
            forecast_data.get(
                "Forecast_Week",
                ""
            )
        )

        result["forecast_units"] = float(
            forecast_data.get(
                "Forecast_Units",
                0
            )
        )

    else:

        result["forecast_week"] = None
        result["forecast_units"] = None

    return result