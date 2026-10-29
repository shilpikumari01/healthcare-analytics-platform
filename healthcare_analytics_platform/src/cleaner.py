import pandas as pd
import numpy as np
import os
from sqlalchemy import text

def clean_healthcare_data(file_path_or_df):
    """
    Cleans healthcare dataset:
    - Accepts file path (str), DataFrame, or Streamlit UploadedFile buffer
    """
    if isinstance(file_path_or_df, str):
        df = pd.read_csv(file_path_or_df)
    elif isinstance(file_path_or_df, pd.DataFrame):
        df = file_path_or_df.copy()
    else:
        # Handles Streamlit UploadedFile buffer objects
        df = pd.read_csv(file_path_or_df)

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

if __name__ == "__main__":
    print("⏳ Starting data cleaning pipeline...")
    cleaned_df, report = clean_healthcare_data("data/raw_healthcare_data.csv")
    print("📊 Data Quality Metrics calculated:", report)
    print("💾 Loading clean records into MySQL database...")
    if load_data_to_mysql(cleaned_df):
        print("✅ Data successfully cleaned and loaded into MySQL tables!")