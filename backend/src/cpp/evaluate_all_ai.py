import race_engine
from stable_baselines3 import PPO
import numpy as np

# 1. Load the "Pro" Brain
model = PPO.load("f1_rl_strategist_pro", device="cpu")

sim = race_engine.RaceSimulator()
TOTAL_LAPS = 50

# 2. Add 22 Cars to the Grid
car_names = [f"AI_Driver_{i+1}" for i in range(22)]
for name in car_names:
    sim.add_car(name, lambda s, g: race_engine.Action(False, "Soft"), 110.0)

print(f"--- STARTING MULTI-AGENT NEURAL NETWORK RACE ({TOTAL_LAPS} LAPS) ---")

for lap in range(TOTAL_LAPS):
    # Dictionary to hold all 22 decisions
    lap_actions = {}
    
    # 3. Ask the Neural Net for 22 separate decisions based on their unique states
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
        
        # Save decision into the dictionary
        lap_actions[name] = cpp_action
        
        if bool(action[0]):
            print(f"🏎️ Lap {lap+1}: {name} PITTED for {tires[action[1]]}!")

    # 4. Inject all 22 actions simultaneously into the C++ Physics Engine!
    sim.simulate_one_lap(lap_actions)

print("\n--- RACE COMPLETED ---")
sim.print_results()