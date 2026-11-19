"""Race Strategy Visualization and Plotting Utilities."""

from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np


def plot_race_gaps(
    race_history,
    focus_cars: Optional[List[str]] = None,
    title: str = "Race Gaps to Leader",
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """Generate race gap chart showing gap to leader across all laps."""
    fig, ax = plt.subplots(figsize=(12, 6))

    laps = [r.lap for r in race_history]
    all_cars = list(race_history[0].car_times.keys())
    cars_to_plot = focus_cars if focus_cars else all_cars[:6]

    for car in cars_to_plot:
        gaps = [r.car_times[car] - r.car_times[r.leader_name] for r in race_history]
        ax.plot(laps, gaps, label=car, linewidth=2.0)

    # Highlight SC periods if present
    for r in race_history:
        if r.safety_car_status == 1:
            ax.axvspan(r.lap - 0.5, r.lap + 0.5, color="yellow", alpha=0.15, label="VSC" if r.lap == 1 else "")
        elif r.safety_car_status == 2:
            ax.axvspan(r.lap - 0.5, r.lap + 0.5, color="orange", alpha=0.25, label="Full SC" if r.lap == 1 else "")

    ax.invert_yaxis()
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Lap Number", fontsize=12)
    ax.set_ylabel("Gap to Leader (seconds)", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches="tight")

    return fig


def plot_tire_stints(
    race_history,
    focus_cars: Optional[List[str]] = None,
    title: str = "Effective Tire Age & Pit Stops",
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """Generate sawtooth tire wear and pit stop stint plot."""
    fig, ax = plt.subplots(figsize=(12, 5))

    laps = [r.lap for r in race_history]
    all_cars = list(race_history[0].car_times.keys())
    cars_to_plot = focus_cars if focus_cars else all_cars[:5]

    for car in cars_to_plot:
        ages = [r.car_tire_ages[car] for r in race_history]
        ax.plot(laps, ages, label=car, linewidth=1.8, linestyle="--")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Lap Number", fontsize=12)
    ax.set_ylabel("Tire Age (Laps Equivalent)", fontsize=12)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left")

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches="tight")

    return fig


def plot_strategy_benchmark_comparison(
    benchmark_results: Dict[str, Any],
    title: str = "Strategy Robustness & Total Race Time Distribution",
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """Plot distribution and comparison of total race times across strategy baselines."""
    fig, ax = plt.subplots(figsize=(10, 6))

    names = list(benchmark_results.keys())
    means = [res.mean_time for res in benchmark_results.values()]
    stds = [res.std_time for res in benchmark_results.values()]

    colors = ["#2ecc71", "#e74c3c", "#3498db", "#9b59b6"][: len(names)]
    bars = ax.bar(names, means, yerr=stds, capsize=6, color=colors, alpha=0.8, edgecolor="black")

    # Add text labels on bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval * 0.98,
            f"{yval:.1f}s",
            ha="center",
            va="top",
            color="white",
            fontweight="bold",
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Race Time (seconds)", fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches="tight")

    return fig
