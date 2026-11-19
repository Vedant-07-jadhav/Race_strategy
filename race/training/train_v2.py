"""PPO Training and Evaluation Pipeline for RaceEnvV2 with Centralized Experiment Tracking."""

import argparse
from pathlib import Path
from typing import Optional
import numpy as np
from race._bootstrap import ensure_project_paths

ensure_project_paths()
from race.envs.env_v2 import RaceEnvV2
from race.tracking.experiment_tracker import ExperimentTracker
from race.visualization.plots import plot_race_gaps, plot_tire_stints


def train(
    total_timesteps: int = 2500,
    save_name: str = "f1_rl_strategist_v2",
    seed: int = 42,
    tracker: Optional[ExperimentTracker] = None,
):
    try:
        from stable_baselines3 import PPO
    except ImportError:
        print("[WARN] stable-baselines3 is not installed in the current environment.")
        return None

    if tracker is None:
        config = {
            "algorithm": "PPO",
            "policy": "MlpPolicy",
            "total_timesteps": total_timesteps,
            "gamma": 0.995,
            "ent_coef": 0.01,
            "learning_rate": 3e-4,
            "seed": seed,
            "env": "RaceEnvV2",
            "obs_dim": 8,
            "action_space": "MultiDiscrete([2, 3])",
        }
        tracker = ExperimentTracker("ppo_v2_training", config=config)

    env = RaceEnvV2()
    print(f"\n{'='*70}")
    print(f"--- STARTING PPO v2 TRAINING RUN ({total_timesteps} TIMESTEPS, SEED {seed}) ---")
    print(f"Run directory: {tracker.run_dir}")
    print(f"{'='*70}\n")

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        device="cpu",
        gamma=0.995,
        ent_coef=0.01,
        learning_rate=3e-4,
        seed=seed,
    )

    model.learn(total_timesteps=total_timesteps)

    # 1. Save checkpoint inside isolated experiment directory
    exp_checkpoint = tracker.save_checkpoint_path(save_name)
    model.save(str(exp_checkpoint))

    # 2. Save in permanent models/checkpoints directory (does not overwrite legacy v1)
    models_dir = Path(__file__).resolve().parents[2] / "models" / "checkpoints"
    models_dir.mkdir(parents=True, exist_ok=True)
    shared_checkpoint = models_dir / save_name
    model.save(str(shared_checkpoint))
    print(f"\n[OK] Model saved to experiment checkpoint: {exp_checkpoint}.zip")
    print(f"[OK] Model saved to shared checkpoint: {shared_checkpoint}.zip\n")

    # 3. Post-training Evaluation Rollout
    eval_env = RaceEnvV2()
    obs, info = eval_env.reset(seed=seed)
    done = False
    total_reward = 0.0
    pit_laps = []

    while not done:
        action, _ = model.predict(obs, deterministic=True)
        if bool(action[0]):
            pit_laps.append(int(obs[0] * 50.0))
        obs, reward, done, truncated, info = eval_env.step(action)
        total_reward += reward

    eval_hist = eval_env.sim.race_history
    final_time = eval_hist[-1].car_times["RL_Agent"]
    tracker.log_metric("total_timesteps", total_timesteps)
    tracker.log_metric("eval_total_reward", float(total_reward))
    tracker.log_metric("eval_race_time", float(final_time))
    tracker.log_metric("eval_pit_stops", len(pit_laps))

    # Log granular telemetry for evaluation race
    for record in eval_hist:
        for car_name, c_time in record.car_times.items():
            tracker.log_simulation_lap(
                {
                    "lap": record.lap,
                    "car": car_name,
                    "time": c_time,
                    "tire_age": record.car_tire_ages.get(car_name, 0.0),
                    "safety_car": record.safety_car_status,
                }
            )

    # 4. Generate evaluation plots
    fig_gaps = plot_race_gaps(eval_hist, title=f"PPO v2 Evaluation: Race Gaps (Total Time: {final_time:.2f}s)")
    tracker.save_plot(fig_gaps, "eval_race_gaps.png")

    fig_tires = plot_tire_stints(eval_hist, title=f"PPO v2 Evaluation: Tire Life (Pits: {len(pit_laps)})")
    tracker.save_plot(fig_tires, "eval_tire_stints.png")

    tracker.finish(
        status="Passed",
        summary_notes=(
            f"Trained PPO v2 for {total_timesteps} steps. "
            f"Evaluation race completed in {final_time:.2f}s with {len(pit_laps)} pit stop(s) "
            f"and cumulative reward of {total_reward:.2f}."
        ),
    )

    return model, tracker


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and Evaluate PPO Strategist v2")
    parser.add_argument("--timesteps", type=int, default=2000, help="Total training timesteps")
    parser.add_argument("--name", type=str, default="f1_rl_strategist_v2", help="Model name")
    parser.add_argument("--seed", type=int, default=42, help="PRNG Seed")
    args = parser.parse_args()

    train(total_timesteps=args.timesteps, save_name=args.name, seed=args.seed)
