import streamlit as st
import re
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px

from langgraph.graph import StateGraph, END
from utils.state import State
from agents.text_to_sql import text_to_sql_agent
from agents.query_executor import query_executor_agent
from agents.insight_generator import insights_agent
from agents.summary_agent import company_summary_agent
from agents.visualization_agent import visualization_agent  # new

load_dotenv()  # Load DB credentials

DB_PARAMS = {
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT"),
    "dbname": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}

# ---------------- Streamlit Page Setup ----------------
st.set_page_config(page_title="PMAY-G Insights Dashboard", layout="wide", page_icon="🏘️")

# ---------------- State Graph Setup ----------------
graph = StateGraph(State)
graph.add_node("text_to_sql", text_to_sql_agent)
graph.add_node("query_executor", query_executor_agent)
graph.add_node("insights", insights_agent)
graph.add_node("visualization", visualization_agent)  # new node
graph.set_entry_point("text_to_sql")

# Edges
graph.add_edge("text_to_sql", "query_executor")
graph.add_edge("query_executor", "insights")
graph.add_edge("query_executor", "visualization")  # query result flows to visualization
graph.add_edge("insights", END)
graph.add_edge("visualization", END)
app = graph.compile()

# ---------------- Sidebar ----------------
st.sidebar.title("PMAY-G Insights")
page = st.sidebar.radio("Navigate to", ["Home", "Ask a Question", "View Data"], index=0)

# ---------------- Home Page ----------------
if page == "Home":
    st.title("🏠 PMAY-G Insights Dashboard")
    st.markdown("### Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Objectives**
        - Safe and durable housing for all rural households
        - Essential amenities: toilets, electricity, LPG, drinking water
        - Promote gender equity in ownership
        - Train rural masons for construction quality
        """)
    with col2:
        st.markdown("""
        **Key Features**
        - Financial assistance via DBT in installments
        - Minimum house size: 25 sq. meters
        - Cost-sharing: 60:40 (plain areas), 90:10 (NE/Himalayan)
        - Aligns with other flagship programs (Swachh Bharat, Ujjwala, Saubhagya)
        """)

    st.markdown("#### Implementation Framework")
    st.info("""
    - Beneficiaries construct houses with trained masons  
    - Gram Panchayats facilitate identification & participation  
    - District & State authorities provide technical support & monitor progress  
    - Central Government provides financial assistance & policy guidance
    """)

    st.markdown("#### Achievements & Progress")
    st.metric("Target Houses by 2024", "2.95 Crore")
    st.markdown("- Significant progress achieved across multiple states\n- Many rural households now have safe housing")

    st.markdown("#### Challenges & Way Forward")
    st.warning("""
    - Construction delays due to material & labor costs  
    - Accurate beneficiary identification needed  
    - Continuous monitoring for quality assurance
    """)

    st.markdown("#### About This Dashboard")
    st.success("""
    This dashboard allows you to explore **fund allocations, utilization, and beneficiary distributions** across
    state, district, block, and panchayat levels. You can ask questions, compare allocations, and identify trends
    in the PMAY-G program.
    """)

# ---------------- Ask a Question Page ----------------
elif page == "Ask a Question":
    st.title("💬 Ask a PMAY-G Question")

    # Company Summary
    if "company_summary" not in st.session_state:
        with st.spinner("Generating PMAY-G summary..."):
            summary_output = company_summary_agent({})
            st.session_state.company_summary = summary_output.get("summary", "Summary not available.")
    else:
        summary_output = {"summary": st.session_state.company_summary}

    st.subheader("🏢 PMAY-G Overview")
    st.info(summary_output["summary"])

    # Example Questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What is the total allocation versus total released funds in Maharashtra?  
        - Which beneficiary category received the most funds in Pune district?  
        - Which beneficiary category is most underrepresented in Khed block?  
        - Show allocations for all beneficiary categories in Khed block.  
        """)

    # User Query Input
    user_query = st.text_input(
        "Enter your question here",
        value=st.session_state.get("user_query", "")
    )

    if st.button("Submit") and user_query:
        st.session_state.user_query = user_query
        with st.spinner("Generating SQL, Insights, and Visualizations..."):
            output = app.invoke({"messages": [user_query]})
            st.session_state.query_output = output

    # Display Output
    if "query_output" in st.session_state:
        output = st.session_state.query_output

        tabs = st.tabs(["Insights", "Generated SQL Query", "Query Result", "Visualization"])

        # SQL Query
        with tabs[1]:
            st.subheader("SQL Query Generated")
            st.code(output.get("sql_query", "N/A"))

        # Query Result
        with tabs[2]:
            st.subheader("Query Result")
            result = output.get("query_result", None)
            if isinstance(result, list) and result:
                df = pd.DataFrame(result).fillna(0)
                st.dataframe(df)
            elif isinstance(result, pd.DataFrame):
                df = result.fillna(0)
                st.dataframe(df)
            else:
                st.write(result if result else "No data returned.")

        # Insights
        with tabs[0]:
            st.subheader("Insights")
            insights_text = output.get("insights", "No insights generated.")
            insights_text = re.sub(r'\n+', '\n', insights_text)
            insights_text = re.sub(r'\s+\n', '\n', insights_text)
            insights_text = insights_text.strip()
            st.success(insights_text)

        # Visualization
        with tabs[3]:
            fig = output.get("visualization", None)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No visualization available for this query.")

# ---------------- View Data Page ----------------
elif page == "View Data":
    st.title("📊 View PMAY-G Excel Sheets")

    excel_files = {
        "pmayg_state": "01_states.xlsx",
        "pmayg_district": "02_maharashtra_districts.xlsx",
        "pmayg_block": "03_pune_blocks.xlsx",
        "pmayg_panchayat": "04_khed_panchayats.xlsx",
    }

    table_name = st.selectbox("Select table to view", list(excel_files.keys()))

    if table_name:
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        EXCEL_FOLDER = os.path.join(PROJECT_ROOT, "db", "excel")
        file_name = excel_files[table_name]
        file_path = os.path.join(EXCEL_FOLDER, file_name)

        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df.columns = [str(c).strip() for c in df.columns]
            st.dataframe(df)
        else:
            st.warning(f"Excel file for {table_name} not found at {file_path}")