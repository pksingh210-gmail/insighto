
Prama-dashboard-agent - Free Dashboard Agent (Banking Demo)
==========================================================

This is a free, modular Streamlit app that generates an interactive dashboard and analytical insights
from either a sample CSV, an uploaded CSV, or a SQLAlchemy-connected database table.

Files included:
- app.py                     : Streamlit entrypoint
- data_loader.py             : CSV/SQL loading utilities
- schema_mapper.py           : Heuristic schema / field mapping
- dashboard_generator.py     : Plotly figure generation per template
- insight_engine.py          : Extended insights (rule-based) + LLM hook
- db_wizard.py               : DB connection builder & tester for common DBs
- ollama_client.py           : Example Ollama HTTP client for local LLMs
- create_project.py          : Script to scaffold the project on a new machine
- bank_transactions.csv      : Sample banking CSV data
- sample_dashboard.json      : Template used to generate the dashboard

Quick start (local):
1) Create virtualenv and activate:
   python -m venv .venv
   source .venv/bin/activate   # mac/linux
   .venv\Scripts\activate    # windows

2) Install Python dependencies:
   pip install streamlit pandas plotly sqlalchemy requests pymysql psycopg2-binary pyodbc

   Note: Install only the drivers you need. For MySQL use pymysql; for Postgres use psycopg2-binary; for MSSQL use pyodbc and an ODBC driver.

3) Run the app:
   streamlit run app.py

DB Wizard usage:
- Use the DB Wizard helper to build SQLAlchemy connection strings. Example:
  from db_wizard import build_sqlalchemy_string, test_db_connection
  conn = build_sqlalchemy_string('postgresql','dbhost.example.com',5432,'mydb','user','pass')
  ok, msg = test_db_connection(conn, table='transactions')
- Hive, HBase, and Iceberg often require specialised clients. db_wizard provides guidance placeholders for these systems.
  - Hive: PyHive / SQLAlchemy hive dialect
  - HBase: happybase (Thrift) or HBase REST endpoints
  - Iceberg: access via Spark or PyIceberg

Ollama (optional, free local LLM):
- Install Ollama: https://ollama.ai
- Pull a model locally (example): ollama pull llama3
- Ensure Ollama daemon is running.
- The app will try to detect Ollama and can use ollama_client.ollama_model_client(prompt) to polish insights.
- If Ollama isn't available, the app uses built-in rule-based insights.

Customising templates:
- Edit sample_dashboard.json to change layout, chart types and fields.
- Use the create_project.py script to scaffold copies of this project onto other machines.



SQLite demo:
- A sample SQLite database 'sample_data.sqlite' with table 'transactions' is included.
- Use DB Wizard in the Streamlit sidebar to build a connection string like sqlite:///sample_data.sqlite and test it.

Ollama integrated UI:
- The app detects Ollama automatically and you can toggle 'Polish insights using Ollama' in the sidebar. Provide the model name (e.g., llama3).
