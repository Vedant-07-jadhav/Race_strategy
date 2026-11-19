import gymnasium as gym
from gymnasium import spaces
import numpy as np
import race_engine

class RaceEnv(gym.Env):
    def __init__(self):
        super(RaceEnv, self).__init__()
        
        # 1. Action Space: [Pit? (0=No, 1=Yes), Tire Type (0=Soft, 1=Medium, 2=Hard)]
        self.action_space = spaces.MultiDiscrete([2, 3])
        
        # 2. Observation Space: [Lap, Tire Age, Fuel, Gap Front, Gap Rear]
        # We use box for continuous values (normalized between 0 and 1 is best for RL)
        self.observation_space = spaces.Box(
            low=np.array([1, 0, 0, -5, -5]), 
            high=np.array([50, 60, 110, 300, 300]), 
            dtype=np.float32
        )

        self.sim = None
        self.total_laps = 50

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Initialize a fresh simulator
        self.sim = race_engine.RaceSimulator()
        
        # Add your agent and some "bot" opponents to provide traffic
        # In a real setup, you'd manage the agent's car state manually
        self.sim.add_car("RL_Agent", self._dummy_strat, 110.0) 
        self.sim.add_car("Bot_1", self._dummy_strat, 110.0)
        
        # Return initial observation
        initial_obs = np.array([1, 0, 110, 0, 0], dtype=np.float32)
        return initial_obs, {}

    def step(self, action):
        # 1. Map RL action to C++ Action
        # action[0] is pit (0 or 1), action[1] is tire index
        tire_map = {0: "Soft", 1: "Medium", 2: "Hard"}
        cpp_action = race_engine.Action(bool(action[0]), tire_map[action[1]])

        # 2. Run ONE lap in the engine 
        # (You may need to add a 'simulate_one_lap' method to your C++ simulator)
        # For now, we assume it updates the state
        # result = self.sim.simulate_one_lap(cpp_action) 

        # 3. Calculate Reward
        # Reward = -LapTime (faster is better) + Overtake Bonus
        reward = -90.0 # Placeholder: Use actual lap time from result
        
        # 4. Check if finished
        done = self.current_lap >= self.total_laps
        
        # 5. Get next observation
        obs = self._get_obs()
        
        return obs, reward, done, False, {}

    def _get_obs(self):
        # Extract the latest data from sim.race_history
        return np.array([1, 0, 110, 0, 0], dtype=np.float32)

    def _dummy_strat(self, state, gap):
        # This is just a placeholder because C++ add_car expects a function
        return race_engine.Action(False, "Soft")