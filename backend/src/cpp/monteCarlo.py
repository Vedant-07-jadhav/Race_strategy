import numpy as np
import race_engine
import matplotlib.pyplot as plt

# 1. Heuristic Strategies
def aggressive_strategy(state):
    if state.tire_age > 12:
        return race_engine.Action(True, "Soft")
    return race_engine.Action(False, "")

def conservative_strategy(state):
    if state.tire_age > 25:
        return race_engine.Action(True, "Hard")
    return race_engine.Action(False, "")

# 2. Initialize Engine
TOTAL_LAPS = 50
INITIAL_FUEL = 110.0
engine = race_engine.RaceEngine()

# 3. Get Optimal Strategy (DP)
# This returns a list: [Action_Lap1, Action_Lap2, ...]
optimal_actions = engine.get_optimal_DP_strategy(TOTAL_LAPS, INITIAL_FUEL)

# --- TRACKING PIT STOPS ---
print("--- DP OPTIMAL PIT LOG ---")
# The first tire is what we start on (Lap 1)
print(f"Start: {optimal_actions[0].new_tire}") 

for i, action in enumerate(optimal_actions):
    if action.pit and i > 0: # i is 0-indexed, so Lap is i + 1
        print(f"Lap {i+1}: PIT for {action.new_tire}")

# Wrapper for simulator
def dp_strategy_wrapper(state):
    return optimal_actions[state.lap - 1]

# 4. Monte Carlo Simulation
def monte_carlo(strategy_fn, runs=100):
    results = []
    for _ in range(runs):
        # Fresh engine instance for each run to handle noise/randomness
        eng = race_engine.RaceEngine() 
        res, _ = eng.simulate(TOTAL_LAPS, INITIAL_FUEL, strategy_fn)
        results.append(res.total_time)

    results = np.array(results)
    return {
        "mean": np.mean(results),
        "std": np.std(results),
        "min": np.min(results),
        "max": np.max(results),
        "all_results": results  
    }

mc_agg = monte_carlo(aggressive_strategy, 100)
mc_con = monte_carlo(conservative_strategy, 100)
mc_dp  = monte_carlo(dp_strategy_wrapper, 100)

print("\n--- MONTE CARLO RESULTS ---")
print(f"Aggressive:   Mean {mc_agg['mean']:.2f} | Std {mc_agg['std']:.2f}")
print(f"Conservative: Mean {mc_con['mean']:.2f} | Std {mc_con['std']:.2f}")
print(f"DP Optimal:   Mean {mc_dp['mean']:.2f} | Std {mc_dp['std']:.2f}")

# 5. Visualization
plt.figure(figsize=(10, 6))
plt.hist(mc_agg["all_results"], bins=20, alpha=0.5, label="Aggressive", color='red')
plt.hist(mc_con["all_results"], bins=20, alpha=0.5, label="Conservative", color='blue')
plt.hist(mc_dp["all_results"], bins=20, alpha=0.5, label="DP (Constrained)", color='green')

plt.legend()
plt.title("Strategy Robustness: Race Time Distribution")
plt.xlabel("Total Race Time (seconds)")
plt.ylabel("Frequency")
plt.grid(axis='y', alpha=0.3)
plt.show()