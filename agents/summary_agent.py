# agents/summary_agent.py
from agents.llm_client import llm
import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT"),
    "dbname": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}

def query_db(query):
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

def company_summary_agent(state=None):
    # ----------------- State-level fund summary -----------------
    state_df = query_db("""
        SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
        FROM pmayg_fund_fact ff
        JOIN pmayg_state s ON ff.state_id = s.state_id
        JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
        WHERE i.name IN ('Allocated_Total','Released_Total','Total Available Funds','Utilization of Funds','Percentage Utilization')
        GROUP BY i.name
    """)

    # ----------------- District/Block beneficiary summary -----------------
    beneficiary_df = query_db("""
        SELECT b.name AS block_name, i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
        FROM pmayg_fund_fact ff
        JOIN pmayg_block b ON ff.block_id = b.block_id
        JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
        WHERE i.name IN ('SC','ST','Minority','Others','Total')
        GROUP BY b.name, i.name
    """)

    summary_data = {
        "State Fund Flow Summary": state_df.to_dict(orient="records"),
        "Block Beneficiary Summary": beneficiary_df.to_dict(orient="records")
    }

    prompt = f"""
You are a social sector analyst reviewing PMAY-G program.

State-level fund flow summary:
{summary_data['State Fund Flow Summary']}

Block-level beneficiary summary:
{summary_data['Block Beneficiary Summary']}

Write a concise, high-level summary (10-15 lines):
- Include fund allocation, release, utilization, percentage utilization.
- Include beneficiary counts by block and category.
- Highlight underutilization or anomalies.
- Avoid mechanically repeating numbers.
- If no data exists at a level, mention it clearly.
"""

    response = llm.invoke(prompt)
    return {"summary": response.content}