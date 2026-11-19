"""Enhanced Gymnasium environment (v2) with rich observation space and time-aligned rewards."""

from typing import Dict, Tuple
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine

TIRE_COMPOUND_MAP = {0: "Soft", 1: "Medium", 2: "Hard"}
REVERSE_TIRE_MAP = {"Soft": 0, "Medium": 1, "Hard": 2}


class RaceEnvV2(gym.Env):
    """Enriched Environment for Formula 1 Strategy RL.

    Observation Space (8 dimensions):
    0. Normalized current lap [0.0, 1.0]
    1. Normalized tire age [0.0, 1.0] (clipped at 50 laps)
    2. Current tire compound one-hot/ordinal [0: Soft, 1: Medium, 2: Hard]
    3. Normalized remaining fuel load [0.0, 1.0] (110 kg max)
    4. Normalized gap to leader [-1.0, 1.0] (clipped at +/- 60.0s)
    5. Normalized gap to car ahead [0.0, 1.0] (clipped at 10.0s, 0.0 if leader)
    6. Current race position / rank [1 to 22] normalized [0.0, 1.0]
    7. Laps remaining fraction [0.0, 1.0]

    Action Space:
    - MultiDiscrete([2, 3]): [Pit? (0: No, 1: Yes), New Tire Compound (0: Soft, 1: Medium, 2: Hard)]
    """

    def __init__(self, total_laps: int = 50, initial_fuel: float = 110.0):
        super().__init__()

        self.total_laps = total_laps
        self.initial_fuel = initial_fuel
        self.action_space = spaces.MultiDiscrete([2, 3])

        # 8-dimensional continuous normalized observation space
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        self.sim = None
        self.agent_name = "RL_Agent"
        self.current_compound = "Soft"

    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)
        self.sim = race_engine.RaceSimulator()
        if seed is not None:
            self.sim.set_seed(seed)

        self.current_compound = "Soft"
        self.sim.add_car(self.agent_name, lambda s, g: race_engine.Action(False, "Soft"), self.initial_fuel)
        # Add diverse field
        self.sim.add_car("Bot_Conservative", lambda s, g: race_engine.Action(s.tire_age > 24, "Hard"), self.initial_fuel)
        self.sim.add_car("Bot_Aggressive", lambda s, g: race_engine.Action(s.tire_age > 15, "Medium"), self.initial_fuel)

        return self._get_obs(), {}

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        pit = bool(action[0])
        new_tire_str = TIRE_COMPOUND_MAP[int(action[1])]

        pre_pit_tire_age = 0.0
        if self.sim.race_history:
            pre_pit_tire_age = self.sim.race_history[-1].car_tire_ages[self.agent_name]

        if pit:
            self.current_compound = new_tire_str

        cpp_action = race_engine.Action(pit, new_tire_str)
        self.sim.simulate_one_lap({self.agent_name: cpp_action})

        hist = self.sim.race_history[-1]

        # Compute lap delta
        if len(self.sim.race_history) > 1:
            prev_time = self.sim.race_history[-2].car_times[self.agent_name]
        else:
            prev_time = 0.0

        lap_time = hist.car_times[self.agent_name] - prev_time

        # Objective: minimize race time. Standard benchmark baseline lap is 90.0s.
        reward = 90.0 - lap_time

        # Strategic reward alignment:
        if pit:
            # Reward pitting when tires have genuinely degraded
            if pre_pit_tire_age > 15:
                reward += 80.0
            else:
                reward -= 60.0  # Excessive/wasteful pit stop penalty

        # Severe cliff penalty if tires run into dangerous degradation
        current_tire_age = hist.car_tire_ages[self.agent_name]
        if current_tire_age > 28:
            reward -= 100.0

        done = hist.lap >= self.total_laps
        obs = self._get_obs()

        return obs, reward, done, False, {"lap_time": lap_time, "lap": hist.lap}

    def _get_obs(self) -> np.ndarray:
        if not self.sim.race_history:
            return np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)

        hist = self.sim.race_history[-1]
        lap_norm = min(float(hist.lap) / float(self.total_laps), 1.0)
        tire_age_norm = min(float(hist.car_tire_ages[self.agent_name]) / 50.0, 1.0)
        compound_val = float(REVERSE_TIRE_MAP.get(self.current_compound, 0))

        remaining_fuel = max(self.initial_fuel - float(hist.lap) * 2.2, 0.0)
        fuel_norm = remaining_fuel / self.initial_fuel

        # Inter-car gaps
        agent_time = hist.car_times[self.agent_name]
        leader_time = hist.car_times[hist.leader_name]
        gap_to_leader = agent_time - leader_time
        gap_leader_norm = float(np.clip(gap_to_leader / 60.0, -1.0, 1.0))

        # Position and gap ahead
        sorted_times = sorted(hist.car_times.items(), key=lambda item: item[1])
        rank = 1
        gap_ahead = 0.0
        for i, (name, time_val) in enumerate(sorted_times):
            if name == self.agent_name:
                rank = i + 1
                if i > 0:
                    gap_ahead = time_val - sorted_times[i - 1][1]
                break

        gap_ahead_norm = float(np.clip(gap_ahead / 10.0, 0.0, 1.0))
        rank_norm = float(rank - 1) / float(max(len(sorted_times) - 1, 1))
        laps_remaining_norm = max(1.0 - lap_norm, 0.0)

        return np.array(
            [
                lap_norm,
                tire_age_norm,
                compound_val,
                fuel_norm,
                gap_leader_norm,
                gap_ahead_norm,
                rank_norm,
                laps_remaining_norm,
            ],
            dtype=np.float32,
        )
