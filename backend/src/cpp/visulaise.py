import race_engine
import matplotlib.pyplot as plt
import numpy as np

sim = race_engine.RaceSimulator()
engine = race_engine.RaceEngine() 

# 1. Define strategies (Fix case sensitivity)
def aggressive(state, gap):
    return race_engine.Action(True, "Soft") if state.tire_age > 12 else race_engine.Action(False, "Soft")

def conservative(state, gap):
    return race_engine.Action(True, "Hard") if state.tire_age > 25 else race_engine.Action(False, "Soft")

def reactive(state, gap):
    # Force this car to stay out as long as the leader to keep the gap small
    if gap < 1.0:
        return race_engine.Action(False, "Soft") # Stay in the slipstream
    if state.tire_age > 20:
        return race_engine.Action(True, "Medium")
    return race_engine.Action(False, "Soft")

# 2. Setup Cars
opt_actions = engine.get_optimal_DP_strategy(50, 110.0)
sim.add_car("Aggressive", aggressive, 110.0)
sim.add_car("DP Optimal", lambda s, g: opt_actions[s.lap-1], 110.0)
sim.add_car("Conservative 1-Stop", conservative, 110.0)
sim.add_car("Reactive Undercut", reactive, 110.0)

# 3. RUN THE SIMULATION (Order matters!)
sim.simulate_race(50)
sim.print_results()

# 4. Extract Data
history = sim.race_history 
laps = [r.lap for r in history]
car_names = list(history[0].car_times.keys())

# --- CREATE DASHBOARD ---
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# PLOT 1: RACE GAPS TO LEADER
for name in car_names:
    gaps = [r.car_times[name] - r.car_times[r.leader_name] for r in history]
    axes[0].plot(laps, gaps, label=name, linewidth=2)

axes[0].invert_yaxis() 
axes[0].set_title("Race Gaps to Leader (Leader = 0)", fontsize=14, fontweight='bold')
axes[0].set_ylabel("Gap (seconds)")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# PLOT 2: TIRE AGE (SAWTOOTH)
for name in car_names:
    ages = [r.car_tire_ages[name] for r in history]
    axes[1].plot(laps, ages, label=name, linestyle='--')

axes[1].set_title("Effective Tire Age (Degradation)", fontsize=14, fontweight='bold')
axes[1].set_xlabel("Lap Number")
axes[1].set_ylabel("Tire Age")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.show()

# PLOT 3: INTERACTION SUMMARY (Bar Chart)
plt.figure(figsize=(10, 5))
x = np.arange(len(car_names))
drs = [history[-1].car_stats[name].drs_count for name in car_names]
dirty = [history[-1].car_stats[name].dirty_air_count for name in car_names]

plt.bar(x - 0.2, drs, 0.4, label='DRS Laps', color='green')
plt.bar(x + 0.2, dirty, 0.4, label='Dirty Air Laps', color='red')
plt.xticks(x, car_names)
plt.title("Race Interaction Summary")
plt.ylabel("Count")
plt.legend()
plt.show()