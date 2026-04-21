#ifndef ENGINE_HPP
#define ENGINE_HPP

#include <functional>
#include <memory>
#include <random>
#include <string>
#include <vector>

struct Tire {
    std::string name;
    double base_offset;
    double deg_rate;
    double deg_power;
};

struct State {
    int lap;
    Tire tire;
    double tire_age;
    double fuel;
    double total_time;
};

struct Action {
    bool pit;
    std::string new_tire = "Soft";
};

struct LapData {
    int lap;
    double lap_time;
    double  tire_age;
    std::string tire;
    double fuel;
};

struct DPState {
    double time = 1e18;
    int best_prev_tire = -1;
    int best_prev_age = -1;
    int best_prev_mask = 0;
    int best_prev_pits = 0;
    bool pitted = false;
    std::string tire_chosen = "";
};

using StrategyFn = std::function<Action(const State &)>;

class RaceEngine {
private:
    const double FUEL_PENALTY_PER_KG = 0.035;
    const double PIT_STOP_LOSS = 22.0;
    const double BASE_LAP_TIME = 90.0;

    std::default_random_engine generator;
    std::normal_distribution<double> noise_dist{0.0, 0.2}; // Reduced noise for clearer strategy testing

    Tire soft = {"Soft", 0.0, 0.09, 1.4};
    Tire medium = {"Medium", 0.8, 0.04, 1.2};
    Tire hard = {"Hard", 1.8, 0.02, 1.1};

    static const int MAX_LAPS = 55;
    static const int MAX_TIRES = 3;
    static const int MAX_AGE = 55;
    static const int MAX_MASKS = 8;
    static const int MAX_PITS_DIM = 5;

    std::unique_ptr<DPState[]> dp;
    int get_idx(int lap, int tire, int age, int mask, int pits) const;

public:
    std::vector<LapData> history;
    RaceEngine();
    Tire get_tire(const std::string &type);
    double compute_lap_time(const State &s);
    double compute_lap_time_deterministic(const std::string &type, int age, double fuel);
    State step(State s, const Action &a, double lap_time, double wear_factor);
    std::pair<State, std::vector<LapData>> simulate(int total_laps, double fuel_load, StrategyFn strategy_fn);
    std::vector<Action> get_optimal_DP_strategy(int total_laps, double initial_fuel);
};

#endif