import os
import pandas as pd
import streamlit as st
from Data_loader.data_loader import read_sql_table

def render_input_ui(current_dir):
    st.markdown("### <span style='color:darkblue;font-weight:bold;'>Input Parameters</span>", unsafe_allow_html=True)

    # Step 1: Choose data source
    st.markdown("#### <span style='color:blue;font-weight:bold;'>Choose Data Source</span>", unsafe_allow_html=True)
    data_source = st.selectbox(
        "Select data source",
        ["Sample Data (provided)", "Upload CSV/XLSX", "Database (SQLAlchemy connection)"],
        key="data_source_selectbox"
    )

    file_info = {"type": None, "path_csv": None, "path_xlsx": None, "uploaded": None, "conn": None, "table": None}

    # Step 2: Show relevant input right after selection
    if data_source == "Sample Data (provided)":
        file_info["type"] = "sample"
        file_info["path_csv"] = os.path.join(current_dir, "Data", "bank_transactions.csv")
        file_info["path_xlsx"] = os.path.join(current_dir, "Data", "bank_transactions.xlsx")

    elif data_source == "Upload CSV/XLSX":
        file_info["type"] = "upload"
        st.markdown("#### <span style='color:blue;'>Upload Your File</span>", unsafe_allow_html=True)
        file_info["uploaded"] = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx"],
            key="file_upload"
        )

    elif data_source == "Database (SQLAlchemy connection)":
        file_info["type"] = "db"
        st.markdown("#### <span style='color:blue;'>Database Connection</span>", unsafe_allow_html=True)
        file_info["conn"] = st.text_input("SQLAlchemy connection string", key="db_conn")
        file_info["table"] = st.text_input("Table name", key="db_table")

    # Step 3: Additional inputs
    st.markdown("#### <span style='color:blue;'>Additional Inputs</span>", unsafe_allow_html=True)
    st.file_uploader("Upload sample dashboard image or PDF", type=["png", "jpg", "jpeg", "pdf"], key="sample_upload")
    st.text_area("Dashboard or report requirement", placeholder="Write your requirements here...", key="report_req")

    # Step 4: Run Agent button
    run_agent = st.button("🚀 Run Agent", key="run_agent_btn")
    return file_info, run_agent

def load_dataframe(file_info):
    """Load the actual DataFrame only when needed."""
    df = None
    if file_info["type"] == "sample":
        if os.path.exists(file_info["path_csv"]):
            df = pd.read_csv(file_info["path_csv"], parse_dates=True)
        elif os.path.exists(file_info["path_xlsx"]):
            df = pd.read_excel(file_info["path_xlsx"], parse_dates=True)

    elif file_info["type"] == "upload" and file_info["uploaded"]:
        uploaded = file_info["uploaded"]
        if uploaded.name.lower().endswith(".csv"):
            headers = pd.read_csv(uploaded, nrows=0).columns.tolist()
            date_cols = [c for c in headers if "date" in c.lower()]
            uploaded.seek(0)
            df = pd.read_csv(uploaded, parse_dates=date_cols)
        else:
            headers = pd.read_excel(uploaded, nrows=0).columns.tolist()
            date_cols = [c for c in headers if "date" in c.lower()]
            uploaded.seek(0)
            df = pd.read_excel(uploaded, parse_dates=date_cols)

    elif file_info["type"] == "db" and file_info["conn"] and file_info["table"]:
        df = read_sql_table(file_info["conn"], file_info["table"])

    return df
