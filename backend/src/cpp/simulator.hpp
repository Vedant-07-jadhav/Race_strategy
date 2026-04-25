#ifndef SIMULATOR_HPP
#define SIMULATOR_HPP

#include "engine.hpp"
#include <map>
#include <vector>

using StrategyWithGap = std::function<Action(const State &, double)>;

struct InteractionStats {
    int slipstream_count = 0;
    int drs_count = 0;
    int dirty_air_count = 0;
    double total_time_lost_dirty_air = 0.0;
    double total_time_gained_drs_slip = 0.0;
};

struct CarInternal {
    State state;
    std::string name;
    StrategyWithGap strategy;
    InteractionStats stats;
};

struct LapRecord {
    int lap;
    std::string leader_name;
    std::map<std::string, double> car_times;
    std::map<std::string, double> car_tire_ages;
    std::map<std::string, InteractionStats> car_stats;
};

enum SectorType { STRAIGHT, CORNER, MIXED };

class RaceSimulator {
private:
    RaceEngine engine;
    std::vector<CarInternal> internal_cars;
    std::vector<SectorType> track_sectors;

public:
    std::vector<LapRecord> race_history;
    RaceSimulator();
    void add_car(const std::string &name, StrategyWithGap strategy, double initial_fuel);
    void simulate_one_lap(Action &a);
    void simulate_race(int total_laps);
    void print_results();
};

#endif  