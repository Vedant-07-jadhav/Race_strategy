# AI Agent Handoff Guide

## Project Summary
The **F1 Multi-Agent AI Strategy Engine** simulates Formula 1 race strategies using a high-performance C++17 simulation kernel bridged to Python via PyBind11. It evaluates deterministic dynamic programming (DP) baselines, heuristic strategies, and reinforcement learning (PPO) policies, complemented by an interactive Streamlit & Plotly Strategy Lab.

- **Current Active Branch:** `dev-improvements`
- **Current Status:** 25/25 automated unit tests passing cleanly (0 warnings) in ~1s.
- **Interactive Lab:** Active in `dashboard/app.py` with 6 interactive pages.
- **Project Structure:** Fully reorganized and modularized (no nested `backend/src/cpp/`).
- **Experiment Tracking:** Active in `race/tracking/experiment_tracker.py` with runs logging to `outputs/experiments/`.
- **Safety Car / VSC:** Fully implemented in C++ and Python with pace deltas, cheap pit stops, and pack compression.
- **Timing Tower:** Live terminal timing tower rendering in `race/visualization/timing_tower.py` and interactive broadcast UI in `dashboard/components/tower_ui.py`.

## Directory Map
- `backend/engine/`: `engine.hpp`, `engine.cpp` (Physics & 5D DP)
- `backend/simulator/`: `simulator.hpp`, `simulator.cpp` (Multi-car sector simulator, drafting, SC/VSC)
- `backend/bindings/`: `bindings.cpp` (PyBind11 module)
- `dashboard/`:
  - `app.py`: Streamlit multi-page interactive application
  - `adapter.py`: Data adapter for C++ simulation histories and experiment folders
  - `charts.py`: Plotly visualization builders (gaps, positions, stints, tire wear)
  - `components/tower_ui.py`: Broadcast timing tower and status banner
- `race/envs/`: `env.py` (v1), `env_v2.py` (v2 8-dim enriched)
- `race/training/`: `train.py`, `train_v2.py` (with automated experiment tracking)
- `race/evaluation/`: `evaluate.py` (22-car simulation with Timing Tower), `play.py`
- `race/benchmarks/`: `benchmark_suite.py` (Monte Carlo clean-air benchmark)
- `race/visualization/`: `timing_tower.py`, `plots.py`
- `race/tracking/`: `experiment_tracker.py`
- `legacy/`: Preserved legacy exploratory scripts and C++ prototypes
- `outputs/experiments/`: Isolated run folders (`config.json`, `metadata.json`, `metrics.json`, `summary.md`, `execution.log`, `results.csv`, `plots/`, `checkpoints/`)
- `tests/`: 25 automated unit tests across 9 test files
- `docs/`: `PROJECT_OVERVIEW.md`, `DEVELOPMENT_PROGRESS.md`, `CHANGELOG.md`, `ROADMAP.md`, `AI_HANDOFF.md`, `STRUCTURE_MIGRATION.md`, `EXPERIMENT_JOURNAL.md`, `RESULTS_OVERVIEW.md`

## Validated Baseline Numbers
- **DP Optimal (2-Compound, 50 laps, 110kg fuel):** Mean **$4729.59\text{ s}$** ($\pm 1.59\text{ s}$) — Fastest.
- **Aggressive Soft (Multi-Stop):** Mean **$4746.50\text{ s}$** ($\pm 1.59\text{ s}$) — $+16.91\text{ s}$ slower.
- **Conservative Hard (1-Stop):** Mean **$4766.55\text{ s}$** ($\pm 1.59\text{ s}$) — $+36.96\text{ s}$ slower.

## How to Verify Current State
```bash
# 1. Run all 25 unit tests
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v

# 2. Launch the interactive F1 Strategy Lab
source .venv/bin/activate
PYTHONPATH=. streamlit run dashboard/app.py
```
All 25 tests must pass.

## Next Actionable Tasks
1. Train `f1_rl_strategist_v2` for a longer training horizon (e.g. 50k - 100k timesteps) to improve convergence towards DP optimal.
2. Implement stochastic incident triggers during races (probability of SC deployment depending on dirty-air density and car proximity).
3. Implement dynamic track weather transitions (`Dry` -> `Damp` -> `Wet`).
