import pytest
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine


def test_reproducibility_with_seed():
    def run_sim(seed):
        sim = race_engine.RaceSimulator()
        sim.set_seed(seed)
        sim.add_car("Car_A", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
        sim.add_car("Car_B", lambda s, g: race_engine.Action(False, "Medium"), 110.0)
        sim.simulate_race(20)
        return sim.race_history[-1].car_times["Car_A"], sim.race_history[-1].car_times["Car_B"]

    time_a1, time_b1 = run_sim(seed=4242)
    time_a2, time_b2 = run_sim(seed=4242)
    assert time_a1 == time_a2
    assert time_b1 == time_b2

    # Different seeds should produce statistically divergent noise
    time_a3, _ = run_sim(seed=9999)
    assert time_a1 != time_a3
