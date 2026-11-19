# F1 Strategy Engine — Long-Term Development Roadmap

## Phase 1: Critical Bug Fixes & Reliability
- [x] Fix post-pit reward calculation in `race/envs/env.py`
- [x] Fix DP array bounds memory safety (`MAX_LAPS` + padding expanded to 75)
- [x] Eliminate double-counted quadratic degradation in DP forward pass
- [x] Update PyBind call signatures across legacy evaluation scripts
- [x] Purge tracked Linux `.so` and fix macOS extension module search paths
- [x] Connect Python PRNG seeds to C++ `std::default_random_engine`
- [x] Fix Gymnasium float64 precision casting warnings

## Phase 2: Scientific Accuracy & Benchmark Framework
- [x] Separate clean-air single-car evaluation from multi-car traffic evaluation
- [x] Preserve legacy benchmark plots and outputs under `plots/legacy/`
- [x] Provide analytical ground truth verification for single-stop and two-stop strategy curves
- [x] Multi-trial Monte Carlo evaluation with standard error reporting (`race/benchmarks/benchmark_suite.py`)

## Phase 3: Project Architecture Refactoring
- [x] Simplify backend from `backend/src/cpp/` into `backend/engine/`, `backend/simulator/`, and `backend/bindings/`
- [x] Organize Python code into clear subpackages: `envs/`, `training/`, `evaluation/`, `benchmarks/`, `visualization/`, `tracking/`
- [x] Safely archive exploratory scripts in `legacy/`
- [x] Modernize `CMakeLists.txt` for modular includes and macOS Apple Silicon

## Phase 4: Experiment Tracking & Research Ledger
- [x] Build `ExperimentTracker` creating isolated `outputs/experiments/run_.../` directories
- [x] Automatic logging of telemetry CSV, JSON metrics, configuration, and environment metadata
- [x] Automatic Matplotlib plot export and `summary.md` generation
- [x] Maintain `docs/EXPERIMENT_JOURNAL.md` and `docs/RESULTS_OVERVIEW.md`

## Phase 5: Automated Testing Suite
- [x] Unit tests for C++ tire degradation formulas
- [x] Unit tests for fuel load consumption and mass delta effects
- [x] Unit tests for DP terminal compound selection (Rule 30.5)
- [x] Unit tests for Gymnasium environment step/reset compliance
- [x] Unit tests for multi-car sorting and drafting mechanics
- [x] Unit tests for Safety Car, VSC pace delta, and pack compression
- [x] Unit tests for experiment tracker and telemetry export
- [x] Unit tests for timing tower rendering and plot generation (21/21 passing)

## Phase 6: F1 Simulation Features
- [x] Safety Car (SC) and Virtual Safety Car (VSC) deployment and pace regulation
- [x] Cheap pit stop modeling under SC ($9.0\text{ s}$) and VSC ($12.0\text{ s}$) vs Green Flag ($22.0\text{ s}$)
- [x] Field compression and bunching within $0.8\text{ s}$ behind Full SC
- [ ] Stochastic incident generator based on dirty air and aggression
- [ ] Dynamic weather transitions (Dry -> Damp -> Wet) with Intermediate & Wet compounds
- [ ] Stochastic pit crew turnaround times (variance and cross-threaded wheelnut failure modes)
- [ ] Real-world circuit configurations (Monza, Monaco, Silverstone track profiles)

## Phase 7: Visualization, Interactive Lab & Productionization
- [x] Live F1 timing tower displaying positions, gaps to leader, interval deltas, tire badges, and pit counts
- [x] Reusable Matplotlib plotting utilities for race gaps, tire stints, and strategy distributions
- [x] Interactive Streamlit Strategy Lab (`dashboard/app.py`) with F1 dark theme
- [x] Interactive Plotly race telemetry charts (Gap to P1, Lap positions, Tire age sawtooth, Stint Gantt bars)
- [x] Lap-by-lap race replay with scrubber controls and driver telemetry inspector
- [x] AI Decision Inspector with 8-dimensional observation breakdown and action trace
- [x] Experiment Explorer for browsing `outputs/experiments/` runs, configs, metrics, plots, and CSVs
- [x] Interactive Dynamic Programming clean-air benchmark comparison
- [ ] FastAPI backend for remote simulation and parameter tuning
- [ ] Integration with `fastf1` for historical telemetry ingestion
