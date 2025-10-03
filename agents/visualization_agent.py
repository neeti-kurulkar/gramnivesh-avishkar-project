# agents/visualization_agent.py
import pandas as pd
import plotly.express as px

def visualization_agent(state):
    """
    Generates visualizations based on SQL query results.
    Input:
        state: dict with key 'query_result' containing list of dicts or a DataFrame
    Output:
        dict with 'visualization' key containing a Plotly figure
    """
    result = state.get("query_result", None)
    fig = None

    # Convert list of dicts to DataFrame if needed
    if isinstance(result, list) and result:
        df = pd.DataFrame(result)
    elif isinstance(result, pd.DataFrame):
        df = result.copy()
    else:
        return {"visualization": None}

    # Remove empty columns
    df = df.dropna(axis=1, how='all')

    # --- Detect suitable chart types ---
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    # Simple heuristic: one categorical + one numeric column -> bar chart
    if len(numeric_cols) == 1 and len(categorical_cols) == 1:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        fig = px.bar(
            df,
            x=cat_col,
            y=num_col,
            text=num_col,
            title=f"{num_col} by {cat_col}",
            labels={cat_col: cat_col, num_col: num_col},
            color=cat_col
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(yaxis_title=f"{num_col} (in lakhs)", xaxis_title=cat_col, uniformtext_minsize=8, uniformtext_mode='hide')

    # Multiple numeric columns & categorical -> grouped bar chart
    elif len(numeric_cols) > 1 and len(categorical_cols) == 1:
        fig = px.bar(
            df,
            x=categorical_cols[0],
            y=numeric_cols,
            barmode='group',
            title=f"Comparison of {', '.join(numeric_cols)} by {categorical_cols[0]}"
        )

    # Time series (date + numeric) could be added here as a future enhancement

    return {"visualization": fig}