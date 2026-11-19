import matplotlib.pyplot as plt
import pytest
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine
from race.visualization.plots import plot_race_gaps, plot_tire_stints
from race.visualization.timing_tower import render_timing_tower


def test_timing_tower_rendering():
    car_times = {"Car_A": 90.5, "Car_B": 91.2, "Car_C": 93.0}
    car_tire_ages = {"Car_A": 5.0, "Car_B": 12.0, "Car_C": 22.0}
    car_compounds = {"Car_A": "Soft", "Car_B": "Medium", "Car_C": "Hard"}
    pit_counts = {"Car_A": 0, "Car_B": 1, "Car_C": 2}

    output = render_timing_tower(
        lap=15,
        total_laps=50,
        car_times=car_times,
        car_tire_ages=car_tire_ages,
        car_compounds=car_compounds,
        pit_counts=pit_counts,
        safety_car_status=0,
        top_n=3,
    )

    assert "F1 TIMING TOWER" in output
    assert "Car_A" in output
    assert "LEADER" in output
    assert "+ 0.700s" in output  # 91.2 - 90.5


def test_plotting_utilities_with_simulation():
    sim = race_engine.RaceSimulator()
    sim.set_seed(42)
    sim.add_car("Car_1", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
    sim.add_car("Car_2", lambda s, g: race_engine.Action(False, "Hard"), 110.0)
    sim.simulate_race(5)

    fig_gaps = plot_race_gaps(sim.race_history)
    assert isinstance(fig_gaps, plt.Figure)
    plt.close(fig_gaps)

    fig_stints = plot_tire_stints(sim.race_history)
    assert isinstance(fig_stints, plt.Figure)
    plt.close(fig_stints)
