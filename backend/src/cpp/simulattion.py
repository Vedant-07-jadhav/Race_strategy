import race_engine
import matplotlib.pyplot as plt
import numpy as np

# 1. Strategy Definitions
# High-interaction strategies designed for the sector-based engine
def drs_train_follower(state, gap):
    # Follower stays close to benefit from DRS/Slipstream
    if 0.0 < gap < 1.5 and state.tire_age < 28:
        return race_engine.Action(False, "Soft") 
    return race_engine.Action(True, "Medium") if state.tire_age > 18 else race_engine.Action(False, "Soft")

def aggressive_undercut(state, gap):
    # Attacker pits early if stuck in the dirty air window
    if 0.5 < gap < 1.8 and state.tire_age > 10:
        return race_engine.Action(True, "Soft")
    return race_engine.Action(True, "Medium") if state.tire_age > 22 else race_engine.Action(False, "Soft")

def defensive_leader(state, gap):
    # Leader reacts to being hunted (gap < 0 means car is ahead)
    if -1.2 < gap < 0.0 and state.tire_age > 15:
        return race_engine.Action(True, "Medium") 
    return race_engine.Action(True, "Hard") if state.tire_age > 25 else race_engine.Action(False, "Soft")

# 2. Setup Simulator
sim = race_engine.RaceSimulator()
TOTAL_LAPS = 50
INITIAL_FUEL = 110.0

# Add cars to the grid (Note the internal grid stagger logic)
sim.add_car("Defensive Lead", defensive_leader, INITIAL_FUEL)
sim.add_car("Follower 1", drs_train_follower, INITIAL_FUEL)
sim.add_car("Follower 2", drs_train_follower, INITIAL_FUEL)
sim.add_car("Attacker", aggressive_undercut, INITIAL_FUEL)

# 3. Run Simulation
print("Running Sector-Based Simulation...")
sim.simulate_race(TOTAL_LAPS)
sim.print_results()

# 4. Extract History for Visualisation
history = sim.race_history
laps = [r.lap for r in history]
car_names = list(history[0].car_times.keys())

# --- PLOTTING DASHBOARD ---
fig, axes = plt.subplots(2, 1, figsize=(15, 12))

# Plot 1: Race Gaps to Leader (The "Gap Chart")
# This shows how cars swap positions mid-lap
for name in car_names:
    gaps = [r.car_times[name] - r.car_times[r.leader_name] for r in history]
    axes[0].plot(laps, gaps, label=name, linewidth=2)

axes[0].invert_yaxis() 
axes[0].set_title("Race Gaps to Leader (Sector-Snapshot Precision)", fontsize=14, fontweight='bold')
axes[0].set_ylabel("Gap (seconds)")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# Plot 2: Tire Age (The "Sawtooth" Chart)
# Shows higher wear (steeper slopes) when in Dirty Air
for name in car_names:
    ages = [r.car_tire_ages[name] for r in history]
    axes[1].plot(laps, ages, label=f"{name} Tire Age", linestyle='--')

axes[1].set_title("Effective Tire Age (Reflecting Dirty Air Wear)", fontsize=14, fontweight='bold')
axes[1].set_xlabel("Lap Number")
axes[1].set_ylabel("Tire Age")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.show()

# Plot 3: Cumulative Interaction Performance
plt.figure(figsize=(10, 5))
x = np.arange(len(car_names))
drs_vals = [history[-1].car_stats[name].drs_count for name in car_names]
slip_vals = [history[-1].car_stats[name].slipstream_count for name in car_names]
dirty_vals = [history[-1].car_stats[name].dirty_air_count for name in car_names]

plt.bar(x - 0.2, drs_vals, 0.2, label='DRS Sectors', color='#2ecc71')
plt.bar(x, slip_vals, 0.2, label='Slipstream Sectors', color='#3498db')
plt.bar(x + 0.2, dirty_vals, 0.2, label='Dirty Air Sectors', color='#e74c3c')

plt.xticks(x, car_names)
plt.title("Total Sector-Level Interactions", fontsize=14)
plt.ylabel("Total Count (Sectors)")
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.show()