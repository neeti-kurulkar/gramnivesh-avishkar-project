# utils/sql_validator.py
import re

def validate_sql(sql: str) -> str:
    """
    Basic SQL validation for PostgreSQL PMAY-G pipeline.

    Rules:
    - Only allow SELECT queries or CTEs (WITH ... SELECT ...)
    - Block dangerous operations
    - Strip extra backticks or triple quotes
    """
    sql = sql.strip()

    # Accept queries starting with SELECT or WITH
    if not (sql.lower().startswith("select") or sql.lower().startswith("with")):
        raise ValueError("Only SELECT queries or CTE-based SELECT queries are allowed.")

    # Forbidden keywords
    forbidden = [
        "delete", "drop", "update", "insert", "truncate", "alter", "grant", "revoke"
    ]
    if any(word in sql.lower() for word in forbidden):
        raise ValueError("Query contains forbidden operations.")

    # Remove extra backticks or triple quotes
    sql = re.sub(r"```", "", sql)
    sql = re.sub(r'"""', "", sql)

    # Optional: ensure no semicolons mid-query except at end
    sql_parts = sql.split(";")
    if len(sql_parts) > 2:
        raise ValueError("Multiple statements detected; only single SELECT allowed.")

    # Return cleaned SQL
    return sql.strip()