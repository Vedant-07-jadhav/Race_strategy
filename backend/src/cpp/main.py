import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import PPO

import RL

if __name__ == "__main__":
  env = RL.RaceEnv()
  
  model = PPO.load("f1_rl_strategist")
  obs, info = env.reset()
  done = False
  
  while not done:
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, info = env.step(action)
    
  env.sim.print_results()