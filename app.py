import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Quotation Dashboard", layout="wide")

st.title("📊 Automated Quotation Dashboard")

# Upload file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ---------- DATA CLEANING ----------
    df.columns = df.columns.str.strip()

    # Convert dates
    df['QuotationDate'] = pd.to_datetime(df['QuotationDate'], errors='coerce')
    df['EnquiryDate'] = pd.to_datetime(df['EnquiryDate'], errors='coerce')

    # Conversion flag
    df['ConvertedFlag'] = df['Converted?'].apply(lambda x: 1 if str(x).lower() == 'yes' else 0)

    # ---------- KPI SECTION ----------
    total_enquiries = df['EnquiryNumber'].nunique()
    total_quotes = df['QuotationNumber'].nunique()
    total_converted = df['ConvertedFlag'].sum()
    conversion_rate = (total_converted / total_quotes) * 100 if total_quotes > 0 else 0
    total_quote_value = df['FinalQuotationAmount'].sum()
    total_order_value = df['PartsOrderAmount'].sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Enquiries", total_enquiries)
    col2.metric("Quotations", total_quotes)
    col3.metric("Conversions", total_converted)
    col4.metric("Conversion %", f"{conversion_rate:.2f}%")
    col5.metric("Revenue", f"{total_order_value:,.0f}")

    st.markdown("---")

    # ---------- FILTERS ----------
    branch = st.selectbox("Select Branch", ["All"] + list(df['DealerBranchName'].dropna().unique()))

    if branch != "All":
        df = df[df['DealerBranchName'] == branch]

    # ---------- FUNNEL ----------
    funnel_data = pd.DataFrame({
        "Stage": ["Enquiries", "Quotations", "Conversions"],
        "Count": [total_enquiries, total_quotes, total_converted]
    })

    fig_funnel = px.funnel(funnel_data, x="Count", y="Stage")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # ---------- CATEGORY SALES ----------
    category_sales = df.groupby('PartsCategory')['PartsOrderAmount'].sum().reset_index()

    fig_cat = px.bar(category_sales, x='PartsCategory', y='PartsOrderAmount', title="Category Sales")
    st.plotly_chart(fig_cat, use_container_width=True)

    # ---------- DEALER PERFORMANCE ----------
    dealer_perf = df.groupby('DealerBranchName')['PartsOrderAmount'].sum().reset_index()

    fig_dealer = px.bar(dealer_perf, x='DealerBranchName', y='PartsOrderAmount', title="Dealer Performance")
    st.plotly_chart(fig_dealer, use_container_width=True)

    # ---------- LOSS REASON ----------
    loss_data = df[df['ConvertedFlag'] == 0]
    loss_reason = loss_data['ReasonCode'].value_counts().reset_index()
    loss_reason.columns = ['Reason', 'Count']

    fig_loss = px.pie(loss_reason, names='Reason', values='Count', title="Loss Reasons")
    st.plotly_chart(fig_loss, use_container_width=True)

    # ---------- AI INSIGHTS ----------
    st.markdown("## 🤖 AI Insights")

    if conversion_rate < 30:
        st.warning("Low conversion rate. Consider reducing pricing or improving follow-ups.")

    if df['PartsDisc. %'].mean() > 20:
        st.info("High discounts detected. Check margin impact.")

    top_category = category_sales.sort_values(by='PartsOrderAmount', ascending=False).iloc[0]
    st.success(f"Top selling category is {top_category['PartsCategory']}")