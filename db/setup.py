import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import numpy as np

# ----------------------------
# Load .env
# ----------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# ----------------------------
# Paths
# ----------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_SCHEMA_FILE = os.path.join(PROJECT_ROOT, "schema.sql")
EXCEL_FOLDER = os.path.join(PROJECT_ROOT, "excel")

# List of values representing missing data
NA_VALUES = ["N.A.", "NA", "na", "-", "--", "", " "]

# ----------------------------
# Helper function to execute SQL
# ----------------------------
def execute_sql(cursor, sql, params=None):
    cursor.execute(sql, params or ())

def get_indicator_id(cursor, name):
    cursor.execute("SELECT indicator_id FROM pmayg_indicator WHERE name = %s", (name.strip(),))
    result = cursor.fetchone()
    return result[0] if result else None

# ----------------------------
# Load schema
# ----------------------------
def load_schema(cursor):
    with open(DB_SCHEMA_FILE, "r") as f:
        cursor.execute(f.read())
    print("[INFO] Database schema loaded.")

# ----------------------------
# Load indicators
# ----------------------------
def load_indicators(cursor):
    indicators = [
        ("SC", "beneficiary"),
        ("ST", "beneficiary"),
        ("Minority", "beneficiary"),
        ("Others", "beneficiary"),
        ("Total", "beneficiary"),
        ("Opening Balance", "fund_flow"),
        ("Allocated_Central", "fund_flow"),
        ("Allocated_State", "fund_flow"),
        ("Allocated_Total", "fund_flow"),
        ("Released_Central", "fund_flow"),
        ("Released_ State", "fund_flow"),
        ("Released_Total", "fund_flow"),
        ("Total Available Funds", "fund_flow"),
        ("Utilization of Funds", "fund_flow"),
        ("Percentage Utilization", "fund_flow"),
    ]
    for name, type_ in indicators:
        execute_sql(
            cursor,
            "INSERT INTO pmayg_indicator (name, type) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (name, type_),
        )
    print("[INFO] Indicators loaded.")

# ----------------------------
# Create report
# ----------------------------
def create_report(cursor, report_type="allocation", report_date=None, source_file=None):
    if report_date is None:
        report_date = pd.Timestamp.now()
    execute_sql(
        cursor,
        """INSERT INTO pmayg_report (report_type, report_date, source_file)
           VALUES (%s, %s, %s) RETURNING report_id""",
        (report_type, report_date, source_file)
    )
    report_id = cursor.fetchone()[0]
    print(f"[INFO] Report created with report_id={report_id}")
    return report_id

# ----------------------------
# Load hierarchical data
# ----------------------------
def load_geography_and_facts(cursor, report_id):
    state_map = {}
    district_map = {}
    block_map = {}

    # --------------------
    # Level 1: States
    # --------------------
    df_states = pd.read_excel(os.path.join(EXCEL_FOLDER, "01_states.xlsx"))
    df_states.columns = [str(c).strip() for c in df_states.columns]
    df_states.replace(NA_VALUES, np.nan, inplace=True)
    df_states = df_states[df_states["State Name"].notna()]
    df_states = df_states[~df_states["State Name"].str.strip().str.lower().isin(["total", "grand total"])]

    for _, row in df_states.iterrows():
        state_name = str(row["State Name"]).strip()
        execute_sql(cursor, "INSERT INTO pmayg_state (name) VALUES (%s) RETURNING state_id", (state_name,))
        state_id = cursor.fetchone()[0]
        state_map[state_name.lower()] = state_id

        for col in df_states.columns[2:]:
            indicator_id = get_indicator_id(cursor, col)
            if indicator_id:
                amount = row[col] if pd.notna(row[col]) else None
                execute_sql(
                    cursor,
                    "INSERT INTO pmayg_fund_fact (report_id, state_id, indicator_id, amount) VALUES (%s, %s, %s, %s)",
                    (report_id, state_id, indicator_id, amount),
                )

    # --------------------
    # Level 2: Districts
    # --------------------
    for file in os.listdir(EXCEL_FOLDER):
        if file.startswith("02_") and file.endswith(".xlsx"):
            state_name = file.split("_")[1].lower()  # e.g., 'maharashtra'
            df = pd.read_excel(os.path.join(EXCEL_FOLDER, file))
            df.columns = [str(c).strip() for c in df.columns]
            df.replace(NA_VALUES, np.nan, inplace=True)
            df = df[df["District Name"].notna()]
            df = df[~df["District Name"].str.strip().str.lower().isin(["total", "grand total"])]
            state_id = state_map[state_name]

            for _, row in df.iterrows():
                district_name = str(row["District Name"]).strip()
                execute_sql(cursor, "INSERT INTO pmayg_district (state_id, name) VALUES (%s, %s) RETURNING district_id",
                            (state_id, district_name))
                district_id = cursor.fetchone()[0]
                district_map[(state_name, district_name.lower())] = district_id

                for col in df.columns[1:]:
                    indicator_id = get_indicator_id(cursor, col)
                    if indicator_id:
                        amount = row[col] if pd.notna(row[col]) else None
                        execute_sql(cursor,
                                    "INSERT INTO pmayg_fund_fact (report_id, district_id, indicator_id, amount) VALUES (%s, %s, %s, %s)",
                                    (report_id, district_id, indicator_id, amount))

    # --------------------
    # Level 3: Blocks
    # --------------------
    for file in os.listdir(EXCEL_FOLDER):
        if file.startswith("03_") and file.endswith(".xlsx"):
            district_name = file.split("_")[1].lower()  # e.g., 'pune'
            df = pd.read_excel(os.path.join(EXCEL_FOLDER, file))
            df.columns = [str(c).strip() for c in df.columns]
            df.replace(NA_VALUES, np.nan, inplace=True)
            df = df[df["Block Name"].notna()]
            df = df[~df["Block Name"].str.strip().str.lower().isin(["total", "grand total"])]

            parent = next(((s, d) for (s, d) in district_map if d == district_name), None)
            if not parent:
                continue
            state_name, district_name = parent
            state_id = state_map[state_name]
            district_id = district_map[(state_name, district_name)]

            for _, row in df.iterrows():
                block_name = str(row["Block Name"]).strip()
                execute_sql(cursor, "INSERT INTO pmayg_block (district_id, name) VALUES (%s, %s) RETURNING block_id",
                            (district_id, block_name))
                block_id = cursor.fetchone()[0]
                block_map[(state_name, district_name, block_name.lower())] = block_id

                for col in df.columns[1:]:
                    indicator_id = get_indicator_id(cursor, col)
                    if indicator_id:
                        amount = row[col] if pd.notna(row[col]) else None
                        execute_sql(cursor,
                                    "INSERT INTO pmayg_fund_fact (report_id, block_id, indicator_id, amount) VALUES (%s, %s, %s, %s)",
                                    (report_id, block_id, indicator_id, amount))

    # --------------------
    # Level 4: Panchayats
    # --------------------
    for file in os.listdir(EXCEL_FOLDER):
        if file.startswith("04_") and file.endswith(".xlsx"):
            block_name = file.split("_")[1].lower()
            df = pd.read_excel(os.path.join(EXCEL_FOLDER, file))
            df.columns = [str(c).strip() for c in df.columns]
            df.replace(NA_VALUES, np.nan, inplace=True)
            df = df[df["Panchayat Name"].notna()]
            df = df[~df["Panchayat Name"].str.strip().str.lower().isin(["total", "grand total"])]

            parent = next(((s, d, b) for (s, d, b) in block_map if b == block_name), None)
            if not parent:
                continue
            state_name, district_name, block_name = parent
            block_id = block_map[(state_name, district_name, block_name)]

            for _, row in df.iterrows():
                panchayat_name = str(row["Panchayat Name"]).strip()
                execute_sql(cursor, "INSERT INTO pmayg_panchayat (block_id, name) VALUES (%s, %s) RETURNING panchayat_id",
                            (block_id, panchayat_name))
                panchayat_id = cursor.fetchone()[0]

                for col in df.columns[1:]:
                    indicator_id = get_indicator_id(cursor, col)
                    if indicator_id:
                        amount = row[col] if pd.notna(row[col]) else None
                        execute_sql(cursor,
                                    "INSERT INTO pmayg_fund_fact (report_id, panchayat_id, indicator_id, amount) VALUES (%s, %s, %s, %s)",
                                    (report_id, panchayat_id, indicator_id, amount))


# ----------------------------
# Main
# ----------------------------
def main():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cursor = conn.cursor()

    load_schema(cursor)
    conn.commit()

    load_indicators(cursor)
    conn.commit()

    report_id = create_report(cursor)
    conn.commit()

    load_geography_and_facts(cursor, report_id)
    conn.commit()

    cursor.close()
    conn.close()
    print("[INFO] PMAY-G database setup completed.")


if __name__ == "__main__":
    main()