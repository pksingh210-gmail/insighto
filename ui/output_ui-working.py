import streamlit as st
import os
import time
import json
from ui.input_ui import load_dataframe
from Schema_mapper.schema_mapper import infer_field_roles, map_template_fields
from Dashboard.dashboard_generator import generate_kpi, generate_line, generate_bar, generate_pie
from Insight.insight_engine import basic_kpi_insights

def render_topbar():
    user = st.session_state.get("user", {})
    full_name = user.get("name", "User")  # Pull directly from logged-in user

    st.markdown(
        f"""
        <div class="custom-topbar" style="display:flex; justify-content:space-between; align-items:center;">
            <div class="topbar-title">Insighto Agent</div>
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="font-weight:bold; color:#333;">Welcome {full_name}!</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_results(df=None, kpi_results=None, chart_results=None, insight_results=None):
    # --- Heading with Logout button aligned right ---
    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown("### <span style='color:darkblue;font-weight:bold;'>Results</span>", unsafe_allow_html=True)
        # Dedicated placeholder below heading for dynamic messages
        if "results_status_placeholder" not in st.session_state:
            st.session_state["results_status_placeholder"] = st.empty()
    with col2:
        if st.button("Logout", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = {}
            st.rerun()

    # --- Original results rendering ---
    if df is not None:
        tab_dashboard, tab_insights, tab_data = st.tabs(
            ["📊 Dashboard", "💡 Insights", "📄 Data Preview"]
        )

        # --- Dashboard tab ---
        with tab_dashboard:
            if kpi_results:
                cols = st.columns(len(kpi_results))
                for i, k in enumerate(kpi_results):
                    with cols[i]:
                        st.metric(k.get("title", "KPI"), k.get("value", "N/A"))

            if chart_results:
                left_ch, right_ch = st.columns(2)
                for idx, (chart_type, fig) in enumerate(chart_results):
                    if chart_type in ("line", "pie"):
                        left_ch.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
                    else:
                        right_ch.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")

        # --- Insights tab ---
        with tab_insights:
            for i, ins in enumerate(insight_results):
                st.write(f"**Insight {i+1}:** {ins}", key=f"insight_{i}")

        # --- Data Preview tab ---
        with tab_data:
            st.dataframe(df.head(50), use_container_width=True)

    else:
        # Show initial message in status box
        st.session_state["results_status_placeholder"].info("Please provide input data and click 'Run Agent'.")


# --- New function to handle dynamic processing with spinner ---
def run_processing(file_info, current_dir):
    status_box = st.session_state["results_status_placeholder"]
    status_box.empty()  # Clear previous status

    df, roles, mapping, kpi_results, chart_results, insight_results = None, None, None, [], [], []

    # --- Define dynamic steps ---
    steps = [
        ("📂 Loading data", lambda: load_dataframe(file_info)),
        ("🔍 Inferring field roles", lambda: infer_field_roles(df)),
        ("🗺️ Mapping template fields", lambda: map_template_fields(
            json.load(open(os.path.join(current_dir, "Dashboard", "sample_dashboard.json"))) if os.path.exists(os.path.join(current_dir, "Dashboard", "sample_dashboard.json")) else {"title": "Generated Dashboard","layout": []},
            roles
        )),
        ("📊 Generating KPIs", lambda: [generate_kpi(df, c, mapping) for c in json.load(open(os.path.join(current_dir, "Dashboard", "sample_dashboard.json"))) if c.get("type")=="kpi"]),
        ("📈 Generating Charts", lambda: []),  # handled separately below
        ("💡 Generating Insights", lambda: basic_kpi_insights(df))
    ]

    # Step 1: Load Data
    with status_box.container():
        with st.spinner(steps[0][0]+"..."):
            df = steps[0][1]()
            time.sleep(1)

    if df is None:
        status_box.error("❌ Failed to load data file.")
        return

    # Step 2: Infer Field Roles
    with status_box.container():
        with st.spinner(steps[1][0]+"..."):
            roles = steps[1][1]()
            time.sleep(1)

    # Step 3: Map Template Fields
    template_file = os.path.join(current_dir, "Dashboard", "sample_dashboard.json")
    template = json.load(open(template_file)) if os.path.exists(template_file) else {"title": "Generated Dashboard", "layout": []}
    with status_box.container():
        with st.spinner(steps[2][0]+"..."):
            mapping = map_template_fields(template, roles)
            time.sleep(1)

    # Step 4: Generate KPIs
    kpis = [c for c in template.get("layout", []) if c.get("type")=="kpi"]
    with status_box.container():
        for i, comp in enumerate(kpis):
            with st.spinner(f"📊 Generating KPI {i+1}/{len(kpis)}..."):
                kpi_results.append(generate_kpi(df, comp, mapping))
                time.sleep(0.5)

    # Step 5: Generate Charts dynamically
    chart_results = []
    chart_func_map = {
        "line": generate_line,
        "bar": generate_bar,
        "pie": generate_pie,
        # Add new types here if dashboard template includes them
    }
    charts = [c for c in template.get("layout", []) if c.get("type") in chart_func_map]

    for i, comp in enumerate(charts):
        chart_type = comp.get("type")
        func = chart_func_map.get(chart_type)
        if func:
            with status_box:
                with st.spinner(f"📈 Generating {chart_type} chart {i+1}/{len(charts)}..."):
                    fig = func(df, comp, mapping)
                    chart_results.append((chart_type, fig))
                    time.sleep(1.0)

    # Step 6: Generate Insights
    with status_box.container():
        with st.spinner(steps[5][0]+"..."):
            insight_results = basic_kpi_insights(df)
            time.sleep(0.5)

    # Store results in session
    st.session_state["df"] = df
    st.session_state["kpi_results"] = kpi_results
    st.session_state["chart_results"] = chart_results
    st.session_state["insight_results"] = insight_results

