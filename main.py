import streamlit as st
import pandas as pd
import json
import os
import sys
import time

# --- Auth module path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
auth_dir = os.path.join(current_dir, "Auth")
if auth_dir not in sys.path:
    sys.path.append(auth_dir)

from Auth.auth_json_module import auth_ui
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

# --- Handle logout request ---
if st.session_state.get("logout_request", False):
    st.session_state.logged_in = False
    st.session_state.user = {}
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
    # Input parameters
    file_info, run_agent = render_input_ui(current_dir)

    # Store in session so right_col can access it
    if run_agent:
        st.session_state.run_agent = True

with right_col:
    results_placeholder = st.empty()  # Always keep the heading intact

    # Show results or processing
    if st.session_state.get("run_agent", False):
        from ui.output_ui import run_processing
        run_processing(file_info, current_dir)

    # Render final results below Results heading
    from ui.output_ui import render_results
    render_results(
        df=st.session_state.get("df"),
        kpi_results=st.session_state.get("kpi_results"),
        chart_results=st.session_state.get("chart_results"),
        insight_results=st.session_state.get("insight_results")
    )
