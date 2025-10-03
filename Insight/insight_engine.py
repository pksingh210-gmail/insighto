"""
insight_engine.py (extended)
- Rule-based + optional LLM hook
- Adds:
  - Correlation analysis between numeric fields
  - Top driver detection (simple correlation-based)
  - Category concentration (top categories share)
  - Simple seasonality detection (monthly rolling)
  - Enhanced anomaly detection (z-score)
- Optional integration point: ollama_model_client(prompt)
"""
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import math

def summarize_dataframe(df: pd.DataFrame, max_rows:int=5) -> str:
    s = []
    s.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    s.append(f"Numeric columns: {numeric}")
    s.append("Column samples:")
    for c in df.columns:
        s.append(f" - {c}: {str(df[c].dropna().astype(str).head(max_rows).tolist())}")
    return "\n".join(s)

def compute_correlations(df: pd.DataFrame, min_corr:float=0.3) -> List[Tuple[str,str,float]]:
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return []
    corr = numeric.corr().abs()
    pairs = []
    cols = corr.columns.tolist()
    for i,c1 in enumerate(cols):
        for j,c2 in enumerate(cols):
            if j<=i: 
                continue
            val = corr.loc[c1,c2]
            if abs(val) >= min_corr:
                pairs.append((c1,c2, float(val)))
    pairs = sorted(pairs, key=lambda x: -abs(x[2]))
    return pairs

def detect_top_drivers(df: pd.DataFrame, target: str, top_n:int=3) -> List[Tuple[str,float]]:
    """
    Very simple driver detection: compute Pearson correlation between target and other numeric cols and rank.
    """
    if target not in df.columns:
        return []
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric = [c for c in numeric if c!=target]
    res = []
    for c in numeric:
        try:
            x = df[c].astype(float)
            y = df[target].astype(float)
            if x.isnull().all() or y.isnull().all():
                continue
            corr = x.corr(y)
            if pd.isna(corr):
                continue
            res.append((c, float(corr)))
        except Exception:
            continue
    res = sorted(res, key=lambda x: -abs(x[1]))
    return res[:top_n]

def category_concentration(df: pd.DataFrame, category_col: str, value_col: Optional[str]=None) -> Dict[str, Any]:
    if category_col not in df.columns:
        return {"error":"category_col not in df"}
    df2 = df.copy()
    if value_col and value_col in df.columns:
        df2['abs_val'] = df2[value_col].abs()
        agg = df2.groupby(category_col)['abs_val'].sum().sort_values(ascending=False)
    else:
        agg = df2[category_col].value_counts()
    total = agg.sum()
    top = agg.head(3)
    share = (top / total * 100).round(2).to_dict()
    return {
        "total_categories": len(agg), 
        "top_share_percent": share, 
        "top_categories": top.head(5).to_dict()
    }

def seasonality_summary(df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, Any]:
    if date_col not in df.columns or value_col not in df.columns:
        return {"error":"columns missing"}
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col])
    mo = df2.set_index(date_col).resample('M')[value_col].sum()
    if len(mo) < 3:
        return {"error":"not enough data for seasonality"}
    rolling = mo.rolling(window=3).mean()
    trend = "increasing" if rolling.iloc[-1] > rolling.iloc[0] else "decreasing"
    return {
        "monthly_points": mo.to_dict(), 
        "3mo_trend": trend, 
        "last_value": float(mo.iloc[-1])
    }

def detect_anomalies_zscore(df: pd.DataFrame, value_col: str, z_thresh:float=3.0) -> List[Dict]:
    if value_col not in df.columns:
        return []
    vals = df[value_col].astype(float)
    mu = vals.mean()
    sigma = vals.std()
    if sigma==0 or math.isnan(sigma):
        return []
    z = (vals - mu) / sigma
    idx = z[abs(z) >= z_thresh].index.tolist()
    return [
        {"index": int(i), "value": float(vals.loc[i]), "z": float(z.loc[i])} 
        for i in idx
    ]

def generate_insights(
    df: pd.DataFrame, 
    target_value_col: Optional[str]=None, 
    date_col:Optional[str]=None, 
    category_col:Optional[str]=None, 
    use_llm:bool=False, 
    llm_client=None
) -> List[str]:
    """
    Returns list of insights. If use_llm True, will call llm_client(prompt)->str to get polished text (requires ollama_client or similar).
    """
    insights = []
    # basic summary
    insights.append(f"Dataset has {len(df)} rows and {len(df.columns)} columns.")
    # totals
    if target_value_col and target_value_col in df.columns:
        tot = df[target_value_col].sum()
        insights.append(f"Total {target_value_col}: {tot:,.2f}")
    # concentration
    if category_col and category_col in df.columns:
        cc = category_concentration(df, category_col, target_value_col)
        if "top_share_percent" in cc:
            top_share = cc["top_share_percent"]
            for k,v in top_share.items():
                insights.append(f"Top category '{k}' contributes {v}% of total by value.")
    # seasonality
    if date_col and target_value_col and date_col in df.columns and target_value_col in df.columns:
        ss = seasonality_summary(df, date_col, target_value_col)
        if "3mo_trend" in ss:
            insights.append(f"3-month rolling trend appears {ss['3mo_trend']}; last month net: {ss['last_value']:.2f}.")
    # correlations
    corrs = compute_correlations(df, min_corr=0.35)
    if corrs:
        for c1,c2,v in corrs[:5]:
            insights.append(f"Strong correlation ({v:.2f}) between {c1} and {c2}.")
    # drivers
    if target_value_col and target_value_col in df.columns:
        drivers = detect_top_drivers(df, target_value_col, top_n=3)
        for d,score in drivers:
            insights.append(f"Potential driver: {d} (corr={score:.2f}) with target {target_value_col}.")
    # anomalies
    if target_value_col and target_value_col in df.columns:
        anoms = detect_anomalies_zscore(df, target_value_col, z_thresh=3.0)
        if anoms:
            insights.append(f"Detected {len(anoms)} anomalies in {target_value_col} (z-score >= 3).")
    # Final automated recommendations (simple heuristics)
    recs = []
    if category_col and category_col in df.columns:
        recs.append("Investigate top categories for customer retention & targeted promotions.")
    if date_col and target_value_col:
        recs.append("If trend increasing, consider scaling operations or liquidity management for expected growth.")
    if len(corrs)>0:
        recs.append("Explore causality for correlated fields; consider regression modelling for forecasting.")
    if 'anoms' in locals() and anoms:
        recs.append("Review anomalous transactions for fraud or data entry issues.")
    insights.extend(["Recommendation: " + r for r in recs])
    # Optionally call LLM for polishing
    if use_llm and llm_client is not None:
        try:
            prompt = (
                "You are an analytics assistant. Given the following bulleted insights, "
                "produce 5 concise business-ready insights and 3 action recommendations in clear language.\n"
                "Insights bullets:\n" + "\n".join(["- "+s for s in insights])
            )
            polished = llm_client(prompt)
            return [polished]
        except Exception as e:
            insights.append("LLM polishing failed: " + str(e))
    return insights

# NEW: Added missing function so app.py can import it
def basic_kpi_insights(df: pd.DataFrame) -> List[str]:
    """
    Basic KPI-focused insights for dashboards.
    Example: total count, average, min, max for numeric columns.
    """
    insights = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        col_sum = df[col].sum()
        col_avg = df[col].mean()
        col_min = df[col].min()
        col_max = df[col].max()
        insights.append(f"{col}: sum={col_sum:.2f}, avg={col_avg:.2f}, min={col_min:.2f}, max={col_max:.2f}")
    return insights
