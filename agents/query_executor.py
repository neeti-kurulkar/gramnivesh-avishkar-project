# agents/query_executor.py
import os
import psycopg2
import pandas as pd
from utils.sql_validator import validate_sql
from dotenv import load_dotenv

load_dotenv()  # Load DB credentials

DB_PARAMS = {
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT"),
    "dbname": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}

def query_executor_agent(state):
    sql_query = state.get("sql_query", "")
    if not sql_query:
        return {"query_result": "No SQL query provided."}

    try:
        # Validate SQL before executing
        sql_query = validate_sql(sql_query)

        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # If SELECT, fetch results
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            # Convert to list of dicts for downstream processing
            result = [dict(zip(columns, row)) for row in rows]

        else:
            conn.commit()
            result = {"status": "success", "rows_affected": cursor.rowcount}

    except Exception as e:
        result = {"error": str(e)}

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return {"query_result": result}