import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI Sales Dashboard", layout="wide")

st.title("🚀 AI-Powered Quotation Analytics")

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # -------- DATA PREP --------
    df['ConvertedFlag'] = df['Converted?'].astype(str).str.lower().eq('yes').astype(int)
    df['QuotationDate'] = pd.to_datetime(df['QuotationDate'], errors='coerce')

    # -------- KPI --------
    total_quotes = df['QuotationNumber'].nunique()
    total_orders = df['ConvertedFlag'].sum()
    conversion_rate = (total_orders / total_quotes) * 100 if total_quotes else 0

    total_quote_value = df['FinalQuotationAmount'].sum()
    total_order_value = df['PartsOrderAmount'].sum()
    leakage = total_quote_value - total_order_value

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Quotations", total_quotes)
    col2.metric("Orders", total_orders)
    col3.metric("Conversion %", f"{conversion_rate:.2f}%")
    col4.metric("Revenue Leakage", f"{leakage:,.0f}")

    st.markdown("---")

    # -------- FILTERS --------
    col1, col2 = st.columns(2)

    branch = col1.multiselect("Branch", df['DealerBranchName'].dropna().unique())
    category = col2.multiselect("Category", df['PartsCategory'].dropna().unique())

    if branch:
        df = df[df['DealerBranchName'].isin(branch)]
    if category:
        df = df[df['PartsCategory'].isin(category)]

    # -------- FUNNEL --------
    funnel_df = pd.DataFrame({
        "Stage": ["Quotation", "Converted"],
        "Count": [total_quotes, total_orders]
    })
    fig_funnel = px.funnel(funnel_df, x="Count", y="Stage", title="Sales Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # -------- SALES REP PERFORMANCE --------
    rep_perf = df.groupby('AfterMarketSalesRep').agg({
        'PartsOrderAmount': 'sum',
        'ConvertedFlag': 'mean'
    }).reset_index()

    rep_perf['ConvertedFlag'] *= 100

    fig_rep = px.bar(rep_perf, x='AfterMarketSalesRep',
                     y='PartsOrderAmount',
                     title="Sales Rep Revenue")
    st.plotly_chart(fig_rep, use_container_width=True)

    # -------- DISCOUNT VS CONVERSION --------
    fig_disc = px.scatter(df,
                         x='PartsDisc. %',
                         y='PartsOrderAmount',
                         color='ConvertedFlag',
                         title="Discount vs Conversion")
    st.plotly_chart(fig_disc, use_container_width=True)

    # -------- LOSS ANALYSIS --------
    loss_df = df[df['ConvertedFlag'] == 0]

    if not loss_df.empty:
        loss_reason = loss_df['ReasonCode'].value_counts().reset_index()
        loss_reason.columns = ['Reason', 'Count']

        fig_loss = px.pie(loss_reason,
                          names='Reason',
                          values='Count',
                          title="Loss Reasons")
        st.plotly_chart(fig_loss, use_container_width=True)

    # -------- AI INSIGHTS --------
    st.subheader("🤖 AI Insights")

    insights = []

    if conversion_rate < 30:
        insights.append("⚠️ Low conversion rate detected. Improve follow-ups or pricing.")

    if df['PartsDisc. %'].mean() > 20:
        insights.append("💸 High discounts impacting margins.")

    top_rep = rep_perf.sort_values(by='PartsOrderAmount', ascending=False).iloc[0]
    insights.append(f"🏆 Top performer: {top_rep['AfterMarketSalesRep']}")

    high_loss = loss_df['ReasonCode'].value_counts().idxmax() if not loss_df.empty else "N/A"
    insights.append(f"❌ Main loss reason: {high_loss}")

    for i in insights:
        st.write(i)
