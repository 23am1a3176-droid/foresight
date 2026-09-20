from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORTS = PROJECT_ROOT / "reports"

INPUT_FILE = REPORTS / "weekly_sku_demand.csv"
OUTPUT_FILE = REPORTS / "backtest_results.csv"


# --------------------------------------------------
# WAPE calculation
# --------------------------------------------------

def calculate_wape(actual, predicted):

    actual = np.array(actual)
    predicted = np.array(predicted)

    denominator = np.sum(np.abs(actual))

    if denominator == 0:
        return 0.0

    return (
        np.sum(np.abs(actual - predicted))
        / denominator
        * 100
    )


# --------------------------------------------------
# Seasonal-naive forecast
# --------------------------------------------------

def seasonal_naive_forecast(history):

    if len(history) >= 4:
        return history.iloc[-4]

    return history.iloc[-1]


# --------------------------------------------------
# Random Forest prediction
# --------------------------------------------------

def random_forest_forecast(history):

    if len(history) < 5:
        return history.iloc[-1]

    values = history.reset_index(drop=True)

    rows = []

    for i in range(4, len(values)):

        rows.append({
            "Lag_1": values.iloc[i - 1],
            "Lag_2": values.iloc[i - 2],
            "Lag_4": values.iloc[i - 4],
            "Rolling_4": values.iloc[i - 4:i].mean(),
            "Target": values.iloc[i]
        })

    training = pd.DataFrame(rows)

    X = training[
        [
            "Lag_1",
            "Lag_2",
            "Lag_4",
            "Rolling_4"
        ]
    ]

    y = training["Target"]

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    latest_features = pd.DataFrame({
        "Lag_1": [values.iloc[-1]],
        "Lag_2": [values.iloc[-2]],
        "Lag_4": [values.iloc[-4]],
        "Rolling_4": [values.iloc[-4:].mean()]
    })

    prediction = model.predict(
        latest_features
    )[0]

    return max(0, prediction)


# --------------------------------------------------
# Rolling-origin backtesting
# --------------------------------------------------

def run_backtest():

    print("Loading weekly demand data...")

    data = pd.read_csv(INPUT_FILE)

    data["Week"] = pd.to_datetime(
        data["Week"]
    )

    data = data.sort_values(
        ["SKU", "Week"]
    ).reset_index(drop=True)


    results = []


    for sku in data["SKU"].unique():

        sku_data = data[
            data["SKU"] == sku
        ].sort_values("Week")

        demand = sku_data[
            "Units_Sold"
        ].reset_index(drop=True)


        if len(demand) < 8:
            continue


        # Use the last 4 observations
        # as rolling test points
        test_start = max(
            4,
            len(demand) - 4
        )


        for test_index in range(
            test_start,
            len(demand)
        ):

            history = demand[
                :test_index
            ]

            actual = demand[
                test_index
            ]


            # Seasonal-naive
            baseline_prediction = (
                seasonal_naive_forecast(
                    history
                )
            )


            # Random Forest
            ml_prediction = (
                random_forest_forecast(
                    history
                )
            )


            results.append({

                "SKU": sku,

                "Actual_Demand": float(
                    actual
                ),

                "Seasonal_Naive": float(
                    baseline_prediction
                ),

                "Random_Forest": float(
                    ml_prediction
                )
            })


    results_df = pd.DataFrame(results)


    # --------------------------------------------------
    # Calculate overall WAPE
    # --------------------------------------------------

    baseline_wape = calculate_wape(
        results_df["Actual_Demand"],
        results_df["Seasonal_Naive"]
    )

    random_forest_wape = calculate_wape(
        results_df["Actual_Demand"],
        results_df["Random_Forest"]
    )


    # --------------------------------------------------
    # Save detailed results
    # --------------------------------------------------

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print()
    print(
        "Rolling-origin backtesting completed."
    )

    print(
        f"Seasonal-Naive WAPE: "
        f"{baseline_wape:.2f}%"
    )

    print(
        f"Random Forest WAPE: "
        f"{random_forest_wape:.2f}%"
    )

    print(
        f"Results saved to: "
        f"{OUTPUT_FILE}"
    )


# --------------------------------------------------
# Run
# --------------------------------------------------python src/backtest.py

if __name__ == "__main__":
    run_backtest()