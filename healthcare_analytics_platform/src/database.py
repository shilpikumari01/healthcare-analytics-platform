from sqlalchemy import create_engine, text
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
