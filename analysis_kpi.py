import pandas as pd
import streamlit as st
import plotly.express as px

# ─── Page Config & Theme CSS ────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Orderlines Data Analysis Tool")


# ---- STREAMLIT APP ---- #
st.title("🔍 Orderlines Data Analysis Tool")

# Step 1: Upload the OrderLines CSV file
uploaded_file = st.sidebar.file_uploader("Upload your OrderLines CSV", type=["csv"])
if not uploaded_file:
    st.sidebar.info("Please upload a CSV to start.")
    st.stop()

df = pd.read_csv(uploaded_file)
st.subheader("📊 Preview of Uploaded Data")
st.dataframe(df.head())

# Detect and parse the date column
possible_date_columns = ['CreatedDate', 'OrderDate', 'Date', 'InvoiceCreationDate', 'InvoiceDate']
date_column = next((c for c in possible_date_columns if c in df.columns), None)
if date_column:
    df['CreatedDate'] = pd.to_datetime(df[date_column])
    st.write(f"Using '{date_column}' as the date column.")
else:
    st.error("The dataset does not contain a recognized date column!")
    st.stop()

# ─── Further Data Filtering ────────────────────────────────
st.subheader("Further Data Filtering")
filter_columns = [c for c in df.columns if c != date_column]
chosen_col = st.selectbox("Choose a column to filter by:", filter_columns)
if chosen_col:
    unique_vals = df[chosen_col].dropna().unique().tolist()
    selected_vals = st.multiselect(f"Select one or more {chosen_col} values:", unique_vals)
    if selected_vals:
        df = df[df[chosen_col].isin(selected_vals)]
        st.write(f"📉 Filtering {chosen_col} to: {selected_vals}")
        st.dataframe(df.head())

st.write(f"📊 Total records after filtering: {len(df)}")

# ─── Select Two Periods for Comparison ────────────────────
st.subheader("Select Two Periods for Comparison")
start_date1 = st.date_input("Start date for Period 1:", df['CreatedDate'].min())
end_date1   = st.date_input("End date for Period 1:",   df['CreatedDate'].max())
start_date2 = st.date_input("Start date for Period 2:", df['CreatedDate'].min())
end_date2   = st.date_input("End date for Period 2:",   df['CreatedDate'].max())

# Slice data for each period
df_period1 = df[(df['CreatedDate'] >= pd.to_datetime(start_date1)) & 
                (df['CreatedDate'] <= pd.to_datetime(end_date1))]
df_period2 = df[(df['CreatedDate'] >= pd.to_datetime(start_date2)) & 
                (df['CreatedDate'] <= pd.to_datetime(end_date2))]

# ─── Compute Totals ────────────────────────────────────────
total_revenue1  = (df_period1['Quantity'] * df_period1['PricePerUnit']).sum()
total_margin1   = (df_period1['Quantity'] * df_period1['MarginPerUnit']).sum()
total_quantity1 = df_period1['Quantity'].sum()

total_revenue2  = (df_period2['Quantity'] * df_period2['PricePerUnit']).sum()
total_margin2   = (df_period2['Quantity'] * df_period2['MarginPerUnit']).sum()
total_quantity2 = df_period2['Quantity'].sum()

# ─── Compute Differences & Percent Changes ────────────────
diff_revenue   = total_revenue2  - total_revenue1
diff_margin    = total_margin2   - total_margin1
diff_quantity  = total_quantity2 - total_quantity1

pct_change_revenue  = (diff_revenue  / total_revenue1)  * 100 if total_revenue1  != 0 else 0
pct_change_margin   = (diff_margin   / total_margin1)   * 100 if total_margin1   != 0 else 0
pct_change_quantity = (diff_quantity / total_quantity1) * 100 if total_quantity1 != 0 else 0

# ─── Metric Selection & Display ───────────────────────────
metric_choice = st.selectbox("Select the Metric to Display", ["All", "Revenue", "Margin", "Quantity"])

if metric_choice == "All":
    comparison_df = pd.DataFrame({
        'Metric': ['Revenue', 'Margin', 'Quantity'],
        'Period 1 Value': [total_revenue1, total_margin1, total_quantity1],
        'Period 2 Value': [total_revenue2, total_margin2, total_quantity2],
        'Difference':     [diff_revenue, diff_margin, diff_quantity],
        'Percentage Change (%)': [pct_change_revenue, pct_change_margin, pct_change_quantity]
    })
    st.dataframe(comparison_df)

elif metric_choice == "Revenue":
    st.subheader("Revenue Comparison")
    st.write(f"**Period 1 Revenue:** ${total_revenue1:,.2f}")
    st.write(f"**Period 2 Revenue:** ${total_revenue2:,.2f}")
    st.write(f"**Difference:** ${diff_revenue:,.2f}")
    st.write(f"**Percentage Change:** {pct_change_revenue:.2f}%")

elif metric_choice == "Margin":
    st.subheader("Margin Comparison")
    st.write(f"**Period 1 Margin:** ${total_margin1:,.2f}")
    st.write(f"**Period 2 Margin:** ${total_margin2:,.2f}")
    st.write(f"**Difference:** ${diff_margin:,.2f}")
    st.write(f"**Percentage Change:** {pct_change_margin:.2f}%")

elif metric_choice == "Quantity":
    st.subheader("Quantity Comparison")
    st.write(f"**Period 1 Quantity:** {total_quantity1}")
    st.write(f"**Period 2 Quantity:** {total_quantity2}")
    st.write(f"**Difference:** {diff_quantity}")
    st.write(f"**Percentage Change:** {pct_change_quantity:.2f}%")

# ─── Time-Series Lineplots with Adaptive Range & Markers ───
def plot_timeseries(metric):
    # Build the daily series
    ts = df.copy()
    if metric == "Revenue":
        ts["MetricSeries"] = ts["Quantity"] * ts["PricePerUnit"]
    elif metric == "Margin":
        ts["MetricSeries"] = ts["Quantity"] * ts["MarginPerUnit"]
    else:
        ts["MetricSeries"] = ts["Quantity"]

    ts_daily = (
        ts.set_index("CreatedDate")
            .resample("D")["MetricSeries"]
            .sum()
            .reset_index()
    )

    fig = px.line(
        ts_daily,
        x="CreatedDate",
        y="MetricSeries",
        title=f"{metric} Over Time",
        labels={"MetricSeries": metric, "CreatedDate": "Date"},
    )

    # Add period boundary lines
    boundaries = [
        (start_date1, "dash",  "green"),
        (end_date1,   "dot",   "green"),
        (start_date2, "dash",  "red"),
        (end_date2,   "dot",   "red"),
    ]
    for dt, dash, color in boundaries:
        fig.add_vline(
            x=pd.to_datetime(dt),
            line_dash=dash,
            line_color=color,
            opacity=0.6
        )

    # Clamp x-axis
    x0 = min(pd.to_datetime(start_date1), pd.to_datetime(start_date2))
    x1 = max(pd.to_datetime(end_date1),   pd.to_datetime(end_date2))
    fig.update_xaxes(range=[x0, x1], tickformat="%b %d", tickangle=-45, nticks=6)

    st.plotly_chart(fig, use_container_width=True)

if metric_choice == "All":
    # plot all three
    for m in ["Revenue", "Margin", "Quantity"]:
        plot_timeseries(m)
else:
    # plot only the selected one
    plot_timeseries(metric_choice)


