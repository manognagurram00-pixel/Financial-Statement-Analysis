import pandas as pd


# Load Raw Data

df = pd.read_excel("FS.xlsx", header=None)

# Extracting Profit & Loss Section

pl_start = df[df[0] == "PROFIT & LOSS"].index[0]
pl_df = df.iloc[pl_start:]

# for proper column headers
pl_df.columns = pl_df.iloc[1]
pl_df = pl_df.iloc[2:]

# Rename first column
pl_df = pl_df.rename(columns={pl_df.columns[0]: "Metric"})

# Remove unwanted rows
pl_df = pl_df[pl_df["Metric"] != "Report Date"]

# Reshaping Data 

pl_long = pl_df.melt(
    id_vars="Metric",
    var_name="Year",
    value_name="Value"
)

# Converting Year to proper format
pl_long["Year"] = pd.to_datetime(pl_long["Year"]).dt.year

# Extracting Key Metrics

sales_df = pl_long[pl_long["Metric"] == "Sales"]
profit_df = pl_long[pl_long["Metric"] == "Net profit"]
raw_cost_df = pl_long[pl_long["Metric"] == "Raw Material Cost"]
interest_df = pl_long[pl_long["Metric"] == "Interest"]
pbt_df = pl_long[pl_long["Metric"] == "Profit before tax"]

# Merge & Calculate Metrics

merged_df = pd.merge(
    sales_df[["Year", "Value"]],
    profit_df[["Year", "Value"]],
    on="Year",
    suffixes=("_Sales", "_Profit")
)

merged_df = pd.merge(
    merged_df,
    raw_cost_df[["Year", "Value"]],
    on="Year",
    how="left"
)

merged_df = merged_df.rename(columns={"Value": "Raw_Material_Cost"})

merged_df = pd.merge(
    merged_df,
    interest_df[["Year", "Value"]].rename(columns={"Value": "Interest"}),
    on="Year",
    how="left"
)

merged_df = pd.merge(
    merged_df,
    pbt_df[["Year", "Value"]].rename(columns={"Value": "PBT"}),
    on="Year",
    how="left"
)

# Profit Margin
merged_df["Profit_Margin"] = (
    merged_df["Value_Profit"] / merged_df["Value_Sales"]
)

# Cost Ratio 
merged_df["Cost_Ratio"] = (
    merged_df["Value_Sales"] - merged_df["Value_Profit"]
) / merged_df["Value_Sales"]


# Gross Profit
merged_df["Gross_Profit"] = (
    merged_df["Value_Sales"] - merged_df["Raw_Material_Cost"]
)

# Gross Profit Margin
merged_df["Gross_Profit_Margin"] = (
    merged_df["Gross_Profit"] / merged_df["Value_Sales"]
)

# Interest Coverage Ratio
merged_df["Interest_Coverage"] = merged_df["PBT"] / merged_df["Interest"]


# Remove duplicates (due to extra data like quarters)
merged_df = merged_df.drop_duplicates(subset=["Year"])

# Sort by Year
merged_df = merged_df.sort_values(by="Year")

# Revenue Growth
merged_df["Revenue_Growth"] = merged_df["Value_Sales"].pct_change()

# Generating Business Insights
def generate_insight(row):
    if row["Cost_Ratio"] > 0.8:
        return "High cost structure"
    elif row["Profit_Margin"] < 0.2:
        return "Low profitability"
    elif row["Revenue_Growth"] < 0:
        return "Revenue declining"
    elif row["Profit_Margin"] > 0.3:
        return "Strong performance"
    else:
        return "Stable"

merged_df["Insight"] = merged_df.apply(generate_insight, axis=1)


# Final Output
print(merged_df)


# visual 
import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()

# Revenue
ax1.plot(
    merged_df["Year"],
    merged_df["Value_Sales"],
    marker='o',
    linewidth=2,
    color='tab:blue'
)
ax1.set_xlabel("Year")
ax1.set_ylabel("Revenue", color='tab:blue')
ax1.tick_params(axis='y', labelcolor='tab:blue')

# Profit Margin
ax2 = ax1.twinx()
ax2.plot(
    merged_df["Year"],
    merged_df["Profit_Margin"],
    marker='o',
    linewidth=2,
    linestyle='--',
    color='tab:orange'
)
ax2.set_ylabel("Profit Margin", color='tab:orange')
ax2.tick_params(axis='y', labelcolor='tab:orange')

plt.title("Revenue vs Profit Margin Trend")
ax1.grid(alpha=0.3)

plt.show()

# save o/p file

merged_df.to_csv("financial_analysis_output.csv", index=False)


