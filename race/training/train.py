from race._bootstrap import ensure_project_paths

ensure_project_paths()

from stable_baselines3 import PPO
from race.envs.env import RaceEnv


def main():
    env = RaceEnv()

    print("--- TRAINING THE RL AGENT ON CPU ---")
    model = PPO("MlpPolicy", env, verbose=1, device="cpu", gamma=0.999, ent_coef=0.02)
    model.learn(total_timesteps=100000)
    model.save("f1_rl_strategist_pro")
    print("Model Optimized & Saved Successfully.\n")


if __name__ == "__main__":
    main()
