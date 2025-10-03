"""
dashboard_generator.py
- Generates Plotly figures and a simple Streamlit layout based on template
"""
from typing import Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


# ---------- Helper ----------
def _empty_figure(title: str = "No data available") -> go.Figure:
    """Return an empty Plotly figure with a centered message."""
    fig = go.Figure()
    fig.add_annotation(
        text=title,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white"
    )
    return fig


# ---------- KPI ----------
def generate_kpi(df: pd.DataFrame, comp: Dict, mapping: Dict) -> Dict:
    val_field = mapping.get(comp.get("value_field")) or mapping.get(f"{comp.get('id')}.value_field")
    agg = comp.get("agg", "sum")
    if val_field is None:
        return {"title": comp.get("title"), "value": "N/A"}
    if agg == "sum":
        v = df[val_field].sum()
    elif agg == "mean":
        v = df[val_field].mean()
    elif agg == "mean_abs":
        v = df[val_field].abs().mean()
    else:
        v = df[val_field].sum()
    return {"title": comp.get("title"), "value": round(float(v), 2)}


# ---------- Charts ----------
def generate_line(df: pd.DataFrame, comp: Dict, mapping: Dict):
    date_field = mapping.get(comp.get("date_field")) or mapping.get(f"{comp.get('id')}.date_field")
    val_field = mapping.get(comp.get("value_field")) or mapping.get(f"{comp.get('id')}.value_field")
    if date_field is None or val_field is None:
        return _empty_figure(comp.get("title", "Line Chart - No data"))
    df2 = df.copy()
    df2[date_field] = pd.to_datetime(df2[date_field])
    freq = comp.get("time_granularity", "M")
    df2 = df2.set_index(date_field).resample(freq)[val_field].sum().reset_index()
    fig = px.line(df2, x=date_field, y=val_field, title=comp.get("title"))
    return fig


def generate_bar(df: pd.DataFrame, comp: Dict, mapping: Dict):
    grp = mapping.get(comp.get("group_field")) or mapping.get(f"{comp.get('id')}.group_field")
    val = mapping.get(comp.get("value_field")) or mapping.get(f"{comp.get('id')}.value_field")
    if grp is None or val is None:
        return _empty_figure(comp.get("title", "Bar Chart - No data"))
    df2 = df.copy()
    df2["abs_val"] = df2[val].abs()
    top_n = comp.get("top_n", 10)
    df2 = df2.groupby(grp)["abs_val"].sum().reset_index().sort_values("abs_val", ascending=False).head(top_n)
    fig = px.bar(df2, x=grp, y="abs_val", title=comp.get("title"))
    return fig


def generate_pie(df: pd.DataFrame, comp: Dict, mapping: Dict):
    grp = mapping.get(comp.get("group_field")) or mapping.get(f"{comp.get('id')}.group_field")
    val = mapping.get(comp.get("value_field")) or mapping.get(f"{comp.get('id')}.value_field")
    if grp is None or val is None:
        return _empty_figure(comp.get("title", "Pie Chart - No data"))
    df2 = df.copy()
    df2["abs_val"] = df2[val].abs()
    df2 = df2.groupby(grp)["abs_val"].sum().reset_index()
    fig = px.pie(df2, names=grp, values="abs_val", title=comp.get("title"))
    return fig

def generate_scatter(df, comp, mapping):
    x_field = mapping.get(comp.get("x_field", ""), comp.get("x_field"))
    y_field = mapping.get(comp.get("y_field", ""), comp.get("y_field"))
    color_field = mapping.get(comp.get("color_field", ""), comp.get("color_field"))
    size_field = mapping.get(comp.get("size_field", ""), comp.get("size_field"))

    fig = px.scatter(
        df,
        x=x_field,
        y=y_field,
        color=color_field if color_field else None,
        size=size_field if size_field else None,
        title=comp.get("title", "Scatter Plot"),
    )
    return fig


def generate_histogram(df, comp, mapping):
    value_field = mapping.get(comp.get("value_field", ""), comp.get("value_field"))
    color_field = mapping.get(comp.get("color_field", ""), comp.get("color_field"))

    fig = px.histogram(
        df,
        x=value_field,
        color=color_field if color_field else None,
        nbins=comp.get("bins", 20),
        title=comp.get("title", "Histogram"),
    )
    return fig


def generate_heatmap(df, comp, mapping):
    x_field = mapping.get(comp.get("x_field", ""), comp.get("x_field"))
    y_field = mapping.get(comp.get("y_field", ""), comp.get("y_field"))
    value_field = mapping.get(comp.get("value_field", ""), comp.get("value_field"))

    pivot = df.pivot_table(
        index=y_field,
        columns=x_field,
        values=value_field,
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    fig = px.imshow(
        pivot.set_index(y_field).values,
        labels=dict(x=x_field, y=y_field, color=value_field),
        x=pivot.columns[1:],  # skip y_field col
        y=pivot[y_field],
        title=comp.get("title", "Heatmap"),
        aspect="auto"
    )
    return fig

# ---------- Extensible Chart Loader ----------
def generate_chart(df: pd.DataFrame, comp: Dict, mapping: Dict):
    """
    Generic chart generator so you can support more than 6 chart types without editing the dashboard code.
    'type' in comp dict decides which generator is used.
    """
    chart_type = comp.get("type", "").lower()

    chart_map = {
        "line": generate_line,
        "bar": generate_bar,
        "pie": generate_pie,
        "scatter": generate_scatter,
        "histogram": generate_histgram,
        "heatmap": generate_heatmap
    }

    func = chart_map.get(chart_type)
    if func:
        return func(df, comp, mapping)

    # Fallback if unknown chart type
    return _empty_figure(f"Unsupported chart type: {chart_type}")
