from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA = PROJECT_ROOT / "data" / "raw"
REPORTS = PROJECT_ROOT / "reports"


def create_inventory_risk_report():
    inventory_path = RAW_DATA / "inventory_snapshots.csv"
    sku_master_path = RAW_DATA / "sku_master.csv"

    inventory = pd.read_csv(inventory_path)
    sku_master = pd.read_csv(sku_master_path)

    inventory["Snapshot_Date"] = pd.to_datetime(
        inventory["Snapshot_Date"]
    )

    # Keep only SKUs available in the project master file
    inventory = inventory[
        inventory["SKU"].isin(sku_master["SKU"])
    ].copy()

    # Use the latest inventory snapshot
    latest_date = inventory["Snapshot_Date"].max()

    latest_inventory = inventory[
        inventory["Snapshot_Date"] == latest_date
    ].copy()

    # Calculate average weekly demand from historical sales
    weekly_demand_path = REPORTS / "weekly_sku_demand.csv"
    weekly_demand = pd.read_csv(weekly_demand_path)

    average_demand = (
        weekly_demand
        .groupby("SKU")["Units_Sold"]
        .mean()
        .reset_index()
        .rename(columns={"Units_Sold": "Average_Weekly_Demand"})
    )

    risk_report = latest_inventory.merge(
        average_demand,
        on="SKU",
        how="left"
    )

    risk_report["Average_Weekly_Demand"] = (
        risk_report["Average_Weekly_Demand"].fillna(0)
    )

    # Estimate demand during lead time
    risk_report["Lead_Time_Demand"] = (
        risk_report["Average_Weekly_Demand"] / 7
        * risk_report["Lead_Time_Days"]
    )

    risk_report["Available_Stock"] = (
        risk_report["Current_Stock"]
        + risk_report["On_Order"]
    )

    # Stockout risk
    risk_report["Stockout_Risk"] = "Low"

    risk_report.loc[
        risk_report["Available_Stock"]
        < risk_report["Lead_Time_Demand"],
        "Stockout_Risk"
    ] = "High"

    risk_report.loc[
        (
            risk_report["Available_Stock"]
            >= risk_report["Lead_Time_Demand"]
        )
        &
        (
            risk_report["Available_Stock"]
            < risk_report["Lead_Time_Demand"]
            + risk_report["Safety_Stock"]
        ),
        "Stockout_Risk"
    ] = "Medium"

    # Overstock calculation
    risk_report["Target_Stock"] = (
        risk_report["Average_Weekly_Demand"] * 4
        + risk_report["Safety_Stock"]
    )

    risk_report["Excess_Units"] = (
        risk_report["Current_Stock"]
        - risk_report["Target_Stock"]
    ).clip(lower=0)

    risk_report["Excess_Inventory_Value"] = (
        risk_report["Excess_Units"]
        * risk_report["Inventory_Value"]
        / risk_report["Current_Stock"].replace(0, 1)
    )

    risk_report["Overstock_Risk"] = "Low"

    risk_report.loc[
        risk_report["Excess_Units"] > 0,
        "Overstock_Risk"
    ] = "High"

    # Recommended action
    risk_report["Recommended_Action"] = "Healthy"

    risk_report.loc[
        risk_report["Stockout_Risk"] == "High",
        "Recommended_Action"
    ] = "Reorder Now"

    risk_report.loc[
        (
            risk_report["Overstock_Risk"] == "High"
        )
        &
        (
            risk_report["Stockout_Risk"] != "High"
        ),
        "Recommended_Action"
    ] = "Review Markdown/Clearance"

    output_path = REPORTS / "inventory_risk_report.csv"

    risk_report.to_csv(
        output_path,
        index=False
    )

    print(f"Risk report saved to: {output_path}")


if __name__ == "__main__":
    create_inventory_risk_report()