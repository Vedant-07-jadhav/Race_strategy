import numpy as np
import pytest
from race._bootstrap import ensure_project_paths

ensure_project_paths()
from race.env_v2 import RaceEnvV2


def test_env_v2_dimensions_and_reset():
    env = RaceEnvV2()
    obs, info = env.reset(seed=123)
    assert obs.shape == (8,)
    # Check that all normalized observations are within bounds
    assert np.all(obs >= env.observation_space.low)
    assert np.all(obs <= env.observation_space.high)


def test_env_v2_step_advancement_and_features():
    env = RaceEnvV2()
    env.reset(seed=42)

    # Step: stay out, keep soft
    obs, reward, done, truncated, info = env.step([0, 0])
    assert obs.shape == (8,)
    # Lap fraction > 0
    assert obs[0] > 0.0
    # Tire age fraction > 0
    assert obs[1] > 0.0
    # Compound is 0 (Soft)
    assert obs[2] == 0.0
    # Fuel < 1.0
    assert obs[3] < 1.0


def test_env_v2_pit_compound_update():
    env = RaceEnvV2()
    env.reset(seed=42)

    # Drive 5 laps on Soft
    for _ in range(5):
        obs, _, _, _, _ = env.step([0, 0])

    # Pit on lap 6 for Medium (compound index 1)
    obs, reward, done, _, info = env.step([1, 1])

    # Compound feature in obs must reflect Medium (1.0)
    assert obs[2] == 1.0
    # Post-pit tire age should be freshly reset (~1 sector aged)
    assert obs[1] < 0.1
