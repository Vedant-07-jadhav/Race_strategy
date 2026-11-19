# Changelog

All notable changes to the `Race_strategy` repository are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

---

## [0.4.0] - 2026-11-19
### Added
- **Interactive F1 Race Strategy Lab (`dashboard/`):**
  - Full-featured Streamlit application (`dashboard/app.py`) with F1 dark theme styling.
  - Multi-page navigation:
    1. **Race Configuration & Execution**: Parameters for laps (10-70), cars (1-22), random seed, starting fuel, Safety Car & VSC schedules, and AI PPO strategist toggling.
    2. **Race Replay & Timing Tower**: Interactive lap-by-lap scrubber, play controls, F1 broadcast status banner (Green, VSC, Full SC), dynamic timing tower with compound badges (`S`, `M`, `H`), interval deltas, and driver telemetry inspector.
    3. **Strategy & Telemetry Analysis**: Interactive Plotly visualizations (`dashboard/charts.py`) for Gap to P1, Position changes, Tire age sawtooth curve, and Stint timeline Gantt bars.
    4. **AI Decision Inspector**: Real-time breakdown of PPO agent's 8-dimensional observation vector, pit action inspection, and compound choice tracing.
    5. **Experiment Explorer**: Historical experiment browser for `outputs/experiments/` with config, hardware metadata, summary markdown, metrics, CSV telemetry, and plot inspection.
    6. **DP & Strategy Benchmarks**: On-demand Monte Carlo clean-air benchmark execution against 5D Dynamic Programming global optimum.
- **Data Adapter & UI Components:**
  - `dashboard/adapter.py`: Translates raw C++ `race_history` records and experiment directories into structured `LapSnapshot` objects and pandas DataFrames.
  - `dashboard/components/tower_ui.py`: F1 broadcast banner and styled timing tower tables.
- **Automated Dashboard Tests (`tests/test_dashboard.py`):**
  - 4 automated unit tests verifying adapter parsing, DataFrame format, chart building, and experiment loading.
  - Full test suite now contains **25 passing tests**.

---

## [0.3.0] - 2026-11-19
### Added
- **Project Structure Reorganization:**
  - Split nested `backend/src/cpp/` into clean components: `backend/engine/`, `backend/simulator/`, and `backend/bindings/`.
  - Structured Python code into modular subpackages: `race/envs/`, `race/training/`, `race/evaluation/`, `race/benchmarks/`, `race/visualization/`, and `race/tracking/`.
  - Safely migrated legacy prototypes into `legacy/backend_scripts/` and `legacy/cpp_demos/`.
  - Created `docs/STRUCTURE_MIGRATION.md` detailing all file relocations and build updates.
- **Centralized Experiment Tracking (`race/tracking/`):**
  - Built `ExperimentTracker` generating reproducible directories under `outputs/experiments/run_YYYYMMDD_HHMMSS_<id>/`.
  - Automatic capture of Git commit, Python version, platform, hardware, hyperparameters, metrics, and CSV telemetry.
  - Automated report generation (`summary.md`) and automatic chronological ledger update in `docs/EXPERIMENT_JOURNAL.md`.
  - Created `docs/RESULTS_OVERVIEW.md` summarizing research baselines.
- **Safety Car & Virtual Safety Car Simulation:**
  - Implemented `SafetyCarType` (`SC_NONE`, `SC_VSC`, `SC_FULL`) in C++ simulator.
  - VSC delta pace ($+35\%$) and Full SC pace ($+50\%$).
  - Cheap pit stop physics ($12.0\text{ s}$ under VSC, $9.0\text{ s}$ under Full SC vs $22.0\text{ s}$ green flag).
  - Field compression and bunching within $0.8\text{ s}$ under Full SC.
  - Exposed schedule and trigger APIs via PyBind11.
- **Live Timing Tower & Visualizations (`race/visualization/`):**
  - Implemented live ASCII F1 timing tower displaying positions, gaps to leader, interval deltas, tire compound badges, tire ages, and pit stop counts.
  - Added reusable plotting tools (`plot_race_gaps`, `plot_tire_stints`, `plot_strategy_benchmark_comparison`).
- **Comprehensive Automated Test Suite (`tests/`):**
  - Expanded test suite to **21 automated unit tests** across engine physics, DP optimizer, Gym envs, seed reproducibility, Safety Car, experiment tracking, and visualization. All 21 tests passing cleanly.

### Fixed
- **Pytest Float Precision Warnings (`race/envs/env.py`):** Explicitly declared `dtype=np.float32` on `spaces.Box` bounds, eliminating all 8 Gymnasium precision lowering warnings.
- **C++ Native Extension Paths (`CMakeLists.txt`):** Updated include paths and source definitions to target `backend/engine/`, `backend/simulator/`, and `backend/bindings/`.

---

## [0.2.0] - 2026-11-19
### Fixed
- **Post-Pit Reward Logic (`race/envs/env.py`):** Fixed bug where `tire_age` was evaluated post-step after being reset to `~0`, causing all pit stops to receive a `-50` penalty. Now caches `pre_pit_tire_age` so pit stops on tires $>15$ laps receive $+100$ bonus.
- **DP Memory Bounds (`backend/engine/engine.hpp`):** Expanded `MAX_LAPS` and `MAX_AGE` from 55 to 75, preventing buffer overflows when DP forward passes scan `total_laps + 1`.
- **DP Degradation Cost Function (`backend/engine/engine.cpp`):** Eliminated the redundant quadratic term that artificially doubled degradation in DP compared to simulator physics.
- **PyBind Call Signatures (`legacy/backend_scripts/evaluate_22_cars.py`):** Fixed legacy calls to pass `dict[str, Action]`.
- **macOS Native Binary Conflicts (`race/_bootstrap.py`):** Prioritized `build/` over source directories. Untracked legacy Linux `.so` from git.
- **Seed Synchronization (`backend/`):** Added `set_seed(unsigned int)` to `RaceEngine` and `RaceSimulator` and exposed via PyBind11.
