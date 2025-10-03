"""
data_loader.py
- functions to read CSV or connect to a DB (DB connection placeholder)
- returns pandas DataFrame and simple schema
"""
import pandas as pd
from typing import Tuple, Dict
import sqlalchemy

def read_csv(path: str, parse_dates=None) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=parse_dates)
    return df

def read_sql_table(conn_string: str, table_name: str, limit:int=None) -> pd.DataFrame:
    """
    Placeholder for DB read. Uses SQLAlchemy connection string.
    """
    engine = sqlalchemy.create_engine(conn_string)
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    df = pd.read_sql(query, engine)
    return df

def describe_schema(df: pd.DataFrame) -> Dict:
    schema = {}
    for c in df.columns:
        dtype = str(df[c].dtype)
        non_null = int(df[c].notnull().sum())
        sample = df[c].dropna().astype(str).head(3).tolist()
        schema[c] = {"dtype":dtype, "non_null":non_null, "sample":sample}
    return schema
