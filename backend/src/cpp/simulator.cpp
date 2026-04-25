#include "engine.hpp"
#include "simulator.hpp"
#include <algorithm>
#include <cstddef>
#include <iostream>
#include <vector>

RaceSimulator::RaceSimulator() {
  // Sector layout: Corner followed by two straights (encourages drafting)
  track_sectors = {CORNER, STRAIGHT, STRAIGHT};
}

void RaceSimulator::add_car(const std::string &name, StrategyWithGap strategy,
                            double initial_fuel) {
  CarInternal car;
  car.name = name;
  car.strategy = strategy;
  double grid_offset = internal_cars.size() * 0.2;
  car.state = {1, engine.get_tire("Soft"), 0, initial_fuel, grid_offset};
  internal_cars.push_back(car);
}

void RaceSimulator::simulate_one_lap(Action &a) {
  LapRecord record;
  record.lap = lap;

  for (auto sector : track_sectors) {
    // 1. RE-SORT EVERY SECTOR: Correct track order for current physics
    std::sort(internal_cars.begin(), internal_cars.end(),
              [](const CarInternal &a, const CarInternal &b) {
                return a.state.total_time < b.state.total_time;
              });

    // 2. SECTOR SNAPSHOT: Freeze positions before sector calculations
    std::vector<double> sector_start_times;
    for (auto &c : internal_cars)
      sector_start_times.push_back(c.state.total_time);

    for (size_t i = 0; i < internal_cars.size(); ++i) {
      auto &car = internal_cars[i];
      double gap =
          (i == 0) ? -1.0 : sector_start_times[i] - sector_start_times[i - 1];

      // Strategy called at start of lap (first sector)
      Action a = {false, ""};
      if (sector == track_sectors[0]) {
        a = car.strategy(car.state, gap);
      }

      double sector_base_time = engine.compute_lap_time(car.state) / 3.0;
      double sector_effect = 0.0;
      double wear_multiplier = 1.0;

      // 3. SECTOR PHYSICS
      if (gap > 0.0 && gap < 3.0) {
        if (sector == STRAIGHT) {
          sector_effect -= 0.4;
          car.stats.slipstream_count++;
          if (gap < 1.2) {
            sector_effect -= 0.7;
            car.stats.drs_count++;
          }
        } else if (sector == CORNER && gap < 1.5) {
          double pen = 0.6 * (1.0 - (gap / 1.5));
          sector_effect += pen;
          wear_multiplier += (0.25 * (1.0 - (gap / 1.5)));
          car.stats.dirty_air_count++;
          car.stats.total_time_lost_dirty_air += pen;
        }
      }

      // Cumulative Gain Tracking
      if (sector_effect < 0)
        car.stats.total_time_gained_drs_slip += (-sector_effect);

      // 4. UPDATE MID-LAP STATE
      if (a.pit && sector == track_sectors[0]) {
        car.state.total_time += 22.0;
        car.state.tire_age = 0.0;
        car.state.tire = engine.get_tire(a.new_tire);
      }

      car.state.total_time += (sector_base_time + sector_effect);
      car.state.tire_age += (0.33 * wear_multiplier);
    }
  }

  // Finalize Lap Record
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

void RaceSimulator::simulate_race(int total_laps) {
  this->race_history.clear();
  for (int lap = 1; lap <= total_laps; lap++) {
    LapRecord record;
    record.lap = lap;

    for (auto sector : track_sectors) {
      // 1. RE-SORT EVERY SECTOR: Correct track order for current physics
      std::sort(internal_cars.begin(), internal_cars.end(),
                [](const CarInternal &a, const CarInternal &b) {
                  return a.state.total_time < b.state.total_time;
                });

      // 2. SECTOR SNAPSHOT: Freeze positions before sector calculations
      std::vector<double> sector_start_times;
      for (auto &c : internal_cars)
        sector_start_times.push_back(c.state.total_time);

      for (size_t i = 0; i < internal_cars.size(); ++i) {
        auto &car = internal_cars[i];
        double gap =
            (i == 0) ? -1.0 : sector_start_times[i] - sector_start_times[i - 1];

        // Strategy called at start of lap (first sector)
        Action a = {false, ""};
        if (sector == track_sectors[0]) {
          a = car.strategy(car.state, gap);
        }

        double sector_base_time = engine.compute_lap_time(car.state) / 3.0;
        double sector_effect = 0.0;
        double wear_multiplier = 1.0;

        // 3. SECTOR PHYSICS
        if (gap > 0.0 && gap < 3.0) {
          if (sector == STRAIGHT) {
            sector_effect -= 0.4;
            car.stats.slipstream_count++;
            if (gap < 1.2) {
              sector_effect -= 0.7;
              car.stats.drs_count++;
            }
          } else if (sector == CORNER && gap < 1.5) {
            double pen = 0.6 * (1.0 - (gap / 1.5));
            sector_effect += pen;
            wear_multiplier += (0.25 * (1.0 - (gap / 1.5)));
            car.stats.dirty_air_count++;
            car.stats.total_time_lost_dirty_air += pen;
          }
        }

        // Cumulative Gain Tracking
        if (sector_effect < 0)
          car.stats.total_time_gained_drs_slip += (-sector_effect);

        // 4. UPDATE MID-LAP STATE
        if (a.pit && sector == track_sectors[0]) {
          car.state.total_time += 22.0;
          car.state.tire_age = 0.0;
          car.state.tire = engine.get_tire(a.new_tire);
        }

        car.state.total_time += (sector_base_time + sector_effect);
        car.state.tire_age += (0.33 * wear_multiplier);
      }
    }

    // Finalize Lap Record
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
}

void RaceSimulator::print_results() {
  std::sort(internal_cars.begin(), internal_cars.end(),
            [](const CarInternal &a, const CarInternal &b) {
              return a.state.total_time < b.state.total_time;
            });

  std::cout << "\n--- FINAL RESULTS & INTERACTION STATS ---\n";
  for (int i = 0; i < (int)internal_cars.size(); ++i) {
    auto &c = internal_cars[i];
    std::cout << i + 1 << ". " << c.name << " | Time: " << c.state.total_time
              << "s\n"
              << "   Interactions: DRS(" << c.stats.drs_count << ") SLIP("
              << c.stats.slipstream_count << ") DIRTY("
              << c.stats.dirty_air_count << ")\n"
              << "   Net Delta: -" << c.stats.total_time_gained_drs_slip
              << "s / +" << c.stats.total_time_lost_dirty_air << "s\n"
              << "-------------------------------------------\n";
  }
}