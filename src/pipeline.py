from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA = PROJECT_ROOT / "data" / "raw"
REPORTS = PROJECT_ROOT / "reports"

REPORTS.mkdir(exist_ok=True)


def load_sales_data():
    sales_path = RAW_DATA / "sales_daily.csv"

    sales = pd.read_csv(sales_path)

    required_columns = [
        "Date",
        "SKU",
        "Units_Sold",
        "Revenue",
        "Price",
        "Promotion"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in sales.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    sales["Date"] = pd.to_datetime(
        sales["Date"],
        errors="coerce"
    )

    if sales["Date"].isna().any():
        raise ValueError("Invalid dates found in sales data.")

    if sales["Units_Sold"].isna().any():
        raise ValueError("Missing Units_Sold values found.")

    if (sales["Units_Sold"] < 0).any():
        raise ValueError("Negative Units_Sold values found.")

    print("Sales data validation completed.")

    return sales


def create_weekly_demand(sales):
    sales["Week"] = (
        sales["Date"]
        .dt.to_period("W")
        .dt.end_time
        .dt.normalize()
    )

    weekly_demand = (
        sales
        .groupby(["Week", "SKU"], as_index=False)["Units_Sold"]
        .sum()
        .sort_values(["SKU", "Week"])
    )

    # These are the lines you asked about
    output_path = REPORTS / "weekly_sku_demand.csv"

    weekly_demand.to_csv(
        output_path,
        index=False
    )

    print(f"Weekly demand file saved to: {output_path}")


def main():
    sales = load_sales_data()
    create_weekly_demand(sales)

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()

    print("\nRunning forecast generation...")
    import forecast
    forecast.create_forecast()

    print("\nRunning inventory risk analysis...")
    import risk
    risk.create_inventory_risk_report()

    print("\nAll pipeline steps completed successfully.")
        