from race._bootstrap import ensure_project_paths

ensure_project_paths()

from stable_baselines3 import PPO

from race.env import RaceEnv


def main():
    model = PPO.load("f1_rl_strategist_pro", device="cpu")
    env = RaceEnv()
    obs, info = env.reset()
    done = False

    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)

    env.sim.print_results()


if __name__ == "__main__":
    main()
