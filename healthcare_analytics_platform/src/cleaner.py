import io
import pandas as pd
from sqlalchemy import create_engine

# MySQL Connection config fallback
try:
    from config import MYSQL_CONFIG
except ImportError:
    MYSQL_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "healthcare_db",
        "port": 3306,
    }


def clean_healthcare_data(uploaded_file):
    """
    Cleans and standardizes raw healthcare CSV uploads.
    Handles column name variations (lowercase/uppercase/case-insensitive).
    """
    df = pd.read_csv(uploaded_file)
    initial_rows = len(df)

    # Standardize Column Names
    column_mapping = {
        "appointment_id": "Appointment_ID",
        "patient_name": "Patient_Name",
        "appointment_date": "Appointment_Date",
        "department_name": "Department_Name",
        "status": "Status",
        "billing_amount": "Billing_Amount",
    }

    df.columns = df.columns.str.strip()
    df.rename(
        columns={
            col: column_mapping[col.lower()]
            for col in df.columns
            if col.lower() in column_mapping
        },
        inplace=True,
    )

    id_col = "Appointment_ID" if "Appointment_ID" in df.columns else df.columns[0]

    # Deduplicate & Clean Numeric/Date Fields
    df.drop_duplicates(subset=[id_col], inplace=True)

    if "Billing_Amount" in df.columns:
        df["Billing_Amount"] = pd.to_numeric(
            df["Billing_Amount"], errors="coerce"
        ).fillna(0.0)

    if "Appointment_Date" in df.columns:
        df["Appointment_Date"] = pd.to_datetime(
            df["Appointment_Date"], errors="coerce"
        )

    final_rows = len(df)

    quality_report = {
        "Initial Records": initial_rows,
        "Cleaned Records": final_rows,
        "Duplicates Removed": initial_rows - final_rows,
        "Missing Values Handled": str(df.isnull().sum().to_dict()),
    }

    return df, quality_report


def load_data_to_mysql(df, table_name="appointments"):
    """Syncs cleaned DataFrame back into MySQL database."""
    try:
        user = MYSQL_CONFIG.get("user", "root")
        password = MYSQL_CONFIG.get("password", "")
        host = MYSQL_CONFIG.get("host", "localhost")
        port = MYSQL_CONFIG.get("port", 3306)
        db = MYSQL_CONFIG.get("database", "healthcare_db")

        connection_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        engine = create_engine(connection_str)

        df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)
        return True, "Data successfully synced to MySQL database."
    except Exception as e:
        return False, f"Database Sync Failed: {str(e)}"


def export_to_excel(df, quality_report=None):
    """
    Exports cleaned dataframe and optional quality report to Excel binary stream.
    Accepts 1 or 2 positional arguments as called by app.py.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned_Data")

        if quality_report is not None:
            if isinstance(quality_report, dict):
                report_df = pd.DataFrame(
                    list(quality_report.items()), columns=["Metric", "Value"]
                )
            else:
                report_df = pd.DataFrame([quality_report])
            report_df.to_excel(
                writer, index=False, sheet_name="Data_Quality_Report"
            )

    return output.getvalue()