import race_engine
from stable_baselines3 import PPO
import numpy as np

# 1. Load the model
model = PPO.load("f1_rl_strategist_pro", device="cpu")

sim = race_engine.RaceSimulator()
TOTAL_LAPS = 50

# 2. Add the RL Agent
sim.add_car("RL_Agent", lambda s, g: race_engine.Action(False, "Soft"), 110.0)

# 3. Add 21 Bots with REAL, varying strategies to create a realistic, spreading field
def bot_conservative(s, g): return race_engine.Action(s.tire_age > 22, "Medium")
def bot_aggressive(s, g): return race_engine.Action(s.tire_age > 16, "Hard")
def bot_soft_runner(s, g): return race_engine.Action(s.tire_age > 18, "Soft")

for i in range(1, 8):
    sim.add_car(f"Bot_Conservative_{i}", bot_conservative, 110.0)
    sim.add_car(f"Bot_Aggressive_{i}", bot_aggressive, 110.0)
    sim.add_car(f"Bot_SoftRunner_{i}", bot_soft_runner, 110.0)

print(f"--- STARTING REALISTIC 22-CAR RACE ---")

for lap in range(TOTAL_LAPS):
    # Get RL Agent Observation
    if not sim.race_history:
        obs = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    else:
        hist = sim.race_history[-1]
        current_lap = float(hist.lap)
        tire_age = float(hist.car_tire_ages["RL_Agent"])
        gap = float(hist.car_times["RL_Agent"] - hist.car_times[hist.leader_name])
        obs = np.array([current_lap, tire_age, gap], dtype=np.float32)
    
    # RL Agent Decision
    action, _ = model.predict(obs, deterministic=True)
    tires = {0: "Soft", 1: "Medium", 2: "Hard"}
    agent_action = race_engine.Action(bool(action[0]), tires[action[1]])
    
    # Simulate Lap (Inject RL Agent; bots use their heuristic functions automatically)
    sim.simulate_one_lap("RL_Agent", agent_action)
    
    # Check and Print Pit History for ALL cars
    if len(sim.race_history) > 1:
        prev_hist = sim.race_history[-2]
        curr_hist = sim.race_history[-1]
        
        for car_name in curr_hist.car_times.keys():
            prev_age = prev_hist.car_tire_ages[car_name]
            curr_age = curr_hist.car_tire_ages[car_name]
            
            # If current tire age is less than the previous lap, they pitted!
            if curr_age < prev_age:
                print(f"🏎️ Lap {lap+1}: {car_name} PITTED!")

print("\n--- RACE COMPLETED ---")
sim.print_results()