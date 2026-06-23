from race._bootstrap import ensure_project_paths

ensure_project_paths()

import numpy as np
import race_engine
from stable_baselines3 import PPO


def main():
    model = PPO.load("f1_rl_strategist_pro", device="cpu")

    sim = race_engine.RaceSimulator()
    total_laps = 50

    car_names = [f"AI_Driver_{i + 1}" for i in range(22)]
    for name in car_names:
        sim.add_car(name, lambda s, g: race_engine.Action(False, "Soft"), 110.0)

    print(f"--- STARTING MULTI-AGENT NEURAL NETWORK RACE ({total_laps} LAPS) ---")

    for lap in range(total_laps):
        lap_actions = {}

        for name in car_names:
            if not sim.race_history:
                obs = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            else:
                hist = sim.race_history[-1]
                current_lap = float(hist.lap)
                tire_age = float(hist.car_tire_ages[name])
                gap = float(hist.car_times[name] - hist.car_times[hist.leader_name])
                obs = np.array([current_lap, tire_age, gap], dtype=np.float32)

            action, _ = model.predict(obs, deterministic=True)
            tires = {0: "Soft", 1: "Medium", 2: "Hard"}
            cpp_action = race_engine.Action(bool(action[0]), tires[action[1]])
            lap_actions[name] = cpp_action

            if bool(action[0]):
                print(f"🏎️ Lap {lap + 1}: {name} PITTED for {tires[action[1]]}!")

        sim.simulate_one_lap(lap_actions)

    print("\n--- RACE COMPLETED ---")
    sim.print_results()


if __name__ == "__main__":
    main()
