"""Streamlit UI components for rendering timing tables and F1 metrics."""

from typing import Any, Dict, List
import pandas as pd
import streamlit as st


def render_f1_banner(lap: int, total_laps: int, sc_status: int, leader_name: str):
    """Renders F1 dark-themed top status banner."""
    if sc_status == 1:
        bg_color = "#997300"
        border_color = "#ffd200"
        status_text = "🟡 VIRTUAL SAFETY CAR (VSC) DEPLOYED — DELTA SPEED REGULATED"
    elif sc_status == 2:
        bg_color = "#994d00"
        border_color = "#ff8000"
        status_text = "🟠 FULL SAFETY CAR (SC) DEPLOYED — FIELD BUNCHED"
    else:
        bg_color = "#1a3320"
        border_color = "#39b54a"
        status_text = "🟢 GREEN FLAG — RACING CONDITIONS"

    st.markdown(
        f"""
        <div style="background-color: {bg_color}; border-left: 6px solid {border_color}; padding: 12px 18px; border-radius: 6px; margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">{status_text}</span>
                <span style="font-size: 1.1rem; font-weight: 800; color: #ffffff; letter-spacing: 1px;">LAP {lap} / {total_laps}</span>
            </div>
            <div style="font-size: 0.9rem; color: #e0e0e0; margin-top: 4px;">
                Race Leader: <b style="color: #ffffff;">{leader_name}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_interactive_timing_tower(positions: List[Dict[str, Any]]):
    """Renders high-fidelity dark-themed timing tower table."""
    if not positions:
        st.info("No timing data available.")
        return

    table_data = []
    for p in positions:
        comp = p["compound"]
        comp_badge = f"{comp} ({int(round(p['tire_age']))}L)"

        gap_str = "LEADER" if p["rank"] == 1 else f"+{p['gap_to_leader']:.3f}s"
        int_str = "—" if p["rank"] == 1 else f"+{p['interval']:.3f}s"

        table_data.append(
            {
                "Pos": p["rank"],
                "Driver": p["driver"],
                "Gap to P1": gap_str,
                "Interval": int_str,
                "Tire (Age)": comp_badge,
                "Pits": p["pit_stops"],
                "DRS": p.get("drs_count", 0),
                "Dirty Air": p.get("dirty_air_count", 0),
                "Total Time": f"{p['total_time']:.2f}s",
            }
        )

    df_display = pd.DataFrame(table_data)
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pos": st.column_config.NumberColumn("POS", width="small"),
            "Driver": st.column_config.TextColumn("DRIVER", width="medium"),
            "Gap to P1": st.column_config.TextColumn("GAP TO P1", width="small"),
            "Interval": st.column_config.TextColumn("INTERVAL", width="small"),
            "Tire (Age)": st.column_config.TextColumn("TIRE", width="small"),
            "Pits": st.column_config.NumberColumn("STOPS", width="small"),
            "DRS": st.column_config.NumberColumn("DRS", width="small"),
            "Dirty Air": st.column_config.NumberColumn("DIRTY", width="small"),
            "Total Time": st.column_config.TextColumn("TIME", width="small"),
        },
    )
