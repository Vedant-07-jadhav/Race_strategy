import numpy as np
import pytest
from race._bootstrap import ensure_project_paths

ensure_project_paths()
from race.env import RaceEnv


def test_race_env_initialization_and_reset():
    env = RaceEnv()
    obs, info = env.reset(seed=123)
    assert obs.shape == (3,)
    assert obs[0] == 1.0  # Lap 1
    assert obs[1] == 0.0  # Initial tire age
    assert obs[2] == 0.0  # Leader gap is zero


def test_race_env_step():
    env = RaceEnv()
    env.reset(seed=123)
    # Action: Stay out (0), tire Soft (0)
    obs, reward, done, truncated, info = env.step([0, 0])
    # The recorded lap in history is the completed lap (lap 1)
    assert obs[0] == 1.0
    assert obs[1] > 0.0  # Tire has aged
    assert not done


def test_race_env_pit_reward_logic():
    env = RaceEnv()
    env.reset(seed=999)

    # Drive 16 laps without pitting so tires age > 15
    for _ in range(16):
        obs, r, done, _, _ = env.step([0, 0])

    assert obs[1] > 15.0

    # Pit on lap 17
    obs, pit_reward, done, _, _ = env.step([1, 1])

    # With pre-pit tire age > 15, the agent must be rewarded (+100.0) rather than penalized (-50.0)
    # Typical reward is (90 - lap_time) + 100 bonus, lap_time for in-lap corner + 22s pit is ~115s,
    # so reward is approx (90 - 115) + 100 ~ +75. It must be substantially positive!
    assert pit_reward > 0.0, f"Expected positive pit reward, got {pit_reward}"


def test_race_env_episode_completion():
    env = RaceEnv()
    env.reset(seed=42)
    done = False
    laps_run = 0
    while not done:
        obs, r, done, _, _ = env.step([0, 1])
        laps_run += 1
        if laps_run > 60:
            break

    assert done
    assert laps_run == 50
