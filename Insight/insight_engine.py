"""
Enhanced insight_engine.py (Dashboard-Aware Edition)
-----------------------------------------------------
Features:
- Rule-based + optional LLM refinement
- Supports:
  - KPI-style insights for dashboards (e.g., Insight 1–9)
  - Correlation, anomalies, trends, category shares
  - Human-readable, descriptive, dynamic phrasing
  - Optional LLM polishing via ollama_model_client(prompt)
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import math


# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------

def compute_correlations(df: pd.DataFrame, min_corr: float = 0.3) -> List[Tuple[str, str, float]]:
    """Finds strong numeric correlations."""
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return []
    corr = numeric.corr().abs()
    pairs = []
    for i, c1 in enumerate(corr.columns):
        for j, c2 in enumerate(corr.columns):
            if j <= i:
                continue
            val = corr.loc[c1, c2]
            if abs(val) >= min_corr:
                pairs.append((c1, c2, float(val)))
    return sorted(pairs, key=lambda x: -abs(x[2]))


def detect_anomalies_zscore(df: pd.DataFrame, value_col: str, z_thresh: float = 3.0) -> List[Dict]:
    """Detects anomalies using z-score."""
    if value_col not in df.columns:
        return []
    vals = df[value_col].astype(float)
    mu, sigma = vals.mean(), vals.std()
    if sigma == 0 or math.isnan(sigma):
        return []
    z = (vals - mu) / sigma
    outliers = z[abs(z) >= z_thresh]
    return [{"index": int(i), "value": float(vals.loc[i]), "z": float(z.loc[i])} for i in outliers.index]


# ---------------------------------------------------
# Main Insight Generator
# ---------------------------------------------------

def basic_kpi_insights(df: pd.DataFrame) -> List[str]:
    insights = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    # Common ID-like or non-business columns to skip
    exclude_keywords = ["id", "code", "zip", "key", "number"]
    filtered_cols = [
        col for col in numeric_cols
        if not any(ex_kw.lower() in col.lower() for ex_kw in exclude_keywords)
    ]

    for col in filtered_cols:
        total = df[col].sum()
        avg = df[col].mean()
        minv = df[col].min()
        maxv = df[col].max()

        # Heuristic: Check if variation is meaningful
        spread_ratio = (maxv - minv) / (avg + 1e-6)
        is_significant = spread_ratio > 0.1  # at least 10% variation

        if is_significant and avg > 1000:
            msg = (
                f"**{col.replace('_', ' ').title()}** averages around {avg:,.2f}, "
                f"totaling {total:,.0f}. Values range between {minv:,.2f} and {maxv:,.2f}, "
                f"showing significant spread."
            )
        elif is_significant:
            msg = (
                f"**{col.replace('_', ' ').title()}** shows moderate variation, "
                f"averaging {avg:,.2f} (min {minv:,.2f}, max {maxv:,.2f})."
            )
        else:
            msg = (
                f"**{col.replace('_', ' ').title()}** remains relatively stable, "
                f"averaging {avg:,.2f} with limited variability."
            )

        insights.append(msg)

    # Handle case: if all columns excluded, provide note
    if not insights:
        insights.append(
            "No business-relevant numeric columns found for KPI analysis. "
            "ID-like or static columns were excluded."
        )

    return insights


def generate_dashboard_insights(
    df: pd.DataFrame,
    dashboard_name: str = "Financial Dashboard",
    include_correlations: bool = True,
    use_llm: bool = False,
    llm_client=None
) -> List[str]:
    """
    Produces descriptive, human-readable dashboard insights
    combining KPI summaries + relationships + patterns.
    """
    insights = []

    # --- KPI Summaries ---
    insights.extend(basic_kpi_insights(df))

    # --- Correlations ---
    if include_correlations:
        corrs = compute_correlations(df)
        if corrs:
            top_corrs = corrs[:3]
            for c1, c2, v in top_corrs:
                insights.append(
                    f"A notable correlation (**r = {v:.2f}**) exists between **{c1}** and **{c2}**, "
                    "indicating they move closely together — potentially useful for predictive modeling."
                )

    # --- Anomalies ---
    for col in df.select_dtypes(include=[np.number]).columns:
        anoms = detect_anomalies_zscore(df, col)
        if len(anoms) > 0:
            insights.append(
                f"**{col.replace('_', ' ').title()}** shows {len(anoms)} unusual data points (anomalies), "
                "which may represent exceptional cases, outliers, or potential data errors."
            )

    # --- Summary Note ---
    insights.append(
        f"📊 These insights summarize {dashboard_name}, combining quantitative patterns and potential risk signals."
    )

    # --- Optional LLM Enhancement ---
    if use_llm and llm_client:
        try:
            prompt = (
                "You are a data storytelling expert. Rewrite these raw insights into an executive-friendly narrative. "
                "Keep it data-driven, concise, and descriptive, reflecting relationships and dashboard findings:\n\n"
                + "\n".join(insights)
            )
            summary = llm_client(prompt)
            return [summary]
        except Exception as e:
            insights.append(f"⚠️ LLM enhancement failed: {e}")

    return insights

