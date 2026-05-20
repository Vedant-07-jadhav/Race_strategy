#include "simulator.hpp"
#include <algorithm>
#include <cstddef>
#include <iostream>
#include <vector>

RaceSimulator::RaceSimulator() {
  // Layout optimized for drafting
  track_sectors = {CORNER, STRAIGHT, STRAIGHT};
}

void RaceSimulator::add_car(const std::string &name, StrategyWithGap strategy,
                            double initial_fuel) {
  CarInternal car;
  car.name = name;
  car.strategy = strategy;
  double grid_offset = internal_cars.size() * 0.2;
  // Using double for tire_age to support sector-level precision
  car.state = {1, engine.get_tire("Soft"), 0.0, initial_fuel, grid_offset};
  internal_cars.push_back(car);
}

// Replace your current simulate_one_lap with this:
void RaceSimulator::simulate_one_lap(const std::map<std::string, Action>& agent_actions) {
  if (internal_cars.empty()) return;

  LapRecord record;
  record.lap = internal_cars[0].state.lap;

  for (auto sector : track_sectors) {
    std::sort(internal_cars.begin(), internal_cars.end(),
              [](const CarInternal &a, const CarInternal &b) {
                return a.state.total_time < b.state.total_time;
              });

    std::vector<double> sector_start_times;
    sector_start_times.reserve(internal_cars.size());
    for (auto &c : internal_cars) sector_start_times.push_back(c.state.total_time);

    for (size_t i = 0; i < internal_cars.size(); ++i) {
      auto &car = internal_cars[i];
      double gap = (i == 0) ? -1.0 : sector_start_times[i] - sector_start_times[i - 1];

      Action chosen_action;
      if (sector == track_sectors[0]) {
        // 🔥 NEW: Check if Python passed an AI decision for this specific car!
        if (agent_actions.count(car.name)) {
          chosen_action = agent_actions.at(car.name);
        } else {
          chosen_action = car.strategy(car.state, gap);
        }

        if (chosen_action.pit) {
          car.state.total_time += 22.0; 
          car.state.tire_age = 0.0;
          car.state.tire = engine.get_tire(chosen_action.new_tire);
        }
      }

      double sector_base_time = engine.compute_lap_time(car.state) / (double)track_sectors.size();
      double sector_effect = 0.0;
      double wear_multiplier = 1.0;

      if (gap > 0.0 && gap < 3.0) {
        if (sector == STRAIGHT) {
          sector_effect -= 0.4; 
          car.stats.slipstream_count++;
          if (gap < 1.2) { sector_effect -= 0.7; car.stats.drs_count++; }
        } else if (sector == CORNER && gap < 1.5) {
          double pen = 0.6 * (1.0 - (gap / 1.5)); 
          sector_effect += pen;
          wear_multiplier += (0.25 * (1.0 - (gap / 1.5))); 
          car.stats.dirty_air_count++;
          car.stats.total_time_lost_dirty_air += pen;
        }
      }

      if (sector_effect < 0) car.stats.total_time_gained_drs_slip += (-sector_effect);

      car.state.total_time += (sector_base_time + sector_effect);
      car.state.tire_age += (1.0 / (double)track_sectors.size()) * wear_multiplier;
    }
  }

  record.leader_name = internal_cars[0].name;
  for (auto &c : internal_cars) {
    record.car_times[c.name] = c.state.total_time;
    record.car_tire_ages[c.name] = c.state.tire_age;
    record.car_stats[c.name] = c.stats;
    c.state.lap++;
    c.state.fuel -= 2.2;
  }
  race_history.push_back(record);
}

// And update the dummy call inside simulate_race to pass an empty map:
void RaceSimulator::simulate_race(int total_laps) {
  this->race_history.clear();
  std::map<std::string, Action> empty_actions;
  for (int lap = 1; lap <= total_laps; lap++) {
    simulate_one_lap(empty_actions); 
  }
}



void RaceSimulator::print_results() {
  std::sort(internal_cars.begin(), internal_cars.end(),
            [](const CarInternal &a, const CarInternal &b) {
              return a.state.total_time < b.state.total_time;
            });

  std::cout << "\n--- FINAL STANDINGS & INTERACTION STATS ---\n";
  for (int i = 0; i < (int)internal_cars.size(); ++i) {
    auto &c = internal_cars[i];
    std::cout << i + 1 << ". " << c.name << " | Time: " << c.state.total_time << "s\n"
              << "   DRS(" << c.stats.drs_count << ") SLIP(" << c.stats.slipstream_count 
              << ") DIRTY(" << c.stats.dirty_air_count << ")\n"
              << "-------------------------------------------\n";
  }
}