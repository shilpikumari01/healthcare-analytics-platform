import os
import pandas as pd
import streamlit as st
import google.generativeai as genai

# Pehle config file se key try karein, agar missing ho toh handle karein
try:
    from config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = ""

# Streamlit Cloud Secrets se API key safe load karein (Crash-Proof)
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", GEMINI_API_KEY))
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)


def generate_template_summary(kpi_data, dept_df):
    """Fallback function: Rule-based template generation when API key is missing or call fails."""
    total = kpi_data.get("total_appointments", 0)
    completed = kpi_data.get("completed_appointments", 0)
    cancel_rate = kpi_data.get("cancellation_rate_pct", 0)
    revenue = kpi_data.get("total_revenue", 0)

    top_dept = "N/A"
    if not dept_df.empty and "department_name" in dept_df.columns:
        top_dept = dept_df.iloc[0]["department_name"]

    return f"""
    ### 📋 Executive Analytical Summary (Template Fallback)
    
    * **Total Patient Visits:** The platform recorded **{total}** total appointment requests.
    * **Completion Rate:** **{completed}** appointments were completed successfully, generating **₹{revenue:,.2f}** in total revenue.
    * **Cancellation Impact:** The overall appointment cancellation rate stands at **{cancel_rate}%**.
    * **Top Department:** The department with the highest patient volume is **{top_dept}**.
    
    *Note: Summary auto-generated using rule-based calculations.*
    """


def generate_executive_summary(kpi_data, dept_df):
    """Generates an AI summary using Google Gemini API if key is present, otherwise falls back to template."""
    # Check if API key is valid
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() in ["your_google_gemini_api_key_here", ""]:
        return generate_template_summary(kpi_data, dept_df)

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        dept_summary = (
            dept_df.to_string(index=False)
            if not dept_df.empty
            else "No department data available."
        )

        prompt = f"""
        You are a healthcare data analyst. Synthesize the following exact calculated metrics into a concise, professional 4-bullet executive summary.
        STRICT REQUIREMENT: Do NOT invent, extrapolate, or estimate any numbers. Use ONLY the exact numbers provided below.

        Exact Aggregated Metrics:
        - Total Appointments: {kpi_data.get('total_appointments')}
        - Completed Appointments: {kpi_data.get('completed_appointments')}
        - Cancelled Appointments: {kpi_data.get('cancelled_appointments')}
        - Cancellation Rate: {kpi_data.get('cancellation_rate_pct')}%
        - Total Revenue: ₹{kpi_data.get('total_revenue')}

        Department-wise Breakdown Table:
        {dept_summary}

        Provide concise insights in professional bullet points.
        """

        response = model.generate_content(prompt)
        if response and response.text:
            return f"### 🤖 AI Executive Summary\n\n{response.text}"
        else:
            return generate_template_summary(kpi_data, dept_df)

    except Exception as e:
        # Any API error falls back cleanly to template summary
        return generate_template_summary(kpi_data, dept_df)