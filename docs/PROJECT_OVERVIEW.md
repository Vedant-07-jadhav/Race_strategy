# F1 Race Strategy Engine — Project Overview

## 1. Objectives & Executive Summary
The **F1 Multi-Agent AI Strategy Engine** simulates Formula 1 race strategies using a high-performance C++17 simulation kernel bridged to Python via PyBind11. It evaluates deterministic dynamic programming (DP) baselines, heuristic strategies, and reinforcement learning (PPO) policies under realistic racing dynamics including tire degradation, fuel burn, DRS, dirty air aerodynamic penalties, Safety Car & VSC deployments, and multi-car grid interactions.

## 2. Technology Stack
- **Core Engine & Physics:** C++17 (`std::vector`, `std::map`, `std::default_random_engine`)
- **Language Bridge:** PyBind11 (exposing C++ state structures, simulators, optimal DP solver, and Safety Car controls)
- **Reinforcement Learning:** Gymnasium (`gym.Env`), Stable-Baselines3 (`PPO`), PyTorch
- **Data & Evaluation:** NumPy, Matplotlib, Tqdm
- **Experiment Tracking:** Custom isolated tracking system (`race/tracking/`) with metadata, CSV telemetry, and automated Markdown reports under `outputs/experiments/`
- **Build System:** CMake (targeting C++17, Python Development Module, PyBind11) & Clang (macOS Darwin arm64)

## 3. High-Level Architecture

```mermaid
flowchart TB
    subgraph C++17 Modular Backend
        RE[backend/engine/\nRaceEngine: Tire & Fuel Physics\n5D DP Optimizer]
        RS[backend/simulator/\nRaceSimulator: Sector Physics\nSafety Car / VSC\nDirty Air & DRS]
    end

    subgraph PyBind11 Interface
        PB[backend/bindings/\nrace_engine module\nZero-copy STL bindings]
    end

    subgraph Python Strategy & Tracking Layer
        ENVS[race/envs/\nRaceEnv (v1 baseline)\nRaceEnvV2 (8-dim enriched)]
        TRAIN[race/training/\n train.py & train_v2.py]
        EVAL[race/evaluation/\n evaluate.py (22-car grid)\n play.py (rollout)]
        BENCH[race/benchmarks/\n benchmark_suite.py]
        TRACK[race/tracking/\n ExperimentTracker\n outputs/experiments/]
        VIS[race/visualization/\n timing_tower.py\n plots.py]
    end

    RE --> RS
    RS --> PB
    PB --> ENVS
    ENVS --> TRAIN
    TRAIN --> TRACK
    EVAL --> VIS
    EVAL --> TRACK
    BENCH --> TRACK
```

## 4. Directory Structure
```text
Race_strategy/
├── CMakeLists.txt
├── requirements.txt
├── README.md
├── backend/
│   ├── engine/          # Physics formulas, fuel, tire degradation, 5D DP optimizer
│   ├── simulator/       # Sector simulator, drafting, dirty air, Safety Car, race state
│   └── bindings/        # PyBind11 module declarations
├── race/
│   ├── envs/            # Gymnasium environments v1 and v2
│   ├── training/        # PPO training pipelines v1 and v2
│   ├── evaluation/      # 22-car grid evaluation and single-agent play
│   ├── benchmarks/      # Clean-air Monte Carlo benchmark suite
│   ├── visualization/   # Live F1 timing tower and plotting functions
│   └── tracking/        # Centralized experiment tracker and telemetry logger
├── legacy/              # Preserved exploratory scripts and C++ prototypes
├── tests/               # 21 automated unit tests (C++, Gym, SC, Tracking, Visualization)
├── outputs/             # Centralized experiment runs, metrics, plots, and checkpoints
├── models/              # Preserved and versioned model checkpoints
└── docs/                # Permanent project memory and architecture documentation
```

## 5. How to Build & Run on macOS
### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Compile Native C++ Extension
```bash
# Via direct clang++:
clang++ -O3 -Wall -shared -std=c++17 -undefined dynamic_lookup -fPIC \
  -I$(python3 -c "import pybind11; print(pybind11.get_include())") \
  -I$(python3 -c "import sysconfig; print(sysconfig.get_paths()['include'])") \
  -Ibackend/engine -Ibackend/simulator -Ibackend/bindings \
  backend/bindings/bindings.cpp backend/engine/engine.cpp backend/simulator/simulator.cpp \
  -o build/race_engine$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
```

### Running Tests, Simulations & Benchmarks
```bash
# Run all 21 automated unit tests:
PYTHONPATH=. pytest tests/ -v

# Run controlled clean-air strategy benchmark:
PYTHONPATH=. python3 race/benchmarks/benchmark_suite.py

# Run 22-car multi-agent race with Timing Tower:
PYTHONPATH=. python3 race/evaluation/evaluate.py --laps 50 --interval 10 --sc-lap 20

# Run PPO v2 training experiment:
PYTHONPATH=. python3 race/training/train_v2.py --timesteps 2500 --seed 42
```
