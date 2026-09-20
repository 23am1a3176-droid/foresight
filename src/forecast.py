from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORTS = PROJECT_ROOT / "reports"


# --------------------------------------------------
# Create Random Forest forecast
# --------------------------------------------------

def create_forecast():

    input_path = REPORTS / "weekly_sku_demand.csv"
    output_path = REPORTS / "forecast_results.csv"

    # Load weekly demand
    data = pd.read_csv(input_path)

    data["Week"] = pd.to_datetime(data["Week"])

    data = data.sort_values(
        ["SKU", "Week"]
    ).reset_index(drop=True)


    # --------------------------------------------------
    # Create forecasting features
    # --------------------------------------------------

    data["Lag_1"] = (
        data.groupby("SKU")["Units_Sold"]
        .shift(1)
    )

    data["Lag_2"] = (
        data.groupby("SKU")["Units_Sold"]
        .shift(2)
    )

    data["Lag_4"] = (
        data.groupby("SKU")["Units_Sold"]
        .shift(4)
    )

    data["Rolling_4_Week"] = (
        data.groupby("SKU")["Units_Sold"]
        .transform(
            lambda x:
            x.shift(1).rolling(4).mean()
        )
    )


    feature_columns = [
        "Lag_1",
        "Lag_2",
        "Lag_4",
        "Rolling_4_Week"
    ]


    # Remove rows where features are unavailable
    training_data = data.dropna(
        subset=feature_columns
    ).copy()


    # --------------------------------------------------
    # Train Random Forest
    # --------------------------------------------------

    X_train = training_data[feature_columns]

    y_train = training_data["Units_Sold"]


    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )


    # --------------------------------------------------
    # Generate one-week-ahead forecast
    # --------------------------------------------------

    forecasts = []


    for sku in data["SKU"].unique():

        sku_data = (
            data[data["SKU"] == sku]
            .sort_values("Week")
            .copy()
        )


        if len(sku_data) < 5:
            continue


        latest = sku_data.iloc[-1]

        lag_1 = sku_data["Units_Sold"].iloc[-1]

        lag_2 = sku_data["Units_Sold"].iloc[-2]

        lag_4 = sku_data["Units_Sold"].iloc[-4]

        rolling_4 = (
            sku_data["Units_Sold"]
            .tail(4)
            .mean()
        )


        X_future = pd.DataFrame({
            "Lag_1": [lag_1],
            "Lag_2": [lag_2],
            "Lag_4": [lag_4],
            "Rolling_4_Week": [rolling_4]
        })


        prediction = model.predict(
            X_future
        )[0]


        prediction = max(
            0,
            prediction
        )


        future_week = (
            latest["Week"]
            + pd.Timedelta(weeks=1)
        )


        forecasts.append({
            "SKU": sku,
            "Forecast_Week": future_week,
            "Forecast_Units": round(
                prediction,
                2
            )
        })


    # --------------------------------------------------
    # Save forecast
    # --------------------------------------------------

    forecast_results = pd.DataFrame(
        forecasts
    )


    forecast_results.to_csv(
        output_path,
        index=False
    )


    print(
        "Random Forest forecast created successfully."
    )

    print(
        f"Forecast file saved to: {output_path}"
    )

    print(
        f"Forecasted SKUs: {len(forecast_results)}"
    )


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    create_forecast()