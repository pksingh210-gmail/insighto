"""
db_wizard.py
- Helpers to build SQLAlchemy connection strings and test connectivity for common DBs:
  - PostgreSQL, MySQL, MSSQL (pyodbc), Hive (via PyHive/SQLAlchemy), HBase (happybase), Iceberg (PyIceberg or Spark)
- These functions are lightweight connection testers. Users must install appropriate drivers.
"""
from typing import Tuple, Optional
import sqlalchemy
import traceback

def build_sqlalchemy_string(db_type: str, host: str, port: Optional[int], database: str, username: str, password: str, extra: str="") -> str:
    db_type = db_type.lower()
    if db_type in ("postgres", "postgresql"):
        port = port or 5432
        return f"postgresql://{username}:{password}@{host}:{port}/{database}{extra}"
    if db_type in ("mysql", "mariadb"):
        port = port or 3306
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}{extra}"
    if db_type in ("mssql","sqlserver"):
        port = port or 1433
        # using pyodbc; user needs to have ODBC DSN or driver installed
        return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server{extra}"
    if db_type in ("sqlite",):
        return f"sqlite:///{database}"
    if db_type in ("hive",):
        port = port or 10000
        # requires PyHive and a Thrift hive server
        return f"hive://{username}:{password}@{host}:{port}/{database}{extra}"
    # Iceberg and HBase are special: return placeholders
    if db_type in ("hbase",):
        return "hbase://{host}:{port} (use happybase client)"
    if db_type in ("iceberg",):
        return "iceberg:// (use spark or pyiceberg for connection)"
    raise ValueError("Unsupported db_type: " + db_type)

def test_db_connection(conn_str: str, table: Optional[str]=None, limit: int=1) -> Tuple[bool, str]:
    """
    Attempts to connect using SQLAlchemy engine and run a lightweight query.
    Returns (success, message).
    For HBase/Iceberg connection strings, this function will return a friendly message telling user what to install.
    """
    try:
        if conn_str.startswith("hbase://"):
            return False, ("HBase detected: use 'happybase' or HBase Thrift client. "
                           "This tester does not open HBase connections automatically. Install happybase and use it in your app.")
        if conn_str.startswith("iceberg://") or "iceberg" in conn_str:
            return False, ("Iceberg detected: typically accessed via Spark or PyIceberg. "
                           "This tester only supports SQLAlchemy-accessible endpoints. Use Spark + PyIceberg for Iceberg tables.")
        engine = sqlalchemy.create_engine(conn_str)
        with engine.connect() as conn:
            if table:
                # try a minimal test query
                q = f"SELECT * FROM {table} LIMIT {limit}"
                res = conn.execute(q)
                # fetch one row
                _ = res.fetchone()
            else:
                # run a lightweight version query depending on dialect
                if engine.dialect.name in ("postgresql","mysql","mariadb","mssql","sqlite"):
                    res = conn.execute("SELECT 1")
                    _ = res.fetchone()
                else:
                    res = conn.execute("SELECT 1")
                    _ = res.fetchone()
        return True, "Connection successful and test query executed."
    except Exception as e:
        tb = traceback.format_exc()
        return False, f"Connection failed: {str(e)}\n\nTraceback:\n{tb}"
