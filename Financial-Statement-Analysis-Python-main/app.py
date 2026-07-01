import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import IsolationForest

# Page Config
st.set_page_config(page_title="Financial Statement Analysis", layout="wide")

# Load Data
df = pd.read_csv("financial_analysis_output.csv")
df = df.sort_values("Year").reset_index(drop=True)

# Forecast Function
def build_forecast(data, value_column, future_periods=3):
    data = data.sort_values("Year").copy()

    X = data["Year"].values.reshape(-1, 1)
    y = data[value_column].values

    future_years = np.arange(
        data["Year"].max() + 1,
        data["Year"].max() + future_periods + 1
    ).reshape(-1, 1)

    if len(data) >= 4:
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)
        future_poly = poly.transform(future_years)

        model = LinearRegression()
        model.fit(X_poly, y)
        preds = model.predict(future_poly)
    else:
        model = LinearRegression()
        model.fit(X, y)
        preds = model.predict(future_years)

    return pd.DataFrame({
        "Year": future_years.flatten(),
        f"Forecast_{value_column}": preds
    })

st.title("Financial Statement Analysis")

# Filter
years = sorted(df["Year"].unique())
selected_years = st.multiselect("Select Year(s)", options=years, default=years)

df_filtered = df[df["Year"].isin(selected_years)].sort_values("Year").reset_index(drop=True)

if len(df_filtered) < 2:
    st.warning("Please select at least 2 years")
    st.stop()

# KPI's
latest = df_filtered.iloc[-1]
previous = df_filtered.iloc[-2]

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Revenue",
    f"{latest['Value_Sales']:,.0f}",
    f"{((latest['Value_Sales'] - previous['Value_Sales']) / previous['Value_Sales']):.2%}"
)

col2.metric("Profit Margin",
    f"{latest['Profit_Margin']:.2%}",
    f"{(latest['Profit_Margin'] - previous['Profit_Margin']):.2%}"
)

col3.metric("Revenue Growth",
    f"{latest['Revenue_Growth']:.2%}" if pd.notna(latest["Revenue_Growth"]) else "N/A"
)

col4.metric("Cost Ratio",
    f"{latest['Cost_Ratio']:.2%}",
    f"{(latest['Cost_Ratio'] - previous['Cost_Ratio']):.2%}"
)

col5.metric("Gross Margin",
    f"{latest['Gross_Profit_Margin']:.2%}",
    f"{(latest['Gross_Profit_Margin'] - previous['Gross_Profit_Margin']):.2%}"
)

col6.metric("Interest Coverage",
    f"{latest['Interest_Coverage']:.2f}",
    f"{(latest['Interest_Coverage'] - previous['Interest_Coverage']):.2f}"
)

# Table
st.subheader("Historical Financial Data")
st.dataframe(df_filtered, use_container_width=True)

# Forecast
revenue_forecast = build_forecast(df_filtered, "Value_Sales", 3)
margin_forecast = build_forecast(df_filtered, "Profit_Margin", 3)
forecast_df = revenue_forecast.merge(margin_forecast, on="Year")

# Chart 1
st.subheader("Revenue and Profit Margin with Forecast")

fig, ax1 = plt.subplots(figsize=(11, 5))

ax1.plot(df_filtered["Year"], df_filtered["Value_Sales"], marker="o", linewidth=2, color="tab:blue")
ax1.plot(forecast_df["Year"], forecast_df["Forecast_Value_Sales"], linestyle="dotted", marker="o", color="tab:blue")

ax2 = ax1.twinx()
ax2.plot(df_filtered["Year"], df_filtered["Profit_Margin"], linestyle="--", marker="o", color="tab:orange")
ax2.plot(forecast_df["Year"], forecast_df["Forecast_Profit_Margin"], linestyle="dotted", marker="o", color="tab:orange")

ax1.grid(alpha=0.3)
st.pyplot(fig)

# Chart 2 - Risk
st.subheader("Interest Coverage Risk Analysis")

fig2, ax = plt.subplots(figsize=(10, 4))
ax.plot(df_filtered["Year"], df_filtered["Interest_Coverage"], marker="o", linewidth=2, color="tab:orange")
ax.axhline(1.5, linestyle="--")
ax.axhline(3, linestyle="--")
ax.grid(alpha=0.3)

st.pyplot(fig2)

#ARIMA

st.subheader("Revenue Forecast Comparison (Regression vs ARIMA)")

try:
    model = ARIMA(df_filtered["Value_Sales"], order=(1,1,1))
    model_fit = model.fit()
    arima_vals = model_fit.forecast(steps=3)

    future_years = np.arange(df_filtered["Year"].max()+1, df_filtered["Year"].max()+4)

    fig3, ax = plt.subplots(figsize=(11, 5))

    ax.plot(df_filtered["Year"], df_filtered["Value_Sales"], marker="o", color="tab:blue", label="Actual")
    ax.plot(forecast_df["Year"], forecast_df["Forecast_Value_Sales"], linestyle="dotted", color="tab:blue", label="Regression")
    ax.plot(future_years, arima_vals, linestyle="--", color="tab:orange", label="ARIMA")

    ax.legend()
    ax.grid(alpha=0.3)

    st.pyplot(fig3)

except:
    st.warning("ARIMA not available")

#Anomaly Detection

st.subheader("Anomaly Detection")

features = df_filtered[["Value_Sales","Profit_Margin","Cost_Ratio","Interest_Coverage"]].fillna(0)

model = IsolationForest(contamination=0.2, random_state=42)
df_filtered["Anomaly"] = model.fit_predict(features)

fig4, ax = plt.subplots(figsize=(10, 4))

ax.scatter(df_filtered["Year"], df_filtered["Value_Sales"], c=df_filtered["Anomaly"])
ax.set_title("Anomaly Detection on Revenue")
ax.grid(alpha=0.3)

st.pyplot(fig4)

#What if analysis

st.subheader("What-If Scenario")

rev_change = st.slider("Revenue Change %", -50, 50, 0)
cost_change = st.slider("Cost Change %", -50, 50, 0)

scenario = latest.copy()

new_rev = scenario["Value_Sales"] * (1 + rev_change/100)
new_cost = scenario["Cost_Ratio"] * (1 + cost_change/100)

new_margin = (new_rev * (1 - new_cost)) / new_rev

st.write(f"Adjusted Revenue: {new_rev:,.0f}")
st.write(f"Adjusted Profit Margin: {new_margin:.2%}")

#Summary

st.subheader("Analysis")

analysis = pd.DataFrame([
    ["Trend", "Revenue increasing" if latest["Value_Sales"]>df_filtered.iloc[0]["Value_Sales"] else "Declining"],
    ["Risk", "Low risk" if latest["Interest_Coverage"]>3 else "High risk"],
    ["Recommendation", "Optimize cost" if latest["Cost_Ratio"]>0.7 else "Maintain strategy"]
], columns=["Area","Insight"])

st.dataframe(analysis, use_container_width=True)