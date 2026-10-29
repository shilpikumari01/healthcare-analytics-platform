import pandas as pd
from sqlalchemy import text
from src.database import get_db_engine


def fetch_summary_kpis():
    engine = get_db_engine()
    query = """
    SELECT 
        COUNT(appointment_id) AS total_appointments,
        SUM(CASE WHEN LOWER(status) = 'completed' THEN 1 ELSE 0 END) AS completed_appointments,
        SUM(CASE WHEN LOWER(status) = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_appointments,
        SUM(CASE WHEN LOWER(status) = 'no-show' THEN 1 ELSE 0 END) AS noshow_appointments,
        ROUND((SUM(CASE WHEN LOWER(status) = 'cancelled' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(appointment_id), 0)), 2) AS cancellation_rate_pct,
        SUM(CASE WHEN LOWER(status) = 'completed' THEN consultation_fee ELSE 0 END) AS total_revenue
    FROM appointments;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)

    if df.empty or df.iloc[0]["total_appointments"] == 0:
        return {
            "total_appointments": 0,
            "completed_appointments": 0,
            "cancelled_appointments": 0,
            "cancellation_rate_pct": 0.0,
            "total_revenue": 0.0,
        }

    res = df.to_dict(orient="records")[0]
    res["cancellation_rate_pct"] = res["cancellation_rate_pct"] or 0.0
    res["total_revenue"] = res["total_revenue"] or 0.0
    return res


def fetch_department_kpis():
    engine = get_db_engine()
    query = """
    SELECT 
        COALESCE(d.department_name, 'General') AS department_name,
        COUNT(a.appointment_id) AS total_visits,
        SUM(CASE WHEN LOWER(a.status) = 'completed' THEN 1 ELSE 0 END) AS completed_visits,
        SUM(CASE WHEN LOWER(a.status) = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_visits,
        ROUND(SUM(CASE WHEN LOWER(a.status) = 'completed' THEN a.consultation_fee ELSE 0 END), 2) AS total_revenue
    FROM appointments a
    LEFT JOIN departments d ON a.department_id = d.department_id
    GROUP BY d.department_name
    ORDER BY total_visits DESC;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df


def fetch_monthly_kpis():
    engine = get_db_engine()
    query = """
    SELECT 
        DATE_FORMAT(appointment_date, '%Y-%m') AS month_year,
        COUNT(appointment_id) AS monthly_visits,
        SUM(CASE WHEN LOWER(status) = 'cancelled' THEN 1 ELSE 0 END) AS monthly_cancellations,
        ROUND(SUM(CASE WHEN LOWER(status) = 'completed' THEN consultation_fee ELSE 0 END), 2) AS monthly_revenue
    FROM appointments
    WHERE appointment_date IS NOT NULL
    GROUP BY DATE_FORMAT(appointment_date, '%Y-%m')
    ORDER BY month_year ASC;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df


def fetch_doctor_performance():
    engine = get_db_engine()
    query = """
    SELECT 
        COALESCE(doc.doctor_name, 'Doctor') AS doctor_name,
        COALESCE(dep.department_name, 'General Medicine') AS department_name,
        COUNT(app.appointment_id) AS total_patients,
        SUM(CASE WHEN LOWER(app.status) = 'completed' THEN app.consultation_fee ELSE 0 END) AS revenue_generated
    FROM appointments app
    LEFT JOIN doctors doc ON app.doctor_id = doc.doctor_id
    LEFT JOIN departments dep ON doc.department_id = dep.department_id
    GROUP BY doc.doctor_name, dep.department_name
    ORDER BY total_patients DESC;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df