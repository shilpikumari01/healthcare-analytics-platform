import streamlit as st
import pandas as pd
import os
import streamlit as st
from PIL import Image

# Streamlit config sabse pehle call honi chahiye (StreamlitAPIException fix)[cite: 2]
st.set_page_config(page_title="Healthcare Analytics Platform", layout="wide")

# Baaki modules config ke baad import honge
from src.cleaner import clean_healthcare_data, load_data_to_mysql, export_to_excel
from src.kpi_engine import fetch_summary_kpis, fetch_department_kpis, fetch_monthly_kpis, fetch_doctor_performance
from src.ai_summarizer import generate_executive_summary
from src.api_fetcher import fetch_external_patient_data

st.title("🏥 Healthcare Data Analytics & AI-Powered Insights Platform")

st.sidebar.header("📁 Data Ingestion Pipeline")
uploaded_file = st.sidebar.file_uploader("Upload Healthcare CSV", type=["csv"])

if uploaded_file is not None:
    st.sidebar.success("File uploaded!")
    if st.sidebar.button("Run Data Cleaning & Database Sync"):
        with st.spinner("Cleaning data and updating MySQL database..."):
            cleaned_df, quality_report = clean_healthcare_data(uploaded_file)
            load_data_to_mysql(cleaned_df)
            export_to_excel(cleaned_df, quality_report)
            st.session_state["quality_report"] = quality_report
            st.success("✅ Data ingested, sanitized, and stored in MySQL!")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics Dashboard", "🧹 Data Quality Report", "🤖 AI Executive Summary", "🌐 External API Integration"])

with tab1:
    st.subheader("Key Performance Indicators (KPIs)")
    try:
        kpis = fetch_summary_kpis()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Appointments", kpis.get("total_appointments", 0))
        col2.metric("Completed Visits", kpis.get("completed_appointments", 0))
        col3.metric("Cancellation Rate", f"{kpis.get('cancellation_rate_pct', 0)}%")
        col4.metric("Total Revenue", f"₹{kpis.get('total_revenue', 0):,.2f}")

        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### Department Breakdown")
            dept_df = fetch_department_kpis()
            st.dataframe(dept_df, use_container_width=True)
            if not dept_df.empty and "department_name" in dept_df.columns:
                st.bar_chart(dept_df.set_index("department_name")["total_visits"])

        with col_right:
            st.markdown("### Monthly Trend")
            monthly_df = fetch_monthly_kpis()
            st.dataframe(monthly_df, use_container_width=True)
            if not monthly_df.empty and "month_year" in monthly_df.columns:
                st.line_chart(monthly_df.set_index("month_year")["monthly_visits"])

        st.markdown("### Doctor Performance")
        st.dataframe(fetch_doctor_performance(), use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching metrics from database: {e}. Please run cleaning pipeline.")

with tab2:
    st.header("📊 Power BI Executive Analytics Dashboard")
    st.info("💡 Interactive visual report built on Healthcare Analytics Warehouse.")
    
    # Power BI Dashboard Image Preview
    image = Image.open('dashboard_preview.png')
    st.image(image, caption='Healthcare Executive Dashboard (Power BI Desktop)', use_container_width=True)
    
    st.markdown("""
    ### 📈 Executive Insights Summary:
    * **Revenue & Appointment Volume:** Total Revenue (16K) and Total Volume (14) KPIs.
    * **Department Distribution:** Patient load across Cardiology, Dermatology, Neurology, and Orthopedics.
    * **Fulfillment Analysis:** Status breakdown comparing Completed (71.4%) vs Cancelled/No-Show appointments.
    """)


with tab3:
    st.subheader("GenAI-Powered Executive Summary")
    if st.button("Generate Summary"):
        with st.spinner("Generating summary..."):
            st.markdown(generate_executive_summary(fetch_summary_kpis(), fetch_department_kpis()))

with tab4:
    st.subheader("🌐 External API Data Integration")
    st.caption("Live stream and staging area for third-party medical network records.")

    if st.button("Fetch API Data"):
        with st.spinner("Fetching data from external endpoint..."):
            api_df = fetch_external_patient_data()

        if not api_df.empty:
            st.success("Data successfully fetched from External API!")

            # Check column names (Handles both 'City' and 'city')
            city_col = "City" if "City" in api_df.columns else ("city" if "city" in api_df.columns else None)

            # 1. KPI Summary Cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total External Records", value=len(api_df))
            with col2:
                cities_count = api_df[city_col].nunique() if city_col else 0
                st.metric(label="Unique Regions / Cities", value=cities_count)
            with col3:
                st.metric(
                    label="Integration Status",
                    value="Active Stream",
                    delta="Synced",
                )

            st.markdown("---")

            # 2. Interactive Graph Visualization
            if city_col:
                st.subheader("📊 External Patient Distribution by Region")
                city_counts = api_df[city_col].value_counts()
                st.bar_chart(city_counts)
                st.markdown("---")

            # 3. Raw Data Preview
            st.subheader("📋 Raw External Records Table")
            st.dataframe(api_df, use_container_width=True)
        else:
            st.error("Failed to fetch data from external API endpoint.")
    
               