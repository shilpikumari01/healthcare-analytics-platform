
import os
import streamlit as st
import google.generativeai as genai


def get_api_key():
    # Streamlit Cloud Secrets
    try:
        key = st.secrets["gemini"]["api_key"]
        if key:
            return key.strip()
    except Exception:
        pass

    # Alternative Secrets format
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key:
            return key.strip()
    except Exception:
        pass

    # Local environment variable
    return os.getenv("GEMINI_API_KEY", "").strip()


def generate_executive_summary(kpi_data, dept_df):
    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "Gemini API key missing. Add it under Streamlit Cloud "
            "Settings > Secrets using [gemini] and api_key."
        )

    genai.configure(api_key=api_key)

    department_data = (
        dept_df.to_string(index=False)
        if dept_df is not None and not dept_df.empty
        else "No department data available."
    )

    prompt = f"""
You are a healthcare data analyst.

Write a concise executive summary in 4 bullet points using
only the metrics supplied below. Do not invent numbers.
If the data is sample data, do not describe it as live patient data.

Metrics:
- Total appointments: {kpi_data.get('total_appointments', 0)}
- Completed appointments: {kpi_data.get('completed_appointments', 0)}
- Cancelled appointments: {kpi_data.get('cancelled_appointments', 0)}
- No-show appointments: {kpi_data.get('noshow_appointments', 0)}
- Cancellation rate: {kpi_data.get('cancellation_rate_pct', 0)}%
- Total revenue: ₹{kpi_data.get('total_revenue', 0)}

Department breakdown:
{department_data}

Explain the key patterns and provide practical recommendations
without making unsupported claims.
"""

    # Use a model name supported by the current Gemini API access.
    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(prompt)

    if not response or not response.text:
        raise RuntimeError(
            "Gemini returned an empty response. Check API access and quota."
        )

    return "### 🤖 Gemini AI Executive Summary\n\n" + response.text
