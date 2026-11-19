"""F1 Race Strategy Lab — Interactive Visual Interface.

Connects to the native C++ simulation kernel, PPO v2 agent, DP baselines,
Safety Car simulation, and centralized experiment tracker.
"""

from pathlib import Path
import time
import numpy as np
import pandas as pd
from race._bootstrap import ensure_project_paths
import streamlit as st

ensure_project_paths()
import race_engine
from race.benchmarks.benchmark_suite import run_clean_air_benchmarks
from race.tracking.experiment_tracker import ExperimentTracker

# Local dashboard adapters & components
from dashboard.adapter import RaceDataAdapter
from dashboard.charts import (
    build_gap_chart,
    build_position_chart,
    build_stint_timeline_bars,
    build_tire_stint_chart,
)
from dashboard.components.tower_ui import render_f1_banner, render_interactive_timing_tower

# Page Configuration
st.set_page_config(
    page_title="F1 Race Strategy Lab",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark Theme CSS
st.markdown(
    """
    <style>
    .main {
        background-color: #15151e;
        color: #ffffff;
    }
    .stMetric {
        background-color: #1e1e2d;
        padding: 10px;
        border-radius: 6px;
        border: 1px solid #2d2d3f;
    }
    div[data-testid="stSidebar"] {
        background-color: #111118;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_simulation(
    laps: int,
    num_cars: int,
    seed: int,
    initial_fuel: float,
    vsc_lap: int,
    sc_lap: int,
    use_ppo: bool,
):
    """Executes race simulation against C++ simulator engine."""
    tracker = ExperimentTracker(
        "dashboard_simulation",
        config={
            "laps": laps,
            "num_cars": num_cars,
            "seed": seed,
            "initial_fuel": initial_fuel,
            "vsc_lap": vsc_lap,
            "sc_lap": sc_lap,
            "use_ppo": use_ppo,
        },
    )

    sim = race_engine.RaceSimulator()
    sim.set_seed(seed)

    # Safety car schedule
    sc_sched = {}
    if vsc_lap > 0:
        sc_sched[vsc_lap] = 1
    if sc_lap > 0:
        sc_sched[sc_lap] = 2

    if sc_sched:
        sim.set_safety_car_schedule(sc_sched)

    # Load PPO v2 model if requested
    model = None
    if use_ppo:
        try:
            from stable_baselines3 import PPO

            model_path = Path(__file__).resolve().parents[1] / "models" / "checkpoints" / "f1_rl_strategist_v2.zip"
            if model_path.exists():
                model = PPO.load(str(model_path).replace(".zip", ""), device="cpu")
        except Exception:
            model = None

    car_names = [f"Driver_{i+1}" for i in range(num_cars)]
    car_compounds = {name: "Soft" for name in car_names}
    pit_counts = {name: 0 for name in car_names}
    ai_decisions_log = []

    for name in car_names:
        sim.add_car(name, lambda s, g: race_engine.Action(False, "Soft"), initial_fuel)

    tire_idx_map = {0: "Soft", 1: "Medium", 2: "Hard"}

    for lap in range(laps):
        lap_actions = {}
        for name in car_names:
            if not sim.race_history:
                obs_v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            else:
                hist = sim.race_history[-1]
                cur_lap = float(hist.lap)
                tire_age = float(hist.car_tire_ages[name])
                gap = float(hist.car_times[name] - hist.car_times[hist.leader_name])
                obs_v1 = np.array([cur_lap, tire_age, gap], dtype=np.float32)

            curr_comp = car_compounds[name]
            curr_age = obs_v1[1]

            if model is not None and name == car_names[0]:
                # If model expects 8 dimensions, construct v2 observation
                if model.observation_space.shape[0] == 8:
                    lap_norm = min(float(lap + 1) / float(laps), 1.0)
                    age_norm = min(curr_age / 50.0, 1.0)
                    comp_val = float({"Soft": 0, "Medium": 1, "Hard": 2}.get(curr_comp, 0))
                    fuel_norm = max((initial_fuel - (lap + 1) * 2.2) / initial_fuel, 0.0)
                    gap_leader_norm = float(np.clip(obs_v1[2] / 60.0, -1.0, 1.0))
                    obs_v2 = np.array(
                        [lap_norm, age_norm, comp_val, fuel_norm, gap_leader_norm, 0.0, 0.0, 1.0 - lap_norm],
                        dtype=np.float32,
                    )
                    action, _ = model.predict(obs_v2, deterministic=True)
                    pitted = bool(action[0])
                    chosen_tire = tire_idx_map[int(action[1])]
                    ai_decisions_log.append(
                        {
                            "lap": lap + 1,
                            "driver": name,
                            "obs": obs_v2.tolist(),
                            "action_pit": pitted,
                            "chosen_tire": chosen_tire,
                            "tire_age_pre": curr_age,
                        }
                    )
                else:
                    action, _ = model.predict(obs_v1, deterministic=True)
                    pitted = bool(action[0])
                    chosen_tire = tire_idx_map[int(action[1])]
            else:
                # Heuristic field strategies
                threshold = 16.0 if curr_comp == "Soft" else 24.0
                pitted = curr_age > threshold
                chosen_tire = "Medium" if curr_comp == "Soft" else "Hard"

            if pitted:
                car_compounds[name] = chosen_tire
                pit_counts[name] += 1

            lap_actions[name] = race_engine.Action(pitted, chosen_tire)

        sim.simulate_one_lap(lap_actions)

    # Convert to snapshots and DataFrame
    snapshots = RaceDataAdapter.history_to_snapshots(sim.race_history, car_compounds, pit_counts)
    df = RaceDataAdapter.snapshots_to_dataframe(snapshots)

    # Log to tracker
    tracker.log_metric("total_laps", laps)
    tracker.log_metric("total_cars", num_cars)
    tracker.log_metric("winning_driver", sim.race_history[-1].leader_name)
    tracker.log_metric("winning_time", sim.race_history[-1].car_times[sim.race_history[-1].leader_name])
    tracker.finish(status="Passed", summary_notes=f"Dashboard simulation run completed with {num_cars} cars.")

    return snapshots, df, ai_decisions_log


# ---------------- Sidebar Navigation ----------------
st.sidebar.title("🏎️ F1 Strategy Lab")
page = st.sidebar.radio(
    "Navigation",
    [
        "🏁 Race Configuration & Run",
        "⏮️ Race Replay (Lap-by-Lap)",
        "📊 Strategy & Telemetry Analysis",
        "🧠 AI Decision Inspector",
        "📁 Experiment Explorer",
        "📈 DP & Strategy Benchmarks",
    ],
)


# ---------------- PAGE 1: Race Configuration & Run ----------------
if page == "🏁 Race Configuration & Run":
    st.title("🏁 Formula 1 Race Simulation Studio")
    st.markdown(
        "Configure and execute race simulations powered by the C++17 physics kernel, DRS aerodynamic models, and PPO strategy agents."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🏎️ Grid & Distance Parameters")
        laps = st.slider("Total Race Laps", min_value=5, max_value=60, value=30, step=5)
        num_cars = st.slider("Number of Cars on Grid", min_value=2, max_value=22, value=10, step=1)
        seed = st.number_input("PRNG Random Seed", min_value=1, max_value=999999, value=42)
        initial_fuel = st.number_input(
            "Starting Fuel Load (kg)", min_value=20.0, max_value=120.0, value=110.0, step=5.0
        )

    with col2:
        st.subheader("⚠️ Incidents & Strategy")
        sc_col1, sc_col2 = st.columns(2)
        with sc_col1:
            vsc_lap = st.number_input("Deploy VSC on Lap (0 = None)", min_value=0, max_value=laps, value=0)
        with sc_col2:
            sc_lap = st.number_input("Deploy Full SC on Lap (0 = None)", min_value=0, max_value=laps, value=0)

        use_ppo = st.checkbox("Control Driver_1 using Trained PPO v2 Agent", value=True)
        st.info(
            "Driver 1 will evaluate neural network policy decisions each lap, while the rest of the field executes realistic strategic heuristics."
        )

    st.markdown("---")
    if st.button("🚀 Run Race Simulation", type="primary", use_container_width=True):
        with st.spinner("Executing C++ simulation and compiling telemetry..."):
            snapshots, df, ai_log = run_simulation(
                laps=laps,
                num_cars=num_cars,
                seed=seed,
                initial_fuel=initial_fuel,
                vsc_lap=vsc_lap,
                sc_lap=sc_lap,
                use_ppo=use_ppo,
            )
            st.session_state["snapshots"] = snapshots
            st.session_state["df"] = df
            st.session_state["ai_log"] = ai_log
            st.session_state["laps"] = laps
            st.success(f"Simulation completed! Winner: **{snapshots[-1].leader_name}** in {snapshots[-1].positions[0]['total_time']:.2f}s.")

    # Show initial classification if available
    if "snapshots" in st.session_state:
        st.subheader("🏆 Race Classification Summary")
        final_snap = st.session_state["snapshots"][-1]
        render_f1_banner(
            final_snap.lap,
            st.session_state["laps"],
            final_snap.safety_car_status,
            final_snap.leader_name,
        )
        render_interactive_timing_tower(final_snap.positions)


# ---------------- PAGE 2: Race Replay (Lap-by-Lap) ----------------
elif page == "⏮️ Race Replay (Lap-by-Lap)":
    st.title("⏮️ Interactive Lap-by-Lap Race Replay")

    if "snapshots" not in st.session_state or not st.session_state["snapshots"]:
        st.warning("No active simulation in memory. Run a simulation from the Configuration page first.")
    else:
        snapshots = st.session_state["snapshots"]
        total_laps = st.session_state.get("laps", len(snapshots))

        st.markdown(
            "Scrub through the race lap-by-lap to observe overtakes, pit window execution, DRS trains, and field compression."
        )

        # Control widgets
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            selected_lap = st.slider("Lap Selector", min_value=1, max_value=total_laps, value=1, step=1)
        with c2:
            st.metric("Total Completed Laps", total_laps)
        with c3:
            st.metric("Cars in Classification", len(snapshots[0].positions))

        # Retrieve selected lap snapshot (1-indexed)
        snap = snapshots[selected_lap - 1]

        # Top banner
        render_f1_banner(snap.lap, total_laps, snap.safety_car_status, snap.leader_name)

        col_left, col_right = st.columns([3, 1])
        with col_left:
            st.subheader(f"⏱️ Timing Tower — Lap {selected_lap}")
            render_interactive_timing_tower(snap.positions)

        with col_right:
            st.subheader("🔍 Driver Focus")
            driver_names = [p["driver"] for p in snap.positions]
            selected_driver = st.selectbox("Inspect Driver", driver_names)
            p_info = next(p for p in snap.positions if p["driver"] == selected_driver)

            st.metric("Position", f"P{p_info['rank']}")
            st.metric("Gap to P1", f"+{p_info['gap_to_leader']:.3f}s" if p_info["rank"] > 1 else "LEADER")
            st.metric("Interval Ahead", f"+{p_info['interval']:.3f}s" if p_info["rank"] > 1 else "—")
            st.metric("Tire Compound", f"{p_info['compound']} ({int(p_info['tire_age'])} laps old)")
            st.metric("Pit Stops Completed", p_info["pit_stops"])
            st.metric("DRS Activations", p_info["drs_count"])
            st.metric("Dirty Air Laps", p_info["dirty_air_count"])


# ---------------- PAGE 3: Strategy & Telemetry Analysis ----------------
elif page == "📊 Strategy & Telemetry Analysis":
    st.title("📊 Multi-Car Strategy & Telemetry Analysis")

    if "df" not in st.session_state or st.session_state["df"] is None:
        st.warning("No active race data available. Run a simulation first.")
    else:
        df = st.session_state["df"]
        all_drivers = sorted(list(df["driver"].unique()))

        st.sidebar.subheader("Filter Drivers")
        selected_drivers = st.sidebar.multiselect(
            "Select Drivers to Display",
            options=all_drivers,
            default=all_drivers[:6],
        )

        tab1, tab2, tab3, tab4 = st.tabs(["📉 Race Gaps", "📈 Position Lap Chart", "🛞 Tire Wear Sawtooth", "⏱️ Stint Timeline"])

        with tab1:
            st.plotly_chart(build_gap_chart(df, selected_drivers), use_container_width=True)

        with tab2:
            st.plotly_chart(build_position_chart(df, selected_drivers), use_container_width=True)

        with tab3:
            st.plotly_chart(build_tire_stint_chart(df, selected_drivers), use_container_width=True)

        with tab4:
            st.plotly_chart(build_stint_timeline_bars(df, selected_drivers), use_container_width=True)


# ---------------- PAGE 4: AI Decision Inspector ----------------
elif page == "🧠 AI Decision Inspector":
    st.title("🧠 Neural Network Strategy Decision Inspector")
    st.markdown(
        "Examine the exact 8-dimensional observation vectors received by the PPO agent and trace its strategic reasoning."
    )

    ai_log = st.session_state.get("ai_log", [])
    if not ai_log:
        st.info("No AI decision logs recorded. Ensure 'Control Driver_1 using Trained PPO v2 Agent' was enabled.")
    else:
        df_ai = pd.DataFrame(ai_log)

        st.subheader("📋 Decision Trajectory Table")
        display_ai = []
        for d in ai_log:
            obs = d["obs"]
            display_ai.append(
                {
                    "Lap": d["lap"],
                    "Action": "PIT NOW" if d["action_pit"] else "STAY OUT",
                    "Target Tire": d["chosen_tire"],
                    "Pre-Pit Tire Age": round(d["tire_age_pre"], 1),
                    "Lap Progress": f"{obs[0]*100:.0f}%",
                    "Normalized Fuel": f"{obs[3]*100:.0f}%",
                    "Scaled Gap to P1": f"{obs[4]:.2f}",
                }
            )
        st.dataframe(pd.DataFrame(display_ai), use_container_width=True, hide_index=True)

        st.subheader("🔍 Deep Observation Feature Breakdown")
        inspect_lap = st.selectbox("Inspect Lap Decision", [d["lap"] for d in ai_log])
        target_dec = next(d for d in ai_log if d["lap"] == inspect_lap)

        obs = target_dec["obs"]
        feature_names = [
            "0. Lap Fraction",
            "1. Tire Age Fraction",
            "2. Compound (0:S, 1:M, 2:H)",
            "3. Fuel Load Fraction",
            "4. Gap to P1 Scaled",
            "5. Gap Ahead Scaled",
            "6. Rank Normalized",
            "7. Laps Remaining Fraction",
        ]

        obs_df = pd.DataFrame({"Feature": feature_names, "Value": [round(v, 4) for v in obs]})
        c_obs, c_act = st.columns([1, 1])
        with c_obs:
            st.dataframe(obs_df, use_container_width=True, hide_index=True)
        with c_act:
            st.markdown(
                f"""
                <div style="background-color: #1e1e2d; padding: 20px; border-radius: 8px; border: 1px solid #3d3d5c;">
                    <h4>Agent Decision at Lap {inspect_lap}</h4>
                    <p><b>Pit Decision:</b> {'🛑 PIT STOP' if target_dec['action_pit'] else '🟢 STAY OUT'}</p>
                    <p><b>Compound Selection:</b> {target_dec['chosen_tire']}</p>
                    <p><b>Current Tire Age:</b> {target_dec['tire_age_pre']:.1f} laps</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------- PAGE 5: Experiment Explorer ----------------
elif page == "📁 Experiment Explorer":
    st.title("📁 Centralized Experiment Explorer")
    st.markdown("Browse, inspect, and analyze historical simulation runs stored under `outputs/experiments/`.")

    base_dir = Path(__file__).resolve().parents[1] / "outputs" / "experiments"
    experiments = RaceDataAdapter.list_saved_experiments(base_dir)

    if not experiments:
        st.info("No saved experiment runs found in `outputs/experiments/`.")
    else:
        run_ids = [exp["run_id"] for exp in experiments]
        selected_run_id = st.selectbox("Select Experiment Run", run_ids)
        target_exp = next(exp for exp in experiments if exp["run_id"] == selected_run_id)

        col_meta, col_cfg = st.columns(2)
        with col_meta:
            st.subheader("ℹ️ Run Metadata")
            st.json(target_exp["metadata"])
        with col_cfg:
            st.subheader("⚙️ Configuration")
            st.json(target_exp["config"])

        if target_exp["summary_md"]:
            st.subheader("📝 Summary Report")
            st.markdown(target_exp["summary_md"])

        if target_exp["plots"]:
            st.subheader("🖼️ Saved Plots")
            for plot_path in target_exp["plots"]:
                st.image(str(plot_path), caption=plot_path.name, use_container_width=True)

        if target_exp["telemetry_df"] is not None:
            st.subheader("📊 Raw Telemetry CSV Data")
            st.dataframe(target_exp["telemetry_df"].head(100), use_container_width=True)


# ---------------- PAGE 6: DP & Strategy Benchmarks ----------------
elif page == "📈 DP & Strategy Benchmarks":
    st.title("📈 Scientific Strategy Benchmarks")
    st.markdown("Run controlled clean-air benchmarks comparing the analytical 5D DP optimizer against strategic heuristics.")

    b_laps = st.slider("Benchmark Laps", min_value=10, max_value=60, value=50, step=5)
    b_trials = st.slider("Monte Carlo Trials per Strategy", min_value=5, max_value=50, value=20, step=5)

    if st.button("🚀 Run Scientific Benchmark", type="primary"):
        with st.spinner("Computing DP forward pass and running Monte Carlo trials..."):
            results = run_clean_air_benchmarks(total_laps=b_laps, initial_fuel=110.0, trials=b_trials)
            st.success("Benchmark completed! Results logged to `outputs/experiments/`.")

            st.subheader("🏆 Comparative Summary")
            rows = []
            for name, r in results.items():
                rows.append(
                    {
                        "Strategy": name,
                        "Mean Race Time (s)": round(r.mean_time, 2),
                        "Std Dev (s)": round(r.std_time, 2),
                        "Min Race Time (s)": round(r.min_time, 2),
                        "Max Race Time (s)": round(r.max_time, 2),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
