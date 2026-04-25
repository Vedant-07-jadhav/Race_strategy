import race_engine
import matplotlib.pyplot as plt 
import numpy as np

import gymnasium as gym
from stable_baselines3 import PPO # A standard RL algorithm
from your_custom_env import RaceEnv # The wrapper you'll build

# 1. Create the environment
env = RaceEnv()

# 2. Initialize the Agent (The "Brain")
model = PPO("MlpPolicy", env, verbose=1)

# 3. TRAIN: This is where it plays thousands of races to learn
model.learn(total_timesteps=10000)

# 4. SAVE: Your AI is now a strategist
model.save("f1_strategist")