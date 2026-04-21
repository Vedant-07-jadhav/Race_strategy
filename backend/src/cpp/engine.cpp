#include "engine.hpp"
#include <algorithm>
#include <cmath>

RaceEngine::RaceEngine() : generator(std::random_device{}()) {
    size_t total_elements = MAX_LAPS * MAX_TIRES * MAX_AGE * MAX_MASKS * MAX_PITS_DIM;
    dp = std::make_unique<DPState[]>(total_elements);
}

int RaceEngine::get_idx(int lap, int tire, int age, int mask, int pits) const {
    return (((lap * MAX_TIRES + tire) * MAX_AGE + age) * MAX_MASKS + mask) * MAX_PITS_DIM + pits;
}

Tire RaceEngine::get_tire(const std::string &type) {
    if (type == "Soft") return soft;
    if (type == "Medium") return medium;
    if (type == "Hard") return hard;
    return soft;
}

double RaceEngine::compute_lap_time(const State &s) {
    double deg_effect = s.tire.deg_rate * std::pow(s.tire_age, s.tire.deg_power);
    double fuel_effect = s.fuel * FUEL_PENALTY_PER_KG;
    return BASE_LAP_TIME + s.tire.base_offset + deg_effect + fuel_effect + noise_dist(generator);
}

double RaceEngine::compute_lap_time_deterministic(const std::string &type, int age, double fuel) {
    Tire t = get_tire(type);
    return BASE_LAP_TIME + t.base_offset + (t.deg_rate * std::pow(age, t.deg_power)) + (fuel * FUEL_PENALTY_PER_KG);
}

State RaceEngine::step(State s, const Action &a, double lap_time, double wear_factor) {
    if (a.pit) {
        s.total_time += PIT_STOP_LOSS;
        s.tire = get_tire(a.new_tire);
        s.tire_age = 0.0;
    }
    s.total_time += lap_time;
    s.lap++;
    s.tire_age += (1.0 * wear_factor); 
    s.fuel -= 2.2;
    return s;
}

std::pair<State, std::vector<LapData>> RaceEngine::simulate(int total_laps, double fuel_load, StrategyFn strategy_fn) {
  history.clear();
  State s{1, soft, 0, fuel_load, 0.0};
  while (s.lap <= total_laps) {
    Action a = strategy_fn(s);
    double lap_time = compute_lap_time(s);
    history.push_back({s.lap, lap_time, s.tire_age, s.tire.name, s.fuel});
    
    // FIX: Change 0 to 1.0 so tires actually age!
    s = step(s, a, lap_time, 1.0); 
  }
  return {s, history};
}

std::vector<Action> RaceEngine::get_optimal_DP_strategy(int total_laps,
                                                        double initial_fuel) {
  std::string tire_names[] = {"Soft", "Medium", "Hard"};
  const int PIT_LIMIT = 3;

  // Reset the flattened DP table
  size_t total_elements =
      MAX_LAPS * MAX_TIRES * MAX_AGE * MAX_MASKS * MAX_PITS_DIM;
  for (size_t i = 0; i < total_elements; ++i) {
    dp[i] = DPState();
  }

  // Base Case: Lap 1
  for (int t = 0; t < 3; ++t) {
    int initial_mask = (1 << t);
    int idx = get_idx(1, t, 0, initial_mask, 0);
    dp[idx].time = 0;
    dp[idx].tire_chosen = tire_names[t];
  }

  // Forward Pass
  for (int lap = 1; lap <= total_laps; ++lap) {
    double current_fuel = initial_fuel - (lap - 1) * 2.2;
    for (int t = 0; t < 3; ++t) {
      for (int age = 0; age < lap; ++age) {
        for (int mask = 1; mask < 8; ++mask) {
          for (int pits = 0; pits <= PIT_LIMIT; ++pits) {

            int curr_idx = get_idx(lap, t, age, mask, pits);
            DPState &curr = dp[curr_idx];
            if (curr.time > 1e17)
              continue;

            double base = compute_lap_time_deterministic(tire_names[t], age,
                                                         current_fuel);
            double tire_risk = (t == 0 ? 1.5 : (t == 1 ? 1.0 : 0.7));
            double t_lap = base + (0.6 * tire_risk * 0.02 * std::pow(age, 2));

            // OPTION 1: STAY OUT
            int next_idx_stay = get_idx(lap + 1, t, age + 1, mask, pits);
            if (curr.time + t_lap < dp[next_idx_stay].time) {
              dp[next_idx_stay] = {curr.time + t_lap, t, age, mask, pits, false,
                                   tire_names[t]};
            }

            // OPTION 2: PIT (Rule 2: Limit stops)
            if (pits < PIT_LIMIT) {
              for (int next_t = 0; next_t < 3; ++next_t) {
                int next_mask = mask | (1 << next_t);
                int next_idx_pit =
                    get_idx(lap + 1, next_t, 0, next_mask, pits + 1);
                double p_time = curr.time + t_lap + PIT_STOP_LOSS;
                if (p_time < dp[next_idx_pit].time) {
                  dp[next_idx_pit] = {
                      p_time, t, age, mask, pits, true, tire_names[next_t]};
                }
              }
            }
          }
        }
      }
    }
  }

  // Backtrack with Rule 1: Two compound rule
  double min_total = 1e18;
  int b_t = -1, b_a = -1, b_m = -1, b_p = -1;

  for (int t = 0; t < 3; ++t) {
    for (int a = 0; a <= total_laps; ++a) {
      for (int m = 1; m < 8; ++m) {
        int compounds = 0;
        for (int i = 0; i < 3; i++)
          if (m & (1 << i))
            compounds++;
        if (compounds < 2)
          continue; // Skip if only 1 tire type used

        for (int p = 0; p <= PIT_LIMIT; ++p) {
          int final_idx = get_idx(total_laps + 1, t, a, m, p);
          if (dp[final_idx].time < min_total) {
            min_total = dp[final_idx].time;
            b_t = t;
            b_a = a;
            b_m = m;
            b_p = p;
          }
        }
      }
    }
  }

  std::vector<Action> optimal_actions;
  int c_t = b_t, c_a = b_a, c_m = b_m, c_p = b_p;

  for (int lap = total_laps + 1; lap > 1; --lap) {
    int curr_idx = get_idx(lap, c_t, c_a, c_m, c_p);
    DPState &res = dp[curr_idx];
    optimal_actions.push_back({res.pitted, res.tire_chosen});

    int pt = res.best_prev_tire;
    int pa = res.best_prev_age;
    int pm = res.best_prev_mask;
    int pp = res.best_prev_pits;
    c_t = pt;
    c_a = pa;
    c_m = pm;
    c_p = pp;
  }
  std::reverse(optimal_actions.begin(), optimal_actions.end());
  return optimal_actions;
}