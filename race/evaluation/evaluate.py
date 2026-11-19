"""22-Car Multi-Agent Race Evaluation with Live Timing Tower and Experiment Tracking."""

import argparse
from pathlib import Path
from typing import Optional
import numpy as np
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine
from race.tracking.experiment_tracker import ExperimentTracker
from race.visualization.timing_tower import render_timing_tower
from race.visualization.plots import plot_race_gaps, plot_tire_stints


def evaluate(
    total_laps: int = 50,
    model_name: str = "f1_rl_strategist_v2",
    display_interval: int = 10,
    seed: int = 42,
    sc_schedule: Optional[dict] = None,
    tracker: Optional[ExperimentTracker] = None,
):
    try:
        from stable_baselines3 import PPO
    except ImportError:
        PPO = None

    if tracker is None:
        config = {
            "experiment": "22_car_multi_agent_evaluation",
            "total_laps": total_laps,
            "cars": 22,
            "model_name": model_name,
            "seed": seed,
            "safety_car_schedule": sc_schedule or {},
        }
        tracker = ExperimentTracker("multi_agent_22car_eval", config=config)

    # Search for model checkpoint
    model = None
    project_root = Path(__file__).resolve().parents[2]
    checkpoint_candidates = [
        project_root / "models" / "checkpoints" / f"{model_name}.zip",
        project_root / f"{model_name}.zip",
        project_root / "models" / "checkpoints" / "legacy" / f"{model_name}.zip",
        project_root / "models" / "checkpoints" / "f1_rl_strategist_pro.zip",
    ]

    if PPO is not None:
        for cand in checkpoint_candidates:
            if cand.exists():
                try:
                    model = PPO.load(str(cand).replace(".zip", ""), device="cpu")
                    print(f"[INFO] Loaded trained policy: {cand.name}")
                    break
                except Exception as e:
                    print(f"[WARN] Failed loading {cand.name}: {e}")

    sim = race_engine.RaceSimulator()
    sim.set_seed(seed)

    if sc_schedule:
        sim.set_safety_car_schedule(sc_schedule)

    car_names = [f"AI_Driver_{i + 1}" for i in range(22)]
    car_compounds = {name: "Soft" for name in car_names}
    pit_counts = {name: 0 for name in car_names}

    for name in car_names:
        sim.add_car(name, lambda s, g: race_engine.Action(False, "Soft"), 110.0)

    print(f"\n{'='*86}")
    print(f"--- STARTING 22-CAR MULTI-AGENT RACE ({total_laps} LAPS, SEED {seed}) ---")
    print(f"Run Directory: {tracker.run_dir}")
    print(f"{'='*86}\n")

    tires = {0: "Soft", 1: "Medium", 2: "Hard"}

    for lap in range(total_laps):
        lap_actions = {}
        current_lap_num = lap + 1

        for name in car_names:
            if not sim.race_history:
                obs = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            else:
                hist = sim.race_history[-1]
                cur_lap = float(hist.lap)
                tire_age = float(hist.car_tire_ages[name])
                gap = float(hist.car_times[name] - hist.car_times[hist.leader_name])
                obs = np.array([cur_lap, tire_age, gap], dtype=np.float32)

            if model is not None and model.observation_space.shape[0] == 3:
                action, _ = model.predict(obs, deterministic=True)
                pitted = bool(action[0])
                compound = tires[int(action[1])]
            else:
                # Robust heuristic fallback: pit Soft when tire age > 16, pit Medium when tire age > 24
                curr_age = obs[1] if sim.race_history else 0.0
                curr_comp = car_compounds[name]
                threshold = 16.0 if curr_comp == "Soft" else 24.0
                pitted = curr_age > threshold
                compound = "Medium" if curr_comp == "Soft" else "Hard"

            if pitted:
                car_compounds[name] = compound
                pit_counts[name] += 1

            lap_actions[name] = race_engine.Action(pitted, compound)

        sim.simulate_one_lap(lap_actions)
        hist = sim.race_history[-1]

        # Log telemetry
        for name in car_names:
            tracker.log_simulation_lap(
                {
                    "lap": current_lap_num,
                    "car": name,
                    "time": hist.car_times[name],
                    "tire_age": hist.car_tire_ages[name],
                    "compound": car_compounds[name],
                    "pit_stops": pit_counts[name],
                    "safety_car": hist.safety_car_status,
                }
            )

        # Print timing tower at requested intervals and final lap
        if current_lap_num == 1 or current_lap_num % display_interval == 0 or current_lap_num == total_laps:
            tower_str = render_timing_tower(
                lap=current_lap_num,
                total_laps=total_laps,
                car_times=hist.car_times,
                car_tire_ages=hist.car_tire_ages,
                car_compounds=car_compounds,
                pit_counts=pit_counts,
                safety_car_status=hist.safety_car_status,
                top_n=10,
            )
            print(tower_str)

    # Post-race metrics and plots
    final_hist = sim.race_history
    winner = final_hist[-1].leader_name
    winner_time = final_hist[-1].car_times[winner]

    tracker.log_metric("winner", winner)
    tracker.log_metric("winning_time", winner_time)
    tracker.log_metric("total_cars", 22)
    tracker.log_metric("total_pit_stops", sum(pit_counts.values()))

    fig_gaps = plot_race_gaps(final_hist, title="22-Car Multi-Agent Race Gaps to Leader")
    tracker.save_plot(fig_gaps, "22_car_race_gaps.png")

    fig_tires = plot_tire_stints(final_hist, title="22-Car Field Tire Degradation Stints")
    tracker.save_plot(fig_tires, "22_car_tire_stints.png")

    summary_notes = (
        f"22-car simulation completed. Winner: {winner} with total race time of {winner_time:.2f}s. "
        f"Field completed {sum(pit_counts.values())} pit stops."
    )
    tracker.finish(status="Passed", summary_notes=summary_notes)

    return sim, tracker


def main():
    parser = argparse.ArgumentParser(description="Evaluate 22-Car Grid with Timing Tower")
    parser.add_argument("--laps", type=int, default=50, help="Total race laps")
    parser.add_argument("--interval", type=int, default=10, help="Timing tower display interval")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--vsc-lap", type=int, default=0, help="Lap to trigger VSC (0 for none)")
    parser.add_argument("--sc-lap", type=int, default=0, help="Lap to trigger Full SC (0 for none)")
    args = parser.parse_args()

    sc_sched = {}
    if args.vsc_lap > 0:
        sc_sched[args.vsc_lap] = 1
    if args.sc_lap > 0:
        sc_sched[args.sc_lap] = 2

    evaluate(
        total_laps=args.laps,
        display_interval=args.interval,
        seed=args.seed,
        sc_schedule=sc_sched,
    )


if __name__ == "__main__":
    main()
