"""
schema_mapper.py
- Generic schema mapping for any dataset and any domain.
"""
from typing import Dict
import pandas as pd
import numpy as np
import difflib


def infer_field_roles(df: pd.DataFrame) -> Dict[str, str]:
    """
    Assigns a generic role to each column based on data type and content.
    """
    roles = {}
    for c in df.columns:
        series = df[c]
        if pd.api.types.is_datetime64_any_dtype(series):
            roles[c] = "datetime"
        elif pd.api.types.is_numeric_dtype(series):
            roles[c] = "numeric"
        elif series.nunique(dropna=True) < len(series) * 0.5:
            roles[c] = "categorical"
        else:
            roles[c] = "text"
    return roles


def _find_best_match(desired: str, columns: list) -> str:
    """
    Finds the closest matching column name to the desired field using difflib.
    """
    matches = difflib.get_close_matches(desired.lower(), [c.lower() for c in columns], n=1, cutoff=0.6)
    if matches:
        for c in columns:
            if c.lower() == matches[0]:
                return c
    return None


def map_template_fields(template: Dict, df_roles: Dict[str, str]) -> Dict[str, str]:
    """
    Maps template-required fields to actual dataset columns using:
    1. Exact match (case-insensitive)
    2. Closest name match
    3. Role-based fallback
    """
    mapping = {}
    cols = list(df_roles.keys())

    for comp in template.get("layout", []):
        for fld, desired in comp.items():
            if not isinstance(desired, str):
                continue

            # 1. Exact match
            exact_match = next((c for c in cols if c.lower() == desired.lower()), None)
            if exact_match:
                mapping[desired] = exact_match
                continue

            # 2. Closest match by name
            close_match = _find_best_match(desired, cols)
            if close_match:
                mapping[f"{comp.get('id', comp.get('title', fld))}.{fld}"] = close_match
                continue

            # 3. Role-based fallback
            role_match = None
            if "date" in fld.lower() or "time" in fld.lower():
                role_match = "datetime"
            elif "value" in fld.lower() or "amount" in fld.lower() or "price" in fld.lower():
                role_match = "numeric"
            elif "group" in fld.lower() or "category" in fld.lower():
                role_match = "categorical"
            elif "id" in fld.lower():
                role_match = "id"

            if role_match:
                for c in cols:
                    if df_roles[c] == role_match:
                        mapping[f"{comp.get('id', comp.get('title', fld))}.{fld}"] = c
                        break

            # 4. If still nothing, just take the first column
            if f"{comp.get('id', comp.get('title', fld))}.{fld}" not in mapping and cols:
                mapping[f"{comp.get('id', comp.get('title', fld))}.{fld}"] = cols[0]

    return mapping
