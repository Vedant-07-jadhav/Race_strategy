#include "simulator.hpp"
#include <algorithm>
#include <cstddef>
#include <iostream>
#include <vector>

RaceSimulator::RaceSimulator() {
  // Layout optimized for drafting
  track_sectors = {CORNER, STRAIGHT, STRAIGHT};
}

void RaceSimulator::set_seed(unsigned int seed) {
  engine.set_seed(seed);
}

void RaceSimulator::set_safety_car_schedule(const std::map<int, int>& schedule) {
  safety_car_schedule.clear();
  for (const auto& pair : schedule) {
    safety_car_schedule[pair.first] = static_cast<SafetyCarType>(pair.second);
  }
}

void RaceSimulator::trigger_safety_car(int lap, int sc_type) {
  safety_car_schedule[lap] = static_cast<SafetyCarType>(sc_type);
}

void RaceSimulator::clear_safety_car_schedule() {
  safety_car_schedule.clear();
}

int RaceSimulator::get_current_safety_car() const {
  if (internal_cars.empty()) return SC_NONE;
  int current_lap = internal_cars[0].state.lap;
  if (safety_car_schedule.count(current_lap)) {
    return static_cast<int>(safety_car_schedule.at(current_lap));
  }
  return SC_NONE;
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
  int current_lap = internal_cars[0].state.lap;
  record.lap = current_lap;

  SafetyCarType current_sc = SC_NONE;
  if (safety_car_schedule.count(current_lap)) {
    current_sc = safety_car_schedule[current_lap];
  }
  record.safety_car_status = static_cast<int>(current_sc);

  // Pit stop time loss: Green flag = 22.0s, VSC = 12.0s, Full SC = 9.0s ("cheap pit stop")
  double pit_time_loss = 22.0;
  if (current_sc == SC_VSC) {
    pit_time_loss = 12.0;
  } else if (current_sc == SC_FULL) {
    pit_time_loss = 9.0;
  }

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
        if (agent_actions.count(car.name)) {
          chosen_action = agent_actions.at(car.name);
        } else {
          chosen_action = car.strategy(car.state, gap);
        }

        if (chosen_action.pit) {
          car.state.total_time += pit_time_loss; 
          car.state.tire_age = 0.0;
          car.state.tire = engine.get_tire(chosen_action.new_tire);
        }
      }

      double sector_base_time = engine.compute_lap_time(car.state) / (double)track_sectors.size();
      double sector_effect = 0.0;
      double wear_multiplier = 1.0;

      if (current_sc == SC_VSC) {
        sector_base_time *= 1.35; // VSC delta speed (+35% slower lap)
        wear_multiplier = 0.50;    // Reduced tire stress under delta
        // DRS and slipstream are prohibited
      } else if (current_sc == SC_FULL) {
        sector_base_time *= 1.50; // Safety car pace (+50% slower lap)
        wear_multiplier = 0.35;   // Minimal tire degradation behind SC
        // DRS and slipstream are prohibited
      } else {
        // Green flag racing: DRS, Slipstream, Dirty air
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
      }

      if (sector_effect < 0) car.stats.total_time_gained_drs_slip += (-sector_effect);

      car.state.total_time += (sector_base_time + sector_effect);
      car.state.tire_age += (1.0 / (double)track_sectors.size()) * wear_multiplier;
    }
  }

  // Field compression under Full Safety Car
  if (current_sc == SC_FULL && internal_cars.size() > 1) {
    for (size_t i = 1; i < internal_cars.size(); ++i) {
      double max_gap = 0.8; // Pack compresses within 0.8s
      if (internal_cars[i].state.total_time > internal_cars[i - 1].state.total_time + max_gap) {
        internal_cars[i].state.total_time = internal_cars[i - 1].state.total_time + max_gap;
      }
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