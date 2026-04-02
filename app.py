import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI Sales Dashboard", layout="wide")

st.title("🚀 AI-Powered Quotation Analytics Dashboard")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # ---------------- DATA PREP ----------------
    df['ConvertedFlag'] = df['Converted?'].astype(str).str.lower().eq('yes').astype(int)

    df['QuotationDate'] = pd.to_datetime(df['QuotationDate'], errors='coerce')
    df['PartsOrderDate'] = pd.to_datetime(df['PartsOrderDate'], errors='coerce')

    # ---------------- KPI SECTION ----------------
    total_enquiries = df['EnquiryNumber'].nunique()
    total_quotes = df['QuotationNumber'].nunique()
    total_orders = df['ConvertedFlag'].sum()

    conversion_rate = (total_orders / total_quotes) * 100 if total_quotes else 0

    total_quote_value = df['FinalQuotationAmount'].sum()
    total_order_value = df['PartsOrderAmount'].sum()
    leakage = total_quote_value - total_order_value

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Enquiries", total_enquiries)
    col2.metric("Quotations", total_quotes)
    col3.metric("Orders", total_orders)
    col4.metric("Conversion %", f"{conversion_rate:.2f}%")
    col5.metric("Revenue Leakage", f"{leakage:,.0f}")

    st.markdown("---")

    # ---------------- FILTERS ----------------
    col1, col2, col3 = st.columns(3)

    branch = col1.multiselect("Branch", df['DealerBranchName'].dropna().unique())
    category = col2.multiselect("Category", df['PartsCategory'].dropna().unique())
    rep = col3.multiselect("Sales Rep", df['AfterMarketSalesRep'].dropna().unique())

    if branch:
        df = df[df['DealerBranchName'].isin(branch)]
    if category:
        df = df[df['PartsCategory'].isin(category)]
    if rep:
        df = df[df['AfterMarketSalesRep'].isin(rep)]

    # ---------------- FUNNEL ----------------
    funnel_df = pd.DataFrame({
        "Stage": ["Enquiries", "Quotations", "Orders"],
        "Count": [total_enquiries, total_quotes, total_orders]
    })

    fig_funnel = px.funnel(funnel_df, x="Count", y="Stage", title="Sales Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # ---------------- TIME TREND ----------------
    df['Month'] = df['QuotationDate'].dt.to_period('M').astype(str)

    monthly_sales = df.groupby('Month')['PartsOrderAmount'].sum().reset_index()

    fig_time = px.line(monthly_sales, x='Month', y='PartsOrderAmount',
                       title="Monthly Revenue Trend")
    st.plotly_chart(fig_time, use_container_width=True)

    # ---------------- REALIZATION % ----------------
    df['Realization %'] = (df['PartsOrderAmount'] / df['FinalQuotationAmount']) * 100
    realization_avg = df['Realization %'].mean()

    st.metric("Avg Realization %", f"{realization_avg:.2f}%")

    # ---------------- CATEGORY SALES ----------------
    category_sales = df.groupby('PartsCategory')['PartsOrderAmount'].sum().reset_index()

    fig_cat = px.bar(category_sales, x='PartsCategory', y='PartsOrderAmount',
                     title="Category Sales")
    st.plotly_chart(fig_cat, use_container_width=True)

    # ---------------- TOP PARTS ----------------
    top_parts = df.groupby('PartNumber')['PartsOrderAmount'].sum().reset_index()
    top_parts = top_parts.sort_values(by='PartsOrderAmount', ascending=False).head(10)

    fig_parts = px.bar(top_parts, x='PartNumber', y='PartsOrderAmount',
                       title="Top 10 Parts by Revenue")
    st.plotly_chart(fig_parts, use_container_width=True)

    # ---------------- SALES REP PERFORMANCE ----------------
    rep_perf = df.groupby('AfterMarketSalesRep').agg({
        'PartsOrderAmount': 'sum',
        'PartsDisc. %': 'mean',
        'ConvertedFlag': 'mean'
    }).reset_index()

    rep_perf['ConvertedFlag'] *= 100

    fig_rep = px.scatter(rep_perf,
                         x='PartsDisc. %',
                         y='PartsOrderAmount',
                         size='ConvertedFlag',
                         color='AfterMarketSalesRep',
                         title="Sales Rep Performance")
    st.plotly_chart(fig_rep, use_container_width=True)

    # ---------------- DISCOUNT ANALYSIS ----------------
    fig_disc = px.scatter(df,
                          x='PartsDisc. %',
                          y='PartsOrderAmount',
                          color='ConvertedFlag',
                          title="Discount vs Conversion")
    st.plotly_chart(fig_disc, use_container_width=True)

    # ---------------- LOSS ANALYSIS ----------------
    loss_df = df[df['ConvertedFlag'] == 0]

    if not loss_df.empty:
        loss_reason = loss_df['ReasonCode'].value_counts().reset_index()
        loss_reason.columns = ['Reason', 'Count']

        fig_loss = px.pie(loss_reason,
                          names='Reason',
                          values='Count',
                          title="Loss Reasons")
        st.plotly_chart(fig_loss, use_container_width=True)

    # ---------------- CONVERSION TIME ----------------
    df['ConversionDays'] = (df['PartsOrderDate'] - df['QuotationDate']).dt.days
    avg_days = df['ConversionDays'].mean()

    st.metric("Avg Conversion Days", f"{avg_days:.1f} days")

    # ---------------- HEATMAP ----------------
    pivot = df.pivot_table(values='PartsOrderAmount',
                           index='DealerBranchName',
                           columns='PartsCategory',
                           aggfunc='sum',
                           fill_value=0)

    fig_heat = px.imshow(pivot, title="Branch vs Category Heatmap")
    st.plotly_chart(fig_heat, use_container_width=True)

    # ---------------- AI INSIGHTS ----------------
    st.subheader("🤖 AI Insights")

    if conversion_rate < 30:
        st.warning("⚠️ Low conversion rate. Improve pricing or follow-ups.")

    if df['PartsDisc. %'].mean() > 20:
        st.info("💸 High discounts detected. Check margin impact.")

    if realization_avg < 70:
        st.warning("⚠️ Low revenue realization. Discounts may be too high.")

    slow_conv = df[df['ConversionDays'] > 10]
    if not slow_conv.empty:
        st.info("⏳ Slow conversions detected. Improve response time.")

    high_disc_low_conv = df[(df['PartsDisc. %'] > 25) & (df['ConvertedFlag'] == 0)]
    if len(high_disc_low_conv) > 0:
        st.error("❌ High discounts are NOT improving conversion!")

    top_category = category_sales.sort_values(by='PartsOrderAmount', ascending=False).iloc[0]
    st.success(f"🏆 Top category: {top_category['PartsCategory']}")

else:
    st.info("📂 Please upload an Excel file to begin.")
