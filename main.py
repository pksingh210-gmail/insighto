import os
import sys
import streamlit as st
import pandas as pd
import json
import time

# --- Add project root so packages are discoverable ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
if project_root not in sys.path:
    sys.path.append(project_root)

from auth.auth_json_module import auth_ui
from Schema_mapper.schema_mapper import infer_field_roles, map_template_fields
from Dashboard.dashboard_generator import generate_kpi, generate_line, generate_bar, generate_pie
from Insight.insight_engine import basic_kpi_insights
from ui.input_ui import render_input_ui, load_dataframe
from ui.output_ui import render_results, render_topbar, run_processing

# --- Streamlit config ---
st.set_page_config(page_title="Insighto Agent", layout="wide")

# --- Clear session on first load ---
if "initialized" not in st.session_state:
    st.session_state.clear()
    st.session_state.logged_in = False
    st.session_state.initialized = True

# --- Handle logout request (fast) ---
if st.session_state.get("logout_request", False):
    keys_to_clear = [
        "logged_in", "user", "run_agent", "df",
        "kpi_results", "chart_results", "insight_results",
        "file_info"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.logout_request = False
    st.rerun()

# --- Show login if not logged in ---
if not st.session_state.get("logged_in", False):
    auth_ui()
    st.stop()

# --- Load CSS ---
css_file = os.path.join(current_dir, "ui", "style.css")
if os.path.exists(css_file):
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Top Bar ---
render_topbar()

# --- Admin check ---
if st.session_state.user.get("is_admin", False):
    from Auth.auth_module import admin_panel
    admin_panel()
    st.stop()

# --- Layout ---
left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    st.markdown("### <span style='color:darkblue;font-weight:bold;'>Input Parameters</span>", unsafe_allow_html=True)

    # Render input UI (returns file_info dict)
    file_info, _ = render_input_ui(current_dir)
    st.session_state.file_info = file_info  # store for access in right_col

    # Determine button states
    run_agent_enabled = (
        file_info.get("type") is not None and
        (file_info.get("uploaded") or file_info.get("path_csv") or file_info.get("path_xlsx") or file_info.get("conn"))
    )
    reset_enabled = any(st.session_state.get(k) for k in ["df", "kpi_results", "chart_results", "insight_results"])

    # Buttons in one row: Run Agent left, Reset right
    run_col, reset_col = st.columns([1, 1])

    with run_col:
        if run_agent_enabled:
            if st.button("🚀 Run Agent", key="run_agent_btn"):
                st.session_state.run_agent = True
        else:
            st.markdown("<div style='color:gray;'>🚀 Run Agent (select parameters)</div>", unsafe_allow_html=True)

    with reset_col:
        if reset_enabled:
            if st.button("🔄 Reset Inputs & Results"):
                keys_to_reset = ["file_info", "run_agent", "df", "kpi_results", "chart_results", "insight_results"]
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            st.markdown("<div style='color:gray;'>🔄 Reset (no results)</div>", unsafe_allow_html=True)

with right_col:
    results_placeholder = st.empty()  # Always keep the heading intact

    # Show results or processing
    if st.session_state.get("run_agent", False):
        run_processing(st.session_state.file_info, current_dir)

    # Render final results below Results heading
    render_results(
        df=st.session_state.get("df"),
        kpi_results=st.session_state.get("kpi_results"),
        chart_results=st.session_state.get("chart_results"),
        insight_results=st.session_state.get("insight_results")
    )

