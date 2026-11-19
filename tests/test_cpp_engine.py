import pytest
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine


def test_engine_initialization():
    engine = race_engine.RaceEngine()
    assert engine is not None


def test_tire_degradation_ordering():
    engine = race_engine.RaceEngine()
    # At zero age, Soft base offset is 0, Medium is 0.8, Hard is 1.8
    soft_time = engine.compute_lap_time_deterministic("Soft", 0, 100.0)
    medium_time = engine.compute_lap_time_deterministic("Medium", 0, 100.0)
    hard_time = engine.compute_lap_time_deterministic("Hard", 0, 100.0)
    assert soft_time < medium_time < hard_time

    # Soft degrades much faster than Hard
    soft_aged = engine.compute_lap_time_deterministic("Soft", 25, 50.0)
    hard_aged = engine.compute_lap_time_deterministic("Hard", 25, 50.0)
    soft_deg = soft_aged - engine.compute_lap_time_deterministic("Soft", 0, 50.0)
    hard_deg = hard_aged - engine.compute_lap_time_deterministic("Hard", 0, 50.0)
    assert soft_deg > hard_deg


def test_fuel_effect_is_linear():
    engine = race_engine.RaceEngine()
    t_heavy = engine.compute_lap_time_deterministic("Medium", 10, 100.0)
    t_light = engine.compute_lap_time_deterministic("Medium", 10, 50.0)
    # Expected penalty is 0.035 s/kg * 50 kg = 1.75 s
    delta = t_heavy - t_light
    assert abs(delta - (50.0 * 0.035)) < 1e-4


def test_dp_optimizer_bounds_and_two_compounds():
    engine = race_engine.RaceEngine()
    # Test with standard 50 laps and extended 55 laps to ensure no buffer overflow
    for laps in [50, 55]:
        actions = engine.get_optimal_DP_strategy(laps, 110.0)
        assert len(actions) == laps

        # Check two-compound FIA rule
        compounds_used = set()
        for a in actions:
            if a.new_tire:
                compounds_used.add(a.new_tire)
        assert len(compounds_used) >= 2, f"Strategy for {laps} laps used only {compounds_used}"


def test_simulator_multi_car_sorting_and_history():
    sim = race_engine.RaceSimulator()
    sim.set_seed(42)
    sim.add_car("Fast_Car", lambda s, g: race_engine.Action(False, "Soft"), 100.0)
    sim.add_car("Slow_Car", lambda s, g: race_engine.Action(False, "Hard"), 100.0)

    sim.simulate_race(5)
    assert len(sim.race_history) == 5
    last_record = sim.race_history[-1]
    assert last_record.lap == 5
    assert "Fast_Car" in last_record.car_times
    assert "Slow_Car" in last_record.car_times
    assert last_record.car_times["Fast_Car"] < last_record.car_times["Slow_Car"]
