import os
import streamlit as st
import pandas as pd
import plotly.express as px


# --------------------------------------------------
# 1. Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Project FORESIGHT",
    page_icon="📦",
    layout="wide"
)


# --------------------------------------------------
# 2. Application title
# --------------------------------------------------

st.title("📦 Project FORESIGHT")
st.subheader("AI-Powered Demand & Inventory Intelligence Platform")

st.write(
    "This dashboard helps identify demand forecasts, "
    "stockout risks, overstock risks, and recommended inventory actions."
)


# --------------------------------------------------
# 3. Load dashboard data
# --------------------------------------------------

@st.cache_data
def load_data():
    current_folder = os.path.dirname(__file__)

    file_path = os.path.join(
        current_folder,
        "..",
        "reports",
        "dashboard_data.csv"
    )

    data = pd.read_csv(file_path)

    return data


try:
    data = load_data()

except FileNotFoundError:
    st.error(
        "Dashboard data file was not found. "
        "Please check whether reports/dashboard_data.csv exists."
    )
    st.stop()


# --------------------------------------------------
# 4. Data preparation
# --------------------------------------------------

data["Estimated_Excess_Value"] = pd.to_numeric(
    data["Estimated_Excess_Value"],
    errors="coerce"
).fillna(0)

data["Current_Stock"] = pd.to_numeric(
    data["Current_Stock"],
    errors="coerce"
).fillna(0)

data["On_Order"] = pd.to_numeric(
    data["On_Order"],
    errors="coerce"
).fillna(0)

data["Actual_Demand"] = pd.to_numeric(
    data["Actual_Demand"],
    errors="coerce"
)

data["Random_Forest_Forecast"] = pd.to_numeric(
    data["Random_Forest_Forecast"],
    errors="coerce"
)

data["Seasonal_Naive_Forecast"] = pd.to_numeric(
    data["Seasonal_Naive_Forecast"],
    errors="coerce"
)


# --------------------------------------------------
# 5. Sidebar filters
# --------------------------------------------------

st.sidebar.header("🔎 Dashboard Filters")

category_options = ["All"] + sorted(
    data["Category"].dropna().unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "Select Category",
    category_options
)

sku_options = ["All"] + sorted(
    data["SKU"].dropna().unique().tolist()
)

selected_sku = st.sidebar.selectbox(
    "Select SKU",
    sku_options
)


# --------------------------------------------------
# 6. Apply filters
# --------------------------------------------------

filtered_data = data.copy()

if selected_category != "All":
    filtered_data = filtered_data[
        filtered_data["Category"] == selected_category
    ]

if selected_sku != "All":
    filtered_data = filtered_data[
        filtered_data["SKU"] == selected_sku
    ]


# --------------------------------------------------
# 7. Display summary metrics
# --------------------------------------------------

st.header("📊 Inventory Summary")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

total_skus = filtered_data["SKU"].nunique()

high_stockout_risk = (
    filtered_data["Stockout_Risk"] == "High"
).sum()

high_overstock_risk = (
    filtered_data["Overstock_Risk"] == "High"
).sum()

total_excess_value = filtered_data[
    "Estimated_Excess_Value"
].sum()


metric_col1.metric(
    "Total SKUs",
    total_skus
)

metric_col2.metric(
    "High Stockout Risk",
    high_stockout_risk
)

metric_col3.metric(
    "High Overstock Risk",
    high_overstock_risk
)

metric_col4.metric(
    "Estimated Excess Value",
    f"₹{total_excess_value:,.0f}"
)


st.divider()


# --------------------------------------------------
# 8. Risk summary charts
# --------------------------------------------------

st.header("⚠️ Risk Summary")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    stockout_counts = (
        filtered_data["Stockout_Risk"]
        .value_counts()
        .reset_index()
    )

    stockout_counts.columns = [
        "Risk_Level",
        "Count"
    ]

    stockout_chart = px.bar(
        stockout_counts,
        x="Risk_Level",
        y="Count",
        title="Stockout Risk Distribution",
        text="Count"
    )

    stockout_chart.update_layout(
        xaxis_title="Stockout Risk",
        yaxis_title="Number of SKUs"
    )

    st.plotly_chart(
        stockout_chart,
        use_container_width=True
    )


with chart_col2:
    overstock_counts = (
        filtered_data["Overstock_Risk"]
        .value_counts()
        .reset_index()
    )

    overstock_counts.columns = [
        "Risk_Level",
        "Count"
    ]

    overstock_chart = px.bar(
        overstock_counts,
        x="Risk_Level",
        y="Count",
        title="Overstock Risk Distribution",
        text="Count"
    )

    overstock_chart.update_layout(
        xaxis_title="Overstock Risk",
        yaxis_title="Number of SKUs"
    )

    st.plotly_chart(
        overstock_chart,
        use_container_width=True
    )


# --------------------------------------------------
# 9. Recommended actions
# --------------------------------------------------

st.header("🛠️ Recommended Actions")

action_counts = (
    filtered_data["Recommended_Action"]
    .value_counts()
    .reset_index()
)

action_counts.columns = [
    "Recommended_Action",
    "Count"
]

action_chart = px.pie(
    action_counts,
    names="Recommended_Action",
    values="Count",
    title="Recommended Action Distribution"
)

st.plotly_chart(
    action_chart,
    use_container_width=True
)


# --------------------------------------------------
# 10. Inventory risk table
# --------------------------------------------------

st.header("📋 Inventory Risk Details")

risk_columns = [
    "SKU",
    "Category",
    "Current_Stock",
    "On_Order",
    "Lead_Time_Days",
    "Stockout_Risk",
    "Overstock_Risk",
    "Recommended_Action",
    "Estimated_Excess_Value"
]

available_risk_columns = [
    column for column in risk_columns
    if column in filtered_data.columns
]

risk_table = filtered_data[
    available_risk_columns
].copy()

if "Estimated_Excess_Value" in risk_table.columns:
    risk_table["Estimated_Excess_Value"] = (
        risk_table["Estimated_Excess_Value"]
        .round(2)
    )

st.dataframe(
    risk_table,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 11. Forecast comparison
# --------------------------------------------------

st.header("📈 Demand Forecast Comparison")

forecast_columns = [
    "SKU",
    "Actual_Demand",
    "Random_Forest_Forecast",
    "Seasonal_Naive_Forecast"
]

available_forecast_columns = [
    column for column in forecast_columns
    if column in filtered_data.columns
]

forecast_data = filtered_data[
    available_forecast_columns
].copy()

if not forecast_data.empty:
    forecast_long = forecast_data.melt(
        id_vars=["SKU"],
        value_vars=[
            column for column in [
                "Actual_Demand",
                "Random_Forest_Forecast",
                "Seasonal_Naive_Forecast"
            ]
            if column in forecast_data.columns
        ],
        var_name="Forecast_Type",
        value_name="Demand"
    )

    forecast_chart = px.bar(
        forecast_long,
        x="SKU",
        y="Demand",
        color="Forecast_Type",
        barmode="group",
        title="Actual Demand vs Forecasted Demand"
    )

    forecast_chart.update_layout(
        xaxis_title="SKU",
        yaxis_title="Weekly Demand",
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        forecast_chart,
        use_container_width=True
    )

else:
    st.info(
        "No forecast data is available for the selected filters."
    )


# --------------------------------------------------
# 12. Priority action list
# --------------------------------------------------

st.header("🚨 Priority Inventory Actions")

priority_actions = [
    "Reorder Now",
    "Monitor Stockout Risk",
    "Review Markdown/Clearance",
    "Review Excess Stock"
]

priority_data = filtered_data[
    filtered_data["Recommended_Action"].isin(priority_actions)
].copy()

priority_data = priority_data.sort_values(
    by="Estimated_Excess_Value",
    ascending=False
)

priority_columns = [
    "SKU",
    "Category",
    "Recommended_Action",
    "Stockout_Risk",
    "Overstock_Risk",
    "Current_Stock",
    "On_Order",
    "Estimated_Excess_Value"
]

available_priority_columns = [
    column for column in priority_columns
    if column in priority_data.columns
]

if priority_data.empty:
    st.success(
        "No priority inventory actions found for the selected filters."
    )

else:
    st.dataframe(
        priority_data[available_priority_columns],
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 13. Download reports
# --------------------------------------------------

st.header("📥 Download Reports")

download_col1, download_col2, download_col3 = st.columns(3)

# Inventory risk report
risk_report_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "reports",
    "inventory_risk_report.csv"
)

if os.path.exists(risk_report_path):
    with open(risk_report_path, "rb") as file:
        download_col1.download_button(
            label="Download Risk Report",
            data=file,
            file_name="inventory_risk_report.csv",
            mime="text/csv"
        )

# Forecast results
forecast_report_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "reports",
    "forecast_results.csv"
)

if os.path.exists(forecast_report_path):
    with open(forecast_report_path, "rb") as file:
        download_col2.download_button(
            label="Download Forecast Results",
            data=file,
            file_name="forecast_results.csv",
            mime="text/csv"
        )

# Dashboard dataset
dashboard_report_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "reports",
    "dashboard_data.csv"
)

if os.path.exists(dashboard_report_path):
    with open(dashboard_report_path, "rb") as file:
        download_col3.download_button(
            label="Download Dashboard Data",
            data=file,
            file_name="dashboard_data.csv",
            mime="text/csv"
        )
        # --------------------------------------------------
# Top priority inventory items
# --------------------------------------------------

st.header("🚨 Top Priority Inventory Items")

priority_items = filtered_data[
    filtered_data["Recommended_Action"] != "Healthy"
].copy()

priority_items = priority_items.sort_values(
    by="Estimated_Excess_Value",
    ascending=False
)

priority_columns = [
    "SKU",
    "Category",
    "Recommended_Action",
    "Stockout_Risk",
    "Overstock_Risk",
    "Current_Stock",
    "On_Order",
    "Estimated_Excess_Value"
]

available_columns = [
    column for column in priority_columns
    if column in priority_items.columns
]

if priority_items.empty:
    st.success("No priority inventory items found.")

else:
    st.dataframe(
        priority_items[available_columns].head(10),
        use_container_width=True,
        hide_index=True
    )
        # --------------------------------------------------
# Model performance
# --------------------------------------------------

st.header("🎯 Model Performance")

st.write(
    "The model was evaluated using WAPE "
    "(Weighted Absolute Percentage Error)."
)

performance_col1, performance_col2 = st.columns(2)

performance_col1.metric(
    "Seasonal-Naive WAPE",
    "17.31%"
)

performance_col2.metric(
    "Random Forest WAPE",
    "15.47%"
)

st.info(
    "The Random Forest model performed better than the "
    "Seasonal-Naive baseline on the same test period."
)
# --------------------------------------------------
# Category-wise demand analysis
# --------------------------------------------------

st.header("📦 Category-wise Demand")

if "Category" in filtered_data.columns:
    category_demand = (
        filtered_data
        .groupby("Category", as_index=False)["Actual_Demand"]
        .sum()
        .sort_values("Actual_Demand", ascending=False)
    )

    category_chart = px.bar(
        category_demand,
        x="Category",
        y="Actual_Demand",
        title="Demand by Product Category",
        text="Actual_Demand"
    )

    category_chart.update_layout(
        xaxis_title="Product Category",
        yaxis_title="Total Actual Demand",
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        category_chart,
        use_container_width=True
    )

else:
    st.warning(
        "Category information is not available in the dashboard data."
    )