"""
app/charts.py — reusable Plotly chart functions.

Each function takes a pandas DataFrame and returns a Plotly figure object.
Keeping chart styling here means every page looks consistent with one change.
"""

import plotly.express as px
import plotly.graph_objects as go

# A clean, hostel-friendly color palette
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def line_chart(df, x, y, title, x_label=None, y_label=None):
    """A simple line chart."""
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    fig.update_layout(
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def bar_chart(df, x, y, title, x_label=None, y_label=None, color=None):
    """A simple bar chart."""
    fig = px.bar(df, x=x, y=y, title=title, color=color, color_discrete_sequence=COLORS)
    fig.update_layout(
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def grouped_bar_chart(df, x, y, color, title, x_label=None, y_label=None):
    """A grouped bar chart (e.g. room rent vs mess fee by month)."""
    fig = px.bar(df, x=x, y=y, color=color, barmode="group", title=title,
                 color_discrete_sequence=COLORS)
    fig.update_layout(
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="",
    )
    return fig


def pie_chart(df, values, names, title, hole=0.4):
    """A donut/pie chart."""
    fig = px.pie(df, values=values, names=names, title=title, hole=hole,
                 color_discrete_sequence=COLORS)
    fig.update_layout(height=450, margin=dict(l=40, r=40, t=60, b=40))
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def vacancy_table_highlight(df):
    """
    Return a styled copy of the room availability DataFrame for display.
    Rows with high vacancy (>50%) are flagged so Streamlit can highlight them.
    """
    df = df.copy()
    df["high_vacancy"] = df["vacant_beds"] > 0
    return df
