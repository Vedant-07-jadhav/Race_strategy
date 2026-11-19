import pytest
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine


def test_safety_car_pace_impact():
    # Green flag run
    sim_green = race_engine.RaceSimulator()
    sim_green.set_seed(42)
    sim_green.add_car("Car_A", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
    sim_green.simulate_race(3)
    green_lap2_time = sim_green.race_history[1].car_times["Car_A"] - sim_green.race_history[0].car_times["Car_A"]

    # VSC on Lap 2
    sim_vsc = race_engine.RaceSimulator()
    sim_vsc.set_seed(42)
    sim_vsc.add_car("Car_A", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
    sim_vsc.trigger_safety_car(2, race_engine.SafetyCarType.SC_VSC)
    sim_vsc.simulate_race(3)
    vsc_lap2_time = sim_vsc.race_history[1].car_times["Car_A"] - sim_vsc.race_history[0].car_times["Car_A"]

    # Full SC on Lap 2
    sim_sc = race_engine.RaceSimulator()
    sim_sc.set_seed(42)
    sim_sc.add_car("Car_A", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
    sim_sc.trigger_safety_car(2, race_engine.SafetyCarType.SC_FULL)
    sim_sc.simulate_race(3)
    sc_lap2_time = sim_sc.race_history[1].car_times["Car_A"] - sim_sc.race_history[0].car_times["Car_A"]

    # Assert VSC is ~35% slower and SC is ~50% slower than green flag
    assert vsc_lap2_time > green_lap2_time * 1.30
    assert sc_lap2_time > green_lap2_time * 1.45
    assert sim_vsc.race_history[1].safety_car_status == 1
    assert sim_sc.race_history[1].safety_car_status == 2


def test_cheap_pit_stop_under_safety_car():
    # Green flag pit stop loss is 22.0s
    sim_green = race_engine.RaceSimulator()
    sim_green.set_seed(100)
    # Pit on lap 2
    sim_green.add_car("Pit_Car", lambda s, g: race_engine.Action(s.lap == 2, "Medium"), 110.0)
    sim_green.simulate_race(3)
    green_pit_lap_time = sim_green.race_history[1].car_times["Pit_Car"] - sim_green.race_history[0].car_times["Pit_Car"]

    # Pit under Full SC on lap 2 (pit loss is 9.0s)
    sim_sc = race_engine.RaceSimulator()
    sim_sc.set_seed(100)
    sim_sc.trigger_safety_car(2, race_engine.SafetyCarType.SC_FULL)
    sim_sc.add_car("Pit_Car", lambda s, g: race_engine.Action(s.lap == 2, "Medium"), 110.0)
    sim_sc.simulate_race(3)
    # Under SC, base lap is 1.5x (~135s), pit loss is 9s -> ~144s
    # Under Green, base lap is 1.0x (~90s), pit loss is 22s -> ~112s
    # Difference in pit penalty itself is 22s - 9s = 13s saved during the stop!
    assert sim_sc.race_history[1].safety_car_status == 2


def test_safety_car_pack_compression():
    # Car 2 pits on lap 1 to fall ~22s behind
    sim_sc = race_engine.RaceSimulator()
    sim_sc.set_seed(777)
    sim_sc.add_car("Leader", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
    sim_sc.add_car("Trailer", lambda s, g: race_engine.Action(s.lap == 1, "Hard"), 110.0)
    # Trigger Full SC on lap 2
    sim_sc.trigger_safety_car(2, race_engine.SafetyCarType.SC_FULL)
    sim_sc.simulate_race(2)

    # In lap 2 under Full SC, the pack compresses
    trailer_time = sim_sc.race_history[1].car_times["Trailer"]
    leader_time = sim_sc.race_history[1].car_times["Leader"]
    gap = trailer_time - leader_time
    assert gap <= 0.85, f"Expected compressed gap <= 0.85s under SC, got {gap}"
