from agents.llm_client import llm
import pandas as pd

def insights_agent(state):
    result = state.get("query_result", None)
    query = state.get("user_query", "")
    sql = state.get("sql_query", "")

    # ---------------- Preprocess the result ----------------
    def preprocess_result(result):
        if isinstance(result, pd.DataFrame):
            return result.to_dict(orient="records")
        elif isinstance(result, list):
            return result if result else "No relevant data found."
        return str(result) if result else "No relevant data found."

    clean_result = preprocess_result(result)

    # ---------------- Build prompt ----------------
    prompt = f"""
You are an expert analyst evaluating government fund allocation and utilization at multiple levels (state, district, block, panchayat). Use clear, professional language.

Query result (already processed):
{clean_result}
All numeric values are in lakhs.
If a column has the value "Total", it represents the sum across all beneficiary categories (SC, ST, Minority, Others). 
It does not represent a separate beneficiary category.

User's question:
{query}

Instructions:
1. Begin your response by directly answering the user's question in one clear sentence.
2. Then provide a concise, readable summary of any notable insights supported by the data. Include only what is relevant to the question.
3. Use bullets or numbered points if helpful, but do not force a fixed number of points.
4. Highlight relative magnitudes, percentages, or patterns only if they help explain the data.
5. Avoid inventing numbers or assuming data that isn’t present.
6. If the query returns no data, state that concisely.


Focus on making the data interpretable and meaningful for the user's question.
Always answer the user's question directly and clearly FIRST.
ONLY RETURN INSIGHTS. DO NOT RETURN SQL OR RAW DATA. DO NOT REPEAT THE USER'S QUESTION.
"""
    
    response = llm.invoke(prompt)
    return {"insights": response.content}
