"""Plotly Chart Generators for the F1 Strategy Lab Dashboard."""

from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# F1 dark mode color palette
F1_COLORS = {
    "background": "#15151e",
    "surface": "#1e1e2d",
    "primary": "#e10600",  # F1 Red
    "accent": "#00d2be",  # Teal / Cyan
    "soft": "#ff1801",  # Red
    "medium": "#ffd200",  # Yellow
    "hard": "#ffffff",  # White
    "inter": "#39b54a",  # Green
    "wet": "#00a0dd",  # Blue
    "vsc": "rgba(255, 210, 0, 0.2)",
    "sc": "rgba(255, 128, 0, 0.25)",
}


def build_gap_chart(df: pd.DataFrame, focus_drivers: Optional[List[str]] = None) -> go.Figure:
    """Builds interactive Plotly race gap chart (gap to leader vs lap)."""
    fig = go.Figure()

    if df.empty:
        return fig

    drivers = focus_drivers or list(df["driver"].unique()[:6])
    filtered = df[df["driver"].isin(drivers)]

    for driver in drivers:
        d_df = filtered[filtered["driver"] == driver]
        fig.add_trace(
            go.Scatter(
                x=d_df["lap"],
                y=d_df["gap_to_leader"],
                mode="lines+markers",
                name=driver,
                line=dict(width=2.5),
                marker=dict(size=5),
                hovertemplate="<b>%{fullData.name}</b><br>Lap: %{x}<br>Gap: +%{y:.3f}s<extra></extra>",
            )
        )

    # Add SC / VSC vertical bands
    sc_laps = df[df["safety_car_status"] > 0][["lap", "safety_car_status", "safety_car_label"]].drop_duplicates()
    for _, row in sc_laps.iterrows():
        fill_col = F1_COLORS["vsc"] if row["safety_car_status"] == 1 else F1_COLORS["sc"]
        fig.add_vrect(
            x0=row["lap"] - 0.5,
            x1=row["lap"] + 0.5,
            fillcolor=fill_col,
            opacity=0.6,
            layer="below",
            line_width=0,
            annotation_text=row["safety_car_label"] if row["lap"] == sc_laps["lap"].min() else "",
            annotation_position="top left",
        )

    fig.update_layout(
        title="<b>Race Interval Gap to Leader</b>",
        xaxis_title="Lap",
        yaxis_title="Gap to P1 (seconds)",
        yaxis=dict(autorange="reversed", gridcolor="#2c2c3e"),
        xaxis=dict(gridcolor="#2c2c3e"),
        plot_bgcolor=F1_COLORS["surface"],
        paper_bgcolor=F1_COLORS["background"],
        font=dict(color="#ffffff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def build_position_chart(df: pd.DataFrame, focus_drivers: Optional[List[str]] = None) -> go.Figure:
    """Builds interactive lap chart showing driver positions over race distance."""
    fig = go.Figure()

    if df.empty:
        return fig

    drivers = focus_drivers or list(df["driver"].unique()[:8])
    filtered = df[df["driver"].isin(drivers)]

    for driver in drivers:
        d_df = filtered[filtered["driver"] == driver]
        fig.add_trace(
            go.Scatter(
                x=d_df["lap"],
                y=d_df["rank"],
                mode="lines+markers",
                name=driver,
                line=dict(width=2.5),
                marker=dict(size=6),
                hovertemplate="<b>%{fullData.name}</b><br>Lap: %{x}<br>Pos: P%{y}<extra></extra>",
            )
        )

    fig.update_layout(
        title="<b>Position Lap Chart (Overtakes & Undercuts)</b>",
        xaxis_title="Lap",
        yaxis_title="Position (Rank)",
        yaxis=dict(autorange="reversed", dtick=1, gridcolor="#2c2c3e"),
        xaxis=dict(gridcolor="#2c2c3e"),
        plot_bgcolor=F1_COLORS["surface"],
        paper_bgcolor=F1_COLORS["background"],
        font=dict(color="#ffffff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def build_tire_stint_chart(df: pd.DataFrame, focus_drivers: Optional[List[str]] = None) -> go.Figure:
    """Builds tire wear sawtooth degradation and pit stop chart."""
    fig = go.Figure()

    if df.empty:
        return fig

    drivers = focus_drivers or list(df["driver"].unique()[:6])
    filtered = df[df["driver"].isin(drivers)]

    for driver in drivers:
        d_df = filtered[filtered["driver"] == driver]
        fig.add_trace(
            go.Scatter(
                x=d_df["lap"],
                y=d_df["tire_age"],
                mode="lines+markers",
                name=driver,
                line=dict(width=2, dash="dot"),
                marker=dict(size=4),
                hovertemplate="<b>%{fullData.name}</b><br>Lap: %{x}<br>Tire Age: %{y} laps<extra></extra>",
            )
        )

    fig.update_layout(
        title="<b>Tire Age & Stint Lifecycles (Sawtooth)</b>",
        xaxis_title="Lap",
        yaxis_title="Effective Tire Age (Laps Equivalent)",
        xaxis=dict(gridcolor="#2c2c3e"),
        yaxis=dict(gridcolor="#2c2c3e"),
        plot_bgcolor=F1_COLORS["surface"],
        paper_bgcolor=F1_COLORS["background"],
        font=dict(color="#ffffff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def build_stint_timeline_bars(df: pd.DataFrame, focus_drivers: Optional[List[str]] = None) -> go.Figure:
    """Builds compound stint timeline bar visualization for drivers."""
    fig = go.Figure()
    if df.empty:
        return fig

    drivers = focus_drivers or list(df["driver"].unique()[:10])

    compound_colors = {
        "Soft": F1_COLORS["soft"],
        "Medium": F1_COLORS["medium"],
        "Hard": F1_COLORS["hard"],
    }

    y_pos = 0
    for driver in reversed(drivers):
        d_df = df[df["driver"] == driver].sort_values("lap")
        if d_df.empty:
            continue

        # Segment consecutive stints by tire age drops (pit stops)
        stint_start = d_df["lap"].iloc[0]
        curr_compound = d_df["compound"].iloc[0]
        prev_age = d_df["tire_age"].iloc[0]

        for i in range(1, len(d_df)):
            row = d_df.iloc[i]
            if row["tire_age"] < prev_age:
                # Pit stop occurred
                fig.add_trace(
                    go.Bar(
                        y=[driver],
                        x=[row["lap"] - stint_start],
                        base=[stint_start],
                        orientation="h",
                        name=curr_compound,
                        marker=dict(
                            color=compound_colors.get(curr_compound, "#888888"),
                            line=dict(color="#111", width=1),
                        ),
                        showlegend=False,
                        hoverinfo="text",
                        hovertext=f"{driver}: {curr_compound} (Laps {stint_start}-{row['lap']})",
                    )
                )
                stint_start = row["lap"]
                curr_compound = row["compound"]
            prev_age = row["tire_age"]

        # Final stint
        final_lap = d_df["lap"].iloc[-1]
        fig.add_trace(
            go.Bar(
                y=[driver],
                x=[final_lap - stint_start + 1],
                base=[stint_start],
                orientation="h",
                name=curr_compound,
                marker=dict(
                    color=compound_colors.get(curr_compound, "#888888"),
                    line=dict(color="#111", width=1),
                ),
                showlegend=False,
                hoverinfo="text",
                hovertext=f"{driver}: {curr_compound} (Laps {stint_start}-{final_lap})",
            )
        )
        y_pos += 1

    fig.update_layout(
        title="<b>Tire Compound Strategy Stint Timeline</b>",
        xaxis_title="Lap",
        yaxis_title="Driver",
        barmode="stack",
        plot_bgcolor=F1_COLORS["surface"],
        paper_bgcolor=F1_COLORS["background"],
        font=dict(color="#ffffff"),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig
