import math

import pandas as pd
import plotly.graph_objects as go

PURPLE = "#5B35D5"
PURPLE_2 = "#8367E8"
DARK = "#211A4A"
MUTED = "#7A7D92"
GRID = "#ECECF3"
GREEN = "#12A66A"
AMBER = "#E49A27"
RED = "#D84B64"


def _base_layout(height=170):
    return dict(
        height=height,
        margin=dict(l=4, r=4, t=10, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif", color=DARK, size=9),
        hoverlabel=dict(bgcolor="white", font_color=DARK, bordercolor=GRID),
    )


def completion_donut(completion, completed, target):
    pct = 0.0 if completion is None or pd.isna(completion) else max(0.0, min(float(completion), 100.0))
    fig = go.Figure()
    fig.add_trace(go.Pie(
        values=[pct, 100 - pct],
        hole=0.76,
        sort=False,
        direction="clockwise",
        marker=dict(colors=[PURPLE, "#EEEAFB"], line=dict(width=0)),
        textinfo="none",
        hovertemplate="Completion %{value:.0f}%<extra></extra>",
        showlegend=False,
    ))
    center = "Not Set" if target is None or pd.isna(target) else f"{pct:.0f}%"
    subtitle = f"{completed} completed" if target is None or pd.isna(target) else f"{completed} of {int(target)} papers"
    fig.add_annotation(x=0.5, y=0.56, text=f"<b>{center}</b>", showarrow=False, font=dict(size=21, color=DARK))
    fig.add_annotation(x=0.5, y=0.38, text=subtitle, showarrow=False, font=dict(size=8, color=MUTED))
    fig.update_layout(**_base_layout(145))
    return fig


def performance_trend(attempts, status):
    df = attempts.copy()
    df["attempt_date"] = pd.to_datetime(df["attempt_date"], errors="coerce")
    df = df.dropna(subset=["attempt_date", "percentage"]).sort_values("attempt_date").tail(8)
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df["attempt_date"],
            y=df["percentage"],
            mode="lines+markers",
            line=dict(color=PURPLE, width=2.2, shape="spline"),
            marker=dict(size=5.5, color="white", line=dict(color=PURPLE, width=1.6)),
            fill="tozeroy",
            fillcolor="rgba(91,53,213,0.055)",
            customdata=df.get("paper_code"),
            hovertemplate="%{x|%d %b %Y}<br><b>%{y:.1f}%</b><br>%{customdata}<extra></extra>",
            name="Performance",
        ))
        last = df.iloc[-1]
        fig.add_annotation(
            x=last["attempt_date"], y=last["percentage"], text=f"{float(last['percentage']):.0f}%",
            showarrow=False, xshift=8, yshift=10,
            font=dict(size=8, color=DARK),
        )
    fig.update_layout(
        **_base_layout(165),
        xaxis=dict(title="", showgrid=False, zeroline=False, tickfont=dict(size=7, color=MUTED), nticks=5),
        yaxis=dict(title="", range=[0, 100], gridcolor=GRID, zeroline=False, ticksuffix="%", tickfont=dict(size=7, color=MUTED), dtick=25),
        showlegend=False,
    )
    return fig


def priority_bar(priority_df):
    df = priority_df.copy().head(3)
    if df.empty:
        return None
    df["label"] = df.apply(lambda r: f"{r['subtopic_name']}", axis=1)
    df["average_percentage"] = pd.to_numeric(df["average_percentage"], errors="coerce").fillna(0)
    colors = [RED if p == "High" else AMBER if p == "Medium" else PURPLE_2 for p in df["priority"]]
    fig = go.Figure(go.Bar(
        x=df["average_percentage"],
        y=df["label"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df["average_percentage"].map(lambda v: f"{v:.0f}%"),
        textposition="outside",
        cliponaxis=False,
        customdata=df[["topic_name", "priority", "observation_count"]].to_numpy(),
        hovertemplate="<b>%{customdata[0]}</b><br>%{y}<br>Performance: %{x:.1f}%<br>Priority: %{customdata[1]}<br>Observations: %{customdata[2]}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(165),
        xaxis=dict(range=[0, 105], ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(size=7, color=MUTED)),
        yaxis=dict(autorange="reversed", title="", tickfont=dict(size=8, color=DARK)),
        showlegend=False,
        bargap=0.45,
    )
    return fig


def performance_gauge(value, label="Average Performance"):
    if value is None or pd.isna(value):
        return None
    value = float(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 22, "color": DARK}},
        title={"text": label, "font": {"size": 9, "color": MUTED}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)", "tickfont": {"size": 7, "color": MUTED}},
            "bar": {"color": PURPLE, "thickness": 0.38},
            "bgcolor": "#EEEAFB",
            "borderwidth": 0,
        },
    ))
    fig.update_layout(**_base_layout(145))
    return fig


def prediction_band(predicted_percentage, recent_percentage=None):
    if predicted_percentage is None or pd.isna(predicted_percentage):
        return None
    pred = float(predicted_percentage)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[pred], y=["Predicted"], orientation="h", marker=dict(color=PURPLE),
        text=[f"{pred:.1f}%"], textposition="inside", insidetextanchor="end",
        hovertemplate="Predicted Performance: %{x:.1f}%<extra></extra>",
        width=0.35,
    ))
    if recent_percentage is not None and not pd.isna(recent_percentage):
        recent = float(recent_percentage)
        fig.add_shape(type="line", x0=recent, x1=recent, y0=-0.35, y1=0.35, line=dict(color=DARK, width=2))
        fig.add_annotation(x=recent, y=0.43, text=f"Recent {recent:.0f}%", showarrow=False, font=dict(size=7, color=DARK))
    fig.update_layout(
        **_base_layout(100),
        xaxis=dict(range=[0,100], ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(size=7, color=MUTED)),
        yaxis=dict(showticklabels=False, showgrid=False),
        showlegend=False,
    )
    return fig
