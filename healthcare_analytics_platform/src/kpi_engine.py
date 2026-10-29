
import os
import pandas as pd
from sqlalchemy import text
from src.database import get_db_engine


# Demo mode defaults to True for Streamlit Cloud demo.
# Set DEMO_MODE=false when a cloud MySQL database is ready.
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


# ---------------- DEMO DATA ----------------

def _demo_summary():
    return {
        "total_appointments": 14,
        "completed_appointments": 10,
        "cancelled_appointments": 3,
        "noshow_appointments": 1,
        "cancellation_rate_pct": 21.43,
        "total_revenue": 16000.0,
    }


def _demo_departments():
    return pd.DataFrame([
        {
            "department_name": "Cardiology",
            "total_visits": 5,
            "completed_visits": 4,
            "cancelled_visits": 1,
            "total_revenue": 7000.0,
        },
        {
            "department_name": "Dermatology",
            "total_visits": 4,
            "completed_visits": 3,
            "cancelled_visits": 1,
            "total_revenue": 4500.0,
        },
        {
            "department_name": "Neurology",
            "total_visits": 3,
            "completed_visits": 2,
            "cancelled_visits": 1,
            "total_revenue": 3000.0,
        },
        {
            "department_name": "Orthopedics",
            "total_visits": 2,
            "completed_visits": 1,
            "cancelled_visits": 0,
            "total_revenue": 1500.0,
        },
    ])


def _demo_monthly():
    return pd.DataFrame([
        {
            "month_year": "2026-01",
            "monthly_visits": 4,
            "monthly_cancellations": 1,
            "monthly_revenue": 4000.0,
        },
        {
            "month_year": "2026-02",
            "monthly_visits": 5,
            "monthly_cancellations": 1,
            "monthly_revenue": 5500.0,
        },
        {
            "month_year": "2026-03",
            "monthly_visits": 5,
            "monthly_cancellations": 1,
            "monthly_revenue": 6500.0,
        },
    ])


def _demo_doctors():
    return pd.DataFrame([
        {
            "doctor_name": "Dr. Sharma",
            "department_name": "Cardiology",
            "total_patients": 5,
            "revenue_generated": 7000.0,
        },
        {
            "doctor_name": "Dr. Verma",
            "department_name": "Dermatology",
            "total_patients": 4,
            "revenue_generated": 4500.0,
        },
        {
            "doctor_name": "Dr. Singh",
            "department_name": "Neurology",
            "total_patients": 3,
            "revenue_generated": 3000.0,
        },
        {
            "doctor_name": "Dr. Gupta",
            "department_name": "Orthopedics",
            "total_patients": 2,
            "revenue_generated": 1500.0,
        },
    ])


# ---------------- SUMMARY KPIs ----------------

def fetch_summary_kpis():
    if DEMO_MODE:
        return _demo_summary()

    engine = get_db_engine()

    query = """
    SELECT
        COUNT(appointment_id) AS total_appointments,
        SUM(CASE WHEN LOWER(status) = 'completed'
            THEN 1 ELSE 0 END) AS completed_appointments,
        SUM(CASE WHEN LOWER(status) = 'cancelled'
            THEN 1 ELSE 0 END) AS cancelled_appointments,
        SUM(CASE WHEN LOWER(status) = 'no-show'
            THEN 1 ELSE 0 END) AS noshow_appointments,
        ROUND(
            SUM(CASE WHEN LOWER(status) = 'cancelled'
                THEN 1 ELSE 0 END) * 100.0
            / NULLIF(COUNT(appointment_id), 0), 2
        ) AS cancellation_rate_pct,
        SUM(CASE WHEN LOWER(status) = 'completed'
            THEN consultation_fee ELSE 0 END) AS total_revenue
    FROM appointments;
    """

    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)

    if df.empty or pd.isna(df.iloc[0]["total_appointments"]) \
            or df.iloc[0]["total_appointments"] == 0:
        return {
            "total_appointments": 0,
            "completed_appointments": 0,
            "cancelled_appointments": 0,
            "noshow_appointments": 0,
            "cancellation_rate_pct": 0.0,
            "total_revenue": 0.0,
        }

    result = df.to_dict(orient="records")[0]
    result["cancellation_rate_pct"] = (
        result["cancellation_rate_pct"] or 0.0
    )
    result["total_revenue"] = result["total_revenue"] or 0.0

    return result


# ---------------- DEPARTMENT KPIs ----------------

def fetch_department_kpis():
    if DEMO_MODE:
        return _demo_departments()

    engine = get_db_engine()

    query = """
    SELECT
        COALESCE(d.department_name, 'General') AS department_name,
        COUNT(a.appointment_id) AS total_visits,
        SUM(CASE WHEN LOWER(a.status) = 'completed'
            THEN 1 ELSE 0 END) AS completed_visits,
        SUM(CASE WHEN LOWER(a.status) = 'cancelled'
            THEN 1 ELSE 0 END) AS cancelled_visits,
        ROUND(
            SUM(CASE WHEN LOWER(a.status) = 'completed'
                THEN a.consultation_fee ELSE 0 END), 2
        ) AS total_revenue
    FROM appointments a
    LEFT JOIN departments d
        ON a.department_id = d.department_id
    GROUP BY d.department_name
    ORDER BY total_visits DESC;
    """

    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


# ---------------- MONTHLY KPIs ----------------

def fetch_monthly_kpis():
    if DEMO_MODE:
        return _demo_monthly()

    engine = get_db_engine()

    query = """
    SELECT
        DATE_FORMAT(appointment_date, '%Y-%m') AS month_year,
        COUNT(appointment_id) AS monthly_visits,
        SUM(CASE WHEN LOWER(status) = 'cancelled'
            THEN 1 ELSE 0 END) AS monthly_cancellations,
        ROUND(
            SUM(CASE WHEN LOWER(status) = 'completed'
                THEN consultation_fee ELSE 0 END), 2
        ) AS monthly_revenue
    FROM appointments
    WHERE appointment_date IS NOT NULL
    GROUP BY DATE_FORMAT(appointment_date, '%Y-%m')
    ORDER BY month_year ASC;
    """

    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


# ---------------- DOCTOR PERFORMANCE ----------------

def fetch_doctor_performance():
    if DEMO_MODE:
        return _demo_doctors()

    engine = get_db_engine()

    query = """
    SELECT
        COALESCE(doc.doctor_name, 'Doctor') AS doctor_name,
        COALESCE(dep.department_name, 'General Medicine')
            AS department_name,
        COUNT(app.appointment_id) AS total_patients,
        SUM(CASE WHEN LOWER(app.status) = 'completed'
            THEN app.consultation_fee ELSE 0 END) AS revenue_generated
    FROM appointments app
    LEFT JOIN doctors doc
        ON app.doctor_id = doc.doctor_id
    LEFT JOIN departments dep
        ON doc.department_id = dep.department_id
    GROUP BY doc.doctor_name, dep.department_name
    ORDER BY total_patients DESC;
    """

    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)
