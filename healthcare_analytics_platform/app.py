
import os
import pandas as pd
import streamlit as st
from PIL import Image

# --------------------------------------------------
# 1. STREAMLIT CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Healthcare Analytics Platform",
    page_icon="🏥",
    layout="wide"
)

# --------------------------------------------------
# 2. IMPORT PROJECT MODULES
# --------------------------------------------------

from src.cleaner import (
    clean_healthcare_data,
    load_data_to_mysql,
    export_to_excel
)

from src.kpi_engine import (
    fetch_summary_kpis,
    fetch_department_kpis,
    fetch_monthly_kpis,
    fetch_doctor_performance
)

from src.ai_summarizer import generate_executive_summary
from src.api_fetcher import fetch_external_patient_data


# --------------------------------------------------
# 3. APPLICATION TITLE AND DEMO MODE
# --------------------------------------------------

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

st.title("🏥 Healthcare Data Analytics & AI-Powered Insights Platform")



# --------------------------------------------------
# 4. SIDEBAR: DATA INGESTION PIPELINE
# --------------------------------------------------

st.sidebar.header("📁 Data Ingestion Pipeline")

uploaded_file = st.sidebar.file_uploader(
    "Upload Healthcare CSV",
    type=["csv"]
)

if uploaded_file is not None:
    st.sidebar.success("File uploaded!")

    if st.sidebar.button("Run Data Cleaning & Database Sync"):
        try:
            with st.spinner(
                "Cleaning data and updating MySQL database..."
            ):
                cleaned_df, quality_report = clean_healthcare_data(
                    uploaded_file
                )

                load_data_to_mysql(cleaned_df)

                export_to_excel(cleaned_df, quality_report)

                st.session_state["quality_report"] = quality_report

            st.sidebar.success("Data pipeline completed successfully!")
            st.success(
                "✅ Data cleaned and stored in MySQL successfully."
            )

        except Exception as e:
            st.error(
                "Data ingestion failed. Check your database connection "
                f"and CSV format. Details: {e}"
            )


# --------------------------------------------------
# 5. CREATE APPLICATION TABS
# --------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Analytics Dashboard",
    "🧹 Data Quality Report",
    "📈 Power BI Executive Dashboard",
    "🤖 AI Executive Summary",
    "🌐 External API Integration"
])


# --------------------------------------------------
# TAB 1: ANALYTICS DASHBOARD
# --------------------------------------------------

with tab1:
    st.subheader("📊 Key Performance Indicators (KPIs)")

    try:
        kpis = fetch_summary_kpis()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Appointments",
            kpis.get("total_appointments", 0)
        )

        col2.metric(
            "Completed Visits",
            kpis.get("completed_appointments", 0)
        )

        col3.metric(
            "Cancellation Rate",
            f"{kpis.get('cancellation_rate_pct', 0)}%"
        )

        col4.metric(
            "Total Revenue",
            f"₹{kpis.get('total_revenue', 0):,.2f}"
        )

        st.divider()

        col_left, col_right = st.columns(2)

        # Department breakdown
        with col_left:
            st.markdown("### Department Breakdown")

            dept_df = fetch_department_kpis()

            st.dataframe(
                dept_df,
                use_container_width=True
            )

            if (
                not dept_df.empty
                and "department_name" in dept_df.columns
                and "total_visits" in dept_df.columns
            ):
                chart_df = dept_df.set_index("department_name")
                st.bar_chart(chart_df["total_visits"])

        # Monthly trend
        with col_right:
            st.markdown("### Monthly Trend")

            monthly_df = fetch_monthly_kpis()

            st.dataframe(
                monthly_df,
                use_container_width=True
            )

            if (
                not monthly_df.empty
                and "month_year" in monthly_df.columns
                and "monthly_visits" in monthly_df.columns
            ):
                chart_df = monthly_df.set_index("month_year")
                st.line_chart(chart_df["monthly_visits"])

        # Doctor performance
        st.markdown("### Doctor Performance")

        doctor_df = fetch_doctor_performance()

        st.dataframe(
            doctor_df,
            use_container_width=True
        )

    except Exception as e:
        st.error(
            f"Unable to load dashboard metrics: {e}"
        )


# --------------------------------------------------
# TAB 2: DATA QUALITY REPORT
# --------------------------------------------------

with tab2:
    st.header("🧹 Data Sanitation & Quality Report")

    if "quality_report" in st.session_state:
        st.success("Data quality report is available.")

        st.json(st.session_state["quality_report"])

    else:
        st.info(
            "Upload a CSV file and run the data cleaning pipeline "
            "from the sidebar to generate a quality report."
        )


# --------------------------------------------------
# TAB 3: POWER BI DASHBOARD PREVIEW
# --------------------------------------------------

with tab3:
    st.header("📈 Power BI Executive Analytics Dashboard")

    st.info(
        "This section displays a saved preview of the Power BI report."
    )

    image_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "reports",
        "dashboard_preview.png"
    )

    fallback_image_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "dashboard_preview.png"
    )

    if os.path.exists(image_path):
        image = Image.open(image_path)

        st.image(
            image,
            caption="Healthcare Executive Dashboard — Power BI Preview",
            use_column_width=True
        )

    elif os.path.exists(fallback_image_path):
        image = Image.open(fallback_image_path)

        st.image(
            image,
            caption="Healthcare Executive Dashboard — Power BI Preview",
            use_column_width=True
        )

    else:
        st.warning(
            "Power BI preview image not found. "
            "Ensure dashboard_preview.png is present in the reports folder."
        )

    st.markdown("### 📊 Executive Insights")

    st.markdown(
        """
        - **Revenue and Appointment Volume:** Review total revenue
          and appointment counts.
        - **Department Distribution:** Compare visits across departments.
        - **Appointment Status:** Review completed, cancelled and
          no-show appointments.
        """
    )


# --------------------------------------------------
# TAB 4: AI EXECUTIVE SUMMARY
# --------------------------------------------------

with tab4:
    st.subheader("🤖 GenAI-Powered Executive Summary")

    st.write(
        "Generate a short summary of the healthcare dashboard metrics."
    )

    if st.button("Generate Summary"):
        try:
            with st.spinner("Generating executive summary..."):
                summary_kpis = fetch_summary_kpis()
                department_kpis = fetch_department_kpis()

                summary = generate_executive_summary(
                    summary_kpis,
                    department_kpis
                )

            if summary:
                st.markdown(summary)
            else:
                st.warning(
                    "No summary was returned. Check the AI API configuration."
                )

        except Exception as e:
            st.error(
                "Unable to generate the AI summary. "
                f"Check your API key and configuration. Details: {e}"
            )


# --------------------------------------------------
# TAB 5: EXTERNAL API INTEGRATION
# --------------------------------------------------

with tab5:
    st.subheader("🌐 External API Data Integration")

    st.caption(
        "Fetch and preview records returned by the configured external API."
    )

    if st.button("Fetch API Data"):
        try:
            with st.spinner("Fetching external API data..."):
                api_df = fetch_external_patient_data()

            if (
                api_df is not None
                and isinstance(api_df, pd.DataFrame)
                and not api_df.empty
            ):
                st.success(
                    "External API data fetched successfully."
                )

                # Identify city column, if available
                city_col = None

                if "City" in api_df.columns:
                    city_col = "City"
                elif "city" in api_df.columns:
                    city_col = "city"

                # KPI summary cards
                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Total External Records",
                    len(api_df)
                )

                cities_count = (
                    api_df[city_col].nunique()
                    if city_col
                    else 0
                )

                col2.metric(
                    "Unique Regions / Cities",
                    cities_count
                )

                col3.metric(
                    "Integration Status",
                    "Data Retrieved"
                )

                st.divider()

                # Regional distribution
                if city_col:
                    st.subheader(
                        "📊 External Records by Region"
                    )

                    city_counts = api_df[city_col].value_counts()

                    st.bar_chart(city_counts)

                    st.divider()

                # Raw records
                st.subheader("📋 External Records Preview")

                st.dataframe(
                    api_df,
                    use_container_width=True
                )

            else:
                st.warning(
                    "The API returned no records, or the data "
                    "could not be retrieved."
                )

        except Exception as e:
            st.error(
                f"External API request failed: {e}"
            )
