import pandas as pd
from sqlalchemy import text
from src.database import get_db_engine

def fetch_summary_kpis():
    engine = get_db_engine()
    query = """
    SELECT 
        COUNT(a.appointment_id) AS total_appointments,
        SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed_appointments,
        SUM(CASE WHEN a.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_appointments,
        SUM(CASE WHEN a.status = 'No-Show' THEN 1 ELSE 0 END) AS noshow_appointments,
        ROUND((SUM(CASE WHEN a.status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.appointment_id)), 2) AS cancellation_rate_pct,
        SUM(CASE WHEN a.status = 'Completed' THEN a.consultation_fee ELSE 0 END) AS total_revenue
    FROM appointments a;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df.to_dict(orient="records")[0]

def fetch_department_kpis():
    engine = get_db_engine()
    query = """
    SELECT 
        d.department_name,
        COUNT(a.appointment_id) AS total_visits,
        SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed_visits,
        SUM(CASE WHEN a.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_visits,
        ROUND(SUM(CASE WHEN a.status = 'Completed' THEN a.consultation_fee ELSE 0 END), 2) AS total_revenue
    FROM departments d
    LEFT JOIN appointments a ON d.department_id = a.department_id
    GROUP BY d.department_id, d.department_name
    ORDER BY total_visits DESC;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df

def fetch_monthly_kpis():
    engine = get_db_engine()
    query = """
    SELECT 
        DATE_FORMAT(a.appointment_date, '%Y-%m') AS month_year,
        COUNT(a.appointment_id) AS monthly_visits,
        SUM(CASE WHEN a.status = 'Cancelled' THEN 1 ELSE 0 END) AS monthly_cancellations,
        ROUND(SUM(CASE WHEN a.status = 'Completed' THEN a.consultation_fee ELSE 0 END), 2) AS monthly_revenue
    FROM appointments a
    GROUP BY DATE_FORMAT(a.appointment_date, '%Y-%m')
    ORDER BY month_year ASC;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df

def fetch_doctor_performance():
    engine = get_db_engine()
    query = """
    WITH DoctorStats AS (
        SELECT 
            doc.doctor_name,
            dep.department_name,
            COUNT(app.appointment_id) AS total_patients,
            SUM(CASE WHEN app.status = 'Completed' THEN app.consultation_fee ELSE 0 END) AS revenue_generated
        FROM doctors doc
        JOIN departments dep ON doc.department_id = dep.department_id
        LEFT JOIN appointments app ON doc.doctor_id = app.doctor_id
        GROUP BY doc.doctor_id, doc.doctor_name, dep.department_name
    )
    SELECT doctor_name, department_name, total_patients, revenue_generated
    FROM DoctorStats
    ORDER BY total_patients DESC;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)
    return df
