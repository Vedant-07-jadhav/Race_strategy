# Project Structure Refactoring & Migration Guide

## 1. Motivation & Goals
The original codebase accumulated legacy exploratory scripts, nested C++ paths (`backend/src/cpp/`), and mixed responsibilities across the root and subdirectories. This refactoring achieves:
1. **Simplified Backend:** Elimination of `backend/src/cpp/` in favor of modular components:
   - `backend/engine/` (Physics formulas, fuel, tire degradation, 5D DP optimizer)
   - `backend/simulator/` (Sector simulator, drafting, dirty air, Safety Car, race state)
   - `backend/bindings/` (PyBind11 module declarations)
2. **Clear Python Module Separation:**
   - `race/envs/` (Gymnasium environments v1 and v2)
   - `race/training/` (PPO training pipelines v1 and v2)
   - `race/evaluation/` (Multi-car and single-car evaluation runners)
   - `race/benchmarks/` (Analytical and Monte Carlo benchmark suite)
   - `race/visualization/` (Live timing tower, telemetry and corridor plots)
   - `race/tracking/` (Centralized experiment tracker, logging, metrics, and report generator)
3. **Dedicated Legacy Archive:** Exploratory scripts (`monteCarlo.py`, `visulaise.py`, etc.) preserved under `legacy/` without polluting runtime `sys.path`.
4. **Structured Experiment Outputs:** Centralized `outputs/experiments/` for reproducible runs, metrics, plots, and checkpoints.

---

## 2. File Relocation Mapping

| Original Path | New Relocated Path | Purpose / Description |
|---|---|---|
| `backend/src/cpp/engine.hpp` | `backend/engine/engine.hpp` | Physics & 5D DP header |
| `backend/src/cpp/engine.cpp` | `backend/engine/engine.cpp` | Physics & 5D DP implementation |
| `backend/src/cpp/simulator.hpp` | `backend/simulator/simulator.hpp` | Sector simulator & SC header |
| `backend/src/cpp/simulator.cpp` | `backend/simulator/simulator.cpp` | Sector simulator & SC implementation |
| `backend/src/cpp/bindings.cpp` | `backend/bindings/bindings.cpp` | PyBind11 bindings |
| `backend/src/cpp/main.cpp` | `legacy/cpp_demos/main.cpp` | C++ standalone test runner |
| `backend/src/cpp/first.cpp` | `legacy/cpp_demos/first.cpp` | Initial prototype |
| `backend/src/cpp/monteCarlo.py` | `legacy/backend_scripts/monteCarlo.py` | Exploratory MC script |
| `backend/src/cpp/visulaise.py` | `legacy/backend_scripts/visulaise.py` | Exploratory plot script |
| `backend/src/cpp/simulattion.py` | `legacy/backend_scripts/simulattion.py` | Early simulator prototype |
| `backend/src/cpp/RaceEnv.py` | `legacy/backend_scripts/RaceEnv.py` | Early un-namespaced gym env |
| `backend/src/cpp/RL.py` | `legacy/backend_scripts/RL.py` | Early un-namespaced training script |
| `backend/src/cpp/evaluate_*.py` | `legacy/backend_scripts/evaluate_*.py` | Early evaluation scripts |
| `race/env.py` | `race/envs/env.py` | Gymnasium environment v1 |
| `race/env_v2.py` | `race/envs/env_v2.py` | Enriched 8-dim Gymnasium environment v2 |
| `race/train.py` | `race/training/train.py` | PPO training entry point v1 |
| `race/train_v2.py` | `race/training/train_v2.py` | PPO training entry point v2 |
| `race/play.py` | `race/evaluation/play.py` | Model rollout runner |
| `experiments/evaluate_all_ai.py` | `race/evaluation/evaluate.py` | 22-car grid evaluation runner |
| `experiments/benchmark_suite.py` | `race/benchmarks/benchmark_suite.py` | Benchmark runner |

---

## 3. Backward Compatibility
- Root wrappers (`RL.py`, `evaluate_all_ai.py`) continue to function by routing to `race.training.train` and `race.evaluation.evaluate`.
- `race/__init__.py` exposes top-level imports:
  ```python
  from race.envs.env import RaceEnv
  from race.envs.env_v2 import RaceEnvV2
  ```
- `_bootstrap.py` dynamically locates `build/` for `.so` files across all working directories.
