import race_engine
from stable_baselines3 import PPO
import numpy as np

# 1. Load the fully optimized model
model = PPO.load("f1_rl_strategist_pro", device="cpu")

# 2. Fresh standalone simulator setup
sim = race_engine.RaceSimulator()
TOTAL_LAPS = 50
AGENT_NAME = "RL_Agent"
BOT_NAME = "Bot_Conservative"

# Register placeholder strategies since we will control the agent manually lap-by-lap
sim.add_car(AGENT_NAME, lambda s, g: race_engine.Action(False, "Soft"), 110.0)
sim.add_car(BOT_NAME, lambda s, g: race_engine.Action(s.tire_age > 22, "Medium"), 110.0)

print("--- STARTING DETERMINISTIC STANDALONE EVALUATION RACE ---")

for lap in range(TOTAL_LAPS):
    # Get current observation for the agent
    if not sim.race_history:
        obs = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    else:
        hist = sim.race_history[-1]
        current_lap = float(hist.lap)
        tire_age = float(sim.race_history[-1].car_tire_ages[AGENT_NAME])
        gap = float(hist.car_times[AGENT_NAME] - hist.car_times[hist.leader_name])
        obs = np.array([current_lap, tire_age, gap], dtype=np.float32)
    
    # Predict next strategic move using the neural network
    action, _ = model.predict(obs, deterministic=True)
    
    tires = {0: "Soft", 1: "Medium", 2: "Hard"}
    agent_action = race_engine.Action(bool(action[0]), tires[action[1]])
    print(f"Lap {lap+1}: Agent Chose Pit={bool(action[0])}, Tire={tires[action[1]]}")

    # Inject the action directly into the standalone lap execution function
    sim.simulate_one_lap(AGENT_NAME, agent_action)

# Print the true uninhibited results
sim.print_results()