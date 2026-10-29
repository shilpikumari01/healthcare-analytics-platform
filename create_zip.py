import os
import zipfile

files = {
    'healthcare_analytics_platform/.env.example': '''DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=healthcare_db
DB_PORT=3306
GEMINI_API_KEY=your_google_gemini_api_key_here
''',

    'healthcare_analytics_platform/.gitignore': '''__pycache__/
*.pyc
.env
venv/
.venv/
.vscode/
.idea/
exports/*.xlsx
data/*.json
*.pbix.lock
''',

    'healthcare_analytics_platform/requirements.txt': '''pandas==2.2.2
mysql-connector-python==8.4.0
sqlalchemy==2.0.30
openpyxl==3.1.2
streamlit==1.35.0
python-dotenv==1.0.1
requests==2.32.2
google-generativeai==0.7.1
''',

    'healthcare_analytics_platform/config.py': '''import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "healthcare_db")
DB_PORT = os.getenv("DB_PORT", "3306")

DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
''',

    'healthcare_analytics_platform/schema.sql': '''DROP DATABASE IF EXISTS healthcare_db;
CREATE DATABASE healthcare_db;
USE healthcare_db;

CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20),
    doctor_id INT,
    department_id INT,
    appointment_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    consultation_fee DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);
''',

    'healthcare_analytics_platform/data/raw_healthcare_data.csv': '''Appointment_ID,Patient_ID,Patient_Name,Gender,Age,Doctor_Name,Department,Appointment_Date,Status,Consultation_Fee
APT1001,P101,Aarav Sharma,Male,34,Dr. Rajesh Kumar,Cardiology,2026-01-05,Completed,1500.00
APT1002,P102,Priya Patel,Female,28,Dr. Anita Roy,Dermatology,2026-01-06,Completed,800.00
APT1003,P103,Rohan Verma,Male,45,Dr. Suresh Nair,Orthopedics,2026-01-07,Cancelled,1200.00
APT1004,P104,Sneha Gupta,Female,52,Dr. Rajesh Kumar,Cardiology,2026-01-10,Completed,1500.00
APT1005,P105,Vikram Singh,Male,61,Dr. Meena Iyer,Neurology,2026-01-12,No-Show,1000.00
APT1001,P101,Aarav Sharma,Male,34,Dr. Rajesh Kumar,Cardiology,2026-01-05,Completed,1500.00
APT1006,P106,Ananya Rao,Female,,Dr. Anita Roy,dermatology,2026-01-15,Completed,800.00
APT1007,P107,Karan Malhotra,Male,29,Dr. Suresh Nair,Orthopedics,invalid-date,Completed,1200.00
APT1008,P108,Neha Kapoor,Female,39,Dr. Meena Iyer,NEUROLOGY,2026-02-01,Completed,1000.00
APT1009,P109,Amit Joshi,Male,50,Dr. Rajesh Kumar,Cardiology,2026-02-03,Cancelled,1500.00
APT1010,P110,Pooja Hegde,Female,31,Dr. Anita Roy,Dermatology,2026-02-05,Completed,800.00
APT1011,P111,Siddharth Das,Male,42,Dr. Suresh Nair,orthopedics,2026-02-08,Completed,1200.00
APT1012,P112,Kavita Reddy,Female,67,Dr. Meena Iyer,Neurology,2026-02-12,Completed,1000.00
APT1013,P113,Rahul Mehta,Male,23,Dr. Rajesh Kumar,Cardiology,2026-02-15,Completed,1500.00
APT1014,P114,Divya Menon,Female,36,Dr. Anita Roy,Dermatology,2026-02-18,Cancelled,800.00
APT1015,P115,Gaurav Taneja,Male,48,Dr. Suresh Nair,Orthopedics,2026-02-20,Completed,1200.00
''',

    'healthcare_analytics_platform/src/__init__.py': '',

    'healthcare_analytics_platform/src/database.py': '''from sqlalchemy import create_engine, text
from config import DATABASE_URI

def get_db_engine():
    return create_engine(DATABASE_URI, echo=False)

def test_connection():
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;"))
            return True if result.fetchone() else False
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
''',

    'healthcare_analytics_platform/src/cleaner.py': '''import pandas as pd
import numpy as np
import os
from sqlalchemy import text

def clean_healthcare_data(file_path_or_df):
    if isinstance(file_path_or_df, str):
        df = pd.read_csv(file_path_or_df)
    else:
        df = file_path_or_df.copy()

    quality_metrics = {
        "initial_rows": len(df),
        "duplicate_rows_removed": 0,
        "missing_age_imputed": 0,
        "invalid_dates_removed": 0,
        "standardized_departments": 0,
        "final_rows": 0
    }

    initial_count = len(df)
    df = df.drop_duplicates(subset=["Appointment_ID"])
    quality_metrics["duplicate_rows_removed"] = initial_count - len(df)

    if "Department" in df.columns:
        df["Department"] = df["Department"].astype(str).str.strip().str.title()
        quality_metrics["standardized_departments"] = len(df)

    if "Age" in df.columns:
        df["Age"] = pd.to_numeric(df["Age"], errors='coerce')
        missing_age_count = df["Age"].isna().sum()
        median_age = df["Age"].median() if not np.isnan(df["Age"].median()) else 35
        df["Age"] = df["Age"].fillna(median_age).astype(int)
        quality_metrics["missing_age_imputed"] = int(missing_age_count)

    if "Appointment_Date" in df.columns:
        df["Appointment_Date"] = pd.to_datetime(df["Appointment_Date"], errors='coerce')
        invalid_dates = df["Appointment_Date"].isna().sum()
        df = df.dropna(subset=["Appointment_Date"])
        df["Appointment_Date"] = df["Appointment_Date"].dt.strftime('%Y-%m-%d')
        quality_metrics["invalid_dates_removed"] = int(invalid_dates)

    for str_col in ["Patient_Name", "Doctor_Name", "Status", "Gender"]:
        if str_col in df.columns:
            df[str_col] = df[str_col].astype(str).str.strip()

    if "Consultation_Fee" in df.columns:
        df["Consultation_Fee"] = pd.to_numeric(df["Consultation_Fee"], errors='coerce').fillna(0.0)

    quality_metrics["final_rows"] = len(df)
    return df, quality_metrics

def load_data_to_mysql(cleaned_df):
    from src.database import get_db_engine
    engine = get_db_engine()

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text("TRUNCATE TABLE appointments;"))
        conn.execute(text("TRUNCATE TABLE doctors;"))
        conn.execute(text("TRUNCATE TABLE departments;"))
        conn.execute(text("TRUNCATE TABLE patients;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

        unique_depts = pd.DataFrame({'department_name': cleaned_df['Department'].unique()})
        unique_depts.to_sql('departments', conn, if_exists='append', index=False)
        
        dept_db = pd.read_sql("SELECT department_id, department_name FROM departments", conn)
        
        doc_df = cleaned_df[['Doctor_Name', 'Department']].drop_duplicates()
        doc_df = doc_df.merge(dept_db, left_on='Department', right_on='department_name')
        doc_df = doc_df[['Doctor_Name', 'department_id']].rename(columns={'Doctor_Name': 'doctor_name'})
        doc_df.to_sql('doctors', conn, if_exists='append', index=False)

        doc_db = pd.read_sql("SELECT doctor_id, doctor_name FROM doctors", conn)

        pat_df = cleaned_df[['Patient_ID', 'Patient_Name', 'Gender', 'Age']].drop_duplicates(subset=['Patient_ID'])
        pat_df.columns = ['patient_id', 'patient_name', 'gender', 'age']
        pat_df.to_sql('patients', conn, if_exists='append', index=False)

        app_df = cleaned_df.copy()
        app_df = app_df.merge(dept_db, left_on='Department', right_on='department_name')
        app_df = app_df.merge(doc_db, left_on='Doctor_Name', right_on='doctor_name')
        
        app_final = app_df[[
            'Appointment_ID', 'Patient_ID', 'doctor_id', 'department_id',
            'Appointment_Date', 'Status', 'Consultation_Fee'
        ]].rename(columns={
            'Appointment_ID': 'appointment_id',
            'Patient_ID': 'patient_id',
            'Appointment_Date': 'appointment_date',
            'Status': 'status',
            'Consultation_Fee': 'consultation_fee'
        })
        
        app_final.to_sql('appointments', conn, if_exists='append', index=False)

    return True

def export_to_excel(cleaned_df, quality_report, output_dir="exports"):
    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned_patients_data.xlsx")
    report_path = os.path.join(output_dir, "data_quality_report.xlsx")

    cleaned_df.to_excel(cleaned_path, index=False, engine='openpyxl')
    report_df = pd.DataFrame(list(quality_report.items()), columns=["Metric", "Value"])
    report_df.to_excel(report_path, index=False, engine='openpyxl')

    return cleaned_path, report_path
''',

    'healthcare_analytics_platform/src/kpi_engine.py': '''import pandas as pd
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
''',

    'healthcare_analytics_platform/src/ai_summarizer.py': '''import google.generativeai as genai
import pandas as pd
from config import GEMINI_API_KEY

def generate_template_summary(kpi_data, dept_df):
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
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "your_google_gemini_api_key_here":
        return generate_template_summary(kpi_data, dept_df)

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        dept_summary = dept_df.to_string(index=False) if not dept_df.empty else "No department data available."

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
            return f"### 🤖 AI Executive Summary\\n\\n{response.text}"
        else:
            return generate_template_summary(kpi_data, dept_df)

    except Exception as e:
        return generate_template_summary(kpi_data, dept_df)
''',

    'healthcare_analytics_platform/src/api_fetcher.py': '''import requests
import pandas as pd

def fetch_external_patient_data():
    api_url = "https://jsonplaceholder.typicode.com/users"
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            formatted_data = []
            for user in data:
                formatted_data.append({
                    "Patient_ID": f"API-{user['id']}",
                    "Patient_Name": user["name"],
                    "Contact_Email": user["email"],
                    "City": user["address"]["city"],
                    "Company_Affiliation": user["company"]["name"]
                })
            return pd.DataFrame(formatted_data)
        else:
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        return pd.DataFrame([
            {"Patient_ID": "FB-101", "Patient_Name": "Fallback Patient A", "Contact_Email": "a@example.com", "City": "Delhi", "Company_Affiliation": "General Health"},
            {"Patient_ID": "FB-102", "Patient_Name": "Fallback Patient B", "Contact_Email": "b@example.com", "City": "Mumbai", "Company_Affiliation": "General Health"}
        ])
''',

    'healthcare_analytics_platform/app.py': '''import streamlit as st
import pandas as pd
import os
from src.cleaner import clean_healthcare_data, load_data_to_mysql, export_to_excel
from src.kpi_engine import fetch_summary_kpis, fetch_department_kpis, fetch_monthly_kpis, fetch_doctor_performance
from src.ai_summarizer import generate_executive_summary
from src.api_fetcher import fetch_external_patient_data

st.set_page_config(page_title="Healthcare Analytics Platform", layout="wide")
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
            st.bar_chart(dept_df.set_index("department_name")["total_visits"])

        with col_right:
            st.markdown("### Monthly Trend")
            monthly_df = fetch_monthly_kpis()
            st.dataframe(monthly_df, use_container_width=True)
            if not monthly_df.empty:
                st.line_chart(monthly_df.set_index("month_year")["monthly_visits"])

        st.markdown("### Doctor Performance")
        st.dataframe(fetch_doctor_performance(), use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching metrics from database: {e}. Please run cleaning pipeline.")

with tab2:
    st.subheader("Data Cleaning & Quality Metrics")
    if "quality_report" in st.session_state:
        st.json(st.session_state["quality_report"])
    else:
        st.info("Upload a dataset and click 'Run Data Cleaning' in sidebar to view quality report.")

with tab3:
    st.subheader("GenAI-Powered Executive Summary")
    if st.button("Generate Summary"):
        with st.spinner("Generating summary..."):
            st.markdown(generate_executive_summary(fetch_summary_kpis(), fetch_department_kpis()))

with tab4:
    st.subheader("External API Data Integration")
    if st.button("Fetch API Data"):
        st.dataframe(fetch_external_patient_data(), use_container_width=True)
'''
}

zip_filename = "healthcare_analytics_platform.zip"
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        zip_file.write(path)

print(f"✅ Successfully created ZIP archive: {zip_filename}")