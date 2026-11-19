# Scientific Results Overview

This document summarizes validated research results across different development phases of the `Race_strategy` engine.

---

## 1. Verified Current Benchmark Results (Post-Bugfix v0.2.0)

### Clean-Air Single-Car 50-Lap Monte Carlo Benchmark
- **Track Physics:** Base lap time $90.0\text{ s}$, fuel load $110.0\text{ kg}$, $2.2\text{ kg/lap}$ consumption, $0.035\text{ s/kg}$ penalty.
- **Noise Model:** Gaussian $\mathcal{N}(0, 0.2\text{ s})$.
- **Sample Size:** $N = 30$ trials with synchronized PRNG seeds.

| Strategy Algorithm | Mean Race Time | Std Dev | Min Race Time | Delta to DP | Strategy Characteristics |
|---|---|---|---|---|---|
| **DP Optimal (2-Compound)** | **$4729.59\text{ s}$** | $1.59\text{ s}$ | **$4726.55\text{ s}$** | **$0.00\text{ s}$** | Starts Soft, pits for Medium, meets Rule 30.5 |
| **Aggressive Soft (Multi-Stop)** | $4746.50\text{ s}$ | $1.59\text{ s}$ | $4743.45\text{ s}$ | $+16.91\text{ s}$ | Pits Soft whenever tire age $>14$ |
| **Conservative Hard (1-Stop)** | $4766.55\text{ s}$ | $1.59\text{ s}$ | $4763.51\text{ s}$ | $+36.96\text{ s}$ | Pits Hard whenever tire age $>25$ |

**Scientific Takeaway:** The DP strategy achieves global single-car optimality. Aggressive multi-stop strategy is $16.9\text{ s}$ slower due to excessive pit loss ($22.0\text{ s}$ per stop). Conservative 1-stop strategy is $36.9\text{ s}$ slower due to the severe base pace deficit of Hard tires ($+1.8\text{ s}$ base offset).

---

## 2. Historical Baseline Results (Pre-Bugfix v0.1.0)
*Archived under `plots/legacy/` for historical reference.*

> [!NOTE]
> In pre-bugfix evaluations, the DP cost function included a redundant quadratic degradation penalty (`0.6 * tire_risk * 0.02 * pow(age, 2)`), causing DP to pit earlier than physically necessary. Additionally, the RL agent reward evaluated post-reset tire age, artificially penalizing pit decisions. Historical plots in `plots/legacy/` reflect these initial conditions.

---

## 3. Unverified / In-Progress Results
- **Multi-Agent 22-Car PPO v2 Performance:** Currently undergoing training and validation on `RaceEnvV2`.
- **Safety Car Opportunistic Pit Scenarios:** In implementation phase.
