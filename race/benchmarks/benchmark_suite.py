"""Scientific benchmark runner for evaluating DP, heuristic, and RL strategies under equivalent conditions."""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
import numpy as np
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine
from race.tracking.experiment_tracker import ExperimentTracker
from race.visualization.plots import plot_strategy_benchmark_comparison


@dataclass
class BenchmarkResult:
    name: str
    mean_time: float
    std_time: float
    min_time: float
    max_time: float
    pit_counts: List[int]
    all_times: List[float]


def evaluate_strategy_monte_carlo(
    name: str,
    strategy_fn: Callable,
    total_laps: int = 50,
    initial_fuel: float = 110.0,
    trials: int = 30,
    base_seed: int = 42,
) -> BenchmarkResult:
    times = []
    pits = []

    for i in range(trials):
        engine = race_engine.RaceEngine()
        engine.set_seed(base_seed + i)
        state, history = engine.simulate(total_laps, initial_fuel, strategy_fn)
        times.append(state.total_time)

        pit_count = 0
        for idx in range(1, len(history)):
            if history[idx].tire_age < history[idx - 1].tire_age or history[idx].tire != history[idx - 1].tire:
                pit_count += 1
        pits.append(pit_count)

    times_arr = np.array(times)
    return BenchmarkResult(
        name=name,
        mean_time=float(np.mean(times_arr)),
        std_time=float(np.std(times_arr)),
        min_time=float(np.min(times_arr)),
        max_time=float(np.max(times_arr)),
        pit_counts=pits,
        all_times=times,
    )


def run_clean_air_benchmarks(
    total_laps: int = 50,
    initial_fuel: float = 110.0,
    trials: int = 30,
    tracker: Optional[ExperimentTracker] = None,
):
    if tracker is None:
        config = {
            "total_laps": total_laps,
            "initial_fuel": initial_fuel,
            "trials": trials,
            "algorithms": ["DP Optimal", "Aggressive Soft", "Conservative Hard"],
            "seed_base": 42,
        }
        tracker = ExperimentTracker("clean_air_benchmarks", config=config)

    engine = race_engine.RaceEngine()
    dp_actions = engine.get_optimal_DP_strategy(total_laps, initial_fuel)

    def dp_strat(s):
        return dp_actions[s.lap - 1]

    def agg_strat(s):
        if s.tire_age > 14:
            return race_engine.Action(True, "Soft")
        return race_engine.Action(False, s.tire.name)

    def con_strat(s):
        if s.tire_age > 25:
            return race_engine.Action(True, "Hard")
        return race_engine.Action(False, s.tire.name)

    strategies = {
        "DP Optimal (2-Comp)": dp_strat,
        "Aggressive Soft": agg_strat,
        "Conservative Hard": con_strat,
    }

    results = {}
    print(f"\n{'='*70}")
    print(f"--- RUNNING CONTROLLED BENCHMARK ({trials} TRIALS, {total_laps} LAPS) ---")
    print(f"Run Directory: {tracker.run_dir}")
    print(f"{'='*70}")

    for name, strat in strategies.items():
        res = evaluate_strategy_monte_carlo(name, strat, total_laps, initial_fuel, trials=trials)
        results[name] = res
        tracker.log_metric(f"{name}_mean", res.mean_time)
        tracker.log_metric(f"{name}_std", res.std_time)
        tracker.log_metric(f"{name}_min", res.min_time)
        print(f"{name:25} | Mean: {res.mean_time:.2f}s | Std: {res.std_time:.2f}s | Min: {res.min_time:.2f}s")

    # Generate benchmark comparison plot
    fig = plot_strategy_benchmark_comparison(results)
    tracker.save_plot(fig, "strategy_benchmark_distribution.png")

    # Log summary CSV
    for name, res in results.items():
        for trial_idx, t_val in enumerate(res.all_times):
            tracker.log_simulation_lap(
                {
                    "strategy": name,
                    "trial": trial_idx + 1,
                    "race_time": t_val,
                    "pit_stops": res.pit_counts[trial_idx],
                }
            )

    dp_time = results["DP Optimal (2-Comp)"].mean_time
    agg_delta = results["Aggressive Soft"].mean_time - dp_time
    con_delta = results["Conservative Hard"].mean_time - dp_time

    summary_notes = (
        f"DP Optimal benchmark completed across {trials} trials. "
        f"DP Mean: {dp_time:.2f}s. "
        f"Aggressive Soft delta: +{agg_delta:.2f}s. "
        f"Conservative Hard delta: +{con_delta:.2f}s."
    )

    tracker.finish(status="Passed", summary_notes=summary_notes)
    print(f"{'='*70}\n")
    return results


if __name__ == "__main__":
    run_clean_air_benchmarks(total_laps=50, initial_fuel=110.0, trials=30)
