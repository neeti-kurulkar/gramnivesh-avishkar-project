from agents.llm_client import llm
from few_shot_examples.examples import examples

# Build few-shot prompt
FEW_SHOT_PROMPT = "\n".join([f"Q: {ex['query']}\nSQL: {ex['sql']}" for ex in examples])

# PostgreSQL-compatible PMAY-G schema
SCHEMA = """
Table pmayg_state(state_id SERIAL PRIMARY KEY, name TEXT)
Table pmayg_district(district_id SERIAL PRIMARY KEY, state_id INT, name TEXT)
Table pmayg_block(block_id SERIAL PRIMARY KEY, district_id INT, name TEXT)
Table pmayg_panchayat(panchayat_id SERIAL PRIMARY KEY, block_id INT, name TEXT)
Table pmayg_indicator(indicator_id SERIAL PRIMARY KEY, name TEXT, type TEXT)
Table pmayg_report(report_id SERIAL PRIMARY KEY, report_type TEXT, report_date TIMESTAMP, source_file TEXT)
Table pmayg_fund_fact(fact_id SERIAL PRIMARY KEY, report_id INT, state_id INT, district_id INT, block_id INT, panchayat_id INT, indicator_id INT, amount NUMERIC)
"""

SYSTEM_PROMPT = f"""
You are a PostgreSQL SQL assistant specialized in PMAY-G fund allocation data.

Hierarchy rules:
- Block / Panchayat / District level: only beneficiary indicators exist (SC, ST, Minority, Others, Total)
- State level: all fund flow indicators exist (Allocated_Total, Released_Total, Total Available Funds, Utilization of Funds, Percentage Utilization)
- Always use the most specific geographic level mentioned for beneficiary queries.
- For fund flow queries, always query at state level.

Rules:
1. Output ONLY ONE SQL query, no explanations.
2. Use COALESCE(column,0) for SUM aggregates.
3. Avoid window functions unless strictly necessary.
4. All selected columns must be aggregated or in GROUP BY.
5. Use clear aliases.
6. Follow PostgreSQL syntax strictly.

For questions asking about most/least, return all rows, do not limit.

Database schema:
{SCHEMA}
"""

def text_to_sql_agent(state):
    user_query = state["messages"][-1]

    prompt = f"""{SYSTEM_PROMPT}

Few-shot examples:
{FEW_SHOT_PROMPT}

Q: {user_query}
SQL:"""

    response = llm.invoke(prompt)
    sql_raw = response.content.strip()

    # Extract first SELECT statement
    select_index = sql_raw.lower().find("select")
    if select_index == -1:
        raise ValueError("No SELECT statement found in LLM output")

    sql_clean = sql_raw[select_index:].strip().rstrip(";")  # remove trailing semicolons
    sql_clean += ";"  # ensure exactly one semicolon

    return {"sql_query": sql_clean}