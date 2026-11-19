import gymnasium as gym
from gymnasium import spaces
import numpy as np
import race_engine
from stable_baselines3 import PPO

class RaceEnv(gym.Env):
    def __init__(self):
        super(RaceEnv, self).__init__()
        # Action: [0=Stay, 1=Pit], [0=Soft, 1=Medium, 2=Hard]
        self.action_space = spaces.MultiDiscrete([2, 3])
        
        # Observation Space Array Layout: [Lap, Tire Age, Gap to Leader]
        self.observation_space = spaces.Box(
            low=np.array([0, 0.0, -500.0]), 
            high=np.array([55, 60.0, 500.0]), 
            dtype=np.float32
        )
        self.sim = None
        self.agent_name = "RL_Agent"

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.sim = race_engine.RaceSimulator()
        
        # Core Stagger Grid Initialization
        self.sim.add_car(self.agent_name, lambda s, g: race_engine.Action(False, "Soft"), 110.0)
        self.sim.add_car("Bot_Conservative", lambda s, g: race_engine.Action(s.tire_age > 22, "Medium"), 110.0)
        
        return self._get_obs(), {}

    def step(self, action):
        tires = {0: "Soft", 1: "Medium", 2: "Hard"}
        cpp_action = race_engine.Action(bool(action[0]), tires[action[1]])
        
        # Execute sector physics loops in C++ backend
        self.sim.simulate_one_lap(self.agent_name, cpp_action)
        
        obs = self._get_obs()
        hist = self.sim.race_history[-1]
        
        if len(self.sim.race_history) > 1:
            prev_time = self.sim.race_history[-2].car_times[self.agent_name]
        else:
            prev_time = 0.0
            
        lap_time = hist.car_times[self.agent_name] - prev_time
        
        reward = 90.0 -lap_time
        
        tire_age = hist.car_tire_ages[self.agent_name]
        
        if bool(action[0]) == True:
            if(tire_age>15):
                reward +=100.0
            else:
                reward-=50.0 
        if(tire_age>25):
            reward-=150.0
        
        
        if hist.leader_name == self.agent_name:
            reward += 10.0  # Increased reward incentive for taking/holding the lead
        
        done = hist.lap >= 50
        return obs, reward, done, False, {}

    def _get_obs(self):
        if not self.sim.race_history:
            return np.array([1.0, 0.0, 0.0], dtype=np.float32)
            
        hist = self.sim.race_history[-1]
        lap = float(hist.lap)
        tire_age = float(hist.car_tire_ages[self.agent_name])
        
        gap = float(hist.car_times[self.agent_name] - hist.car_times[hist.leader_name])
        
        return np.array([lap, tire_age, gap], dtype=np.float32)

if __name__ == "__main__":
    env = RaceEnv()
    
    print("--- TRAINING THE RL AGENT ON CPU ---")
    model = PPO("MlpPolicy", env, verbose=1, device="cpu", gamma=0.999, ent_coef=0.02)
    
    model.learn(total_timesteps=100000) 
    model.save("f1_rl_strategist_pro")
    print("Model Optimized & Saved Successfully.\n")