#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "engine.hpp"
#include "simulator.hpp"

/*
// g++ -O3 -Wall -shared -std=c++17 -fPIC $(python3 -m pybind11 --includes) \
    bindings.cpp engine.cpp simulator.cpp \
    -o race_engine$(python3-config --extension-suffix)*/
namespace py = pybind11;

PYBIND11_MODULE(race_engine, m) {
    m.doc() = "F1 Race Strategy Engine with Sector-Based Interaction Support";

    // --- Core Engine Structs ---
    py::class_<Tire>(m, "Tire")
        .def_readonly("name", &Tire::name)
        .def_readonly("base_offset", &Tire::base_offset);

    py::class_<Action>(m, "Action")
        .def(py::init<bool, std::string>())
        .def_readwrite("pit", &Action::pit)
        .def_readwrite("new_tire", &Action::new_tire);

    py::class_<State>(m, "State")
        .def_readonly("lap", &State::lap)
        .def_readonly("tire", &State::tire)
        .def_readonly("tire_age", &State::tire_age) // Now correctly reflects double precision
        .def_readonly("fuel", &State::fuel)
        .def_readonly("total_time", &State::total_time);

    py::class_<LapData>(m, "LapData")
        .def_readonly("lap", &LapData::lap)
        .def_readonly("lap_time", &LapData::lap_time)
        .def_readonly("tire_age", &LapData::tire_age)
        .def_readonly("tire", &LapData::tire)
        .def_readonly("fuel", &LapData::fuel);

    // --- Core RaceEngine Class ---
    py::class_<RaceEngine>(m, "RaceEngine")
        .def(py::init<>())
        .def("get_tire", &RaceEngine::get_tire)
        .def("compute_lap_time", &RaceEngine::compute_lap_time)
        .def("step", &RaceEngine::step, 
             py::arg("s"), py::arg("a"), py::arg("lap_time"), py::arg("wear_factor") = 1.0)
        .def("get_optimal_DP_strategy", &RaceEngine::get_optimal_DP_strategy);

    // --- Interaction and Simulator Bindings ---
    py::class_<InteractionStats>(m, "InteractionStats")
        .def_readonly("slipstream_count", &InteractionStats::slipstream_count)
        .def_readonly("drs_count", &InteractionStats::drs_count)
        .def_readonly("dirty_air_count", &InteractionStats::dirty_air_count)
        .def_readonly("total_time_lost_dirty_air", &InteractionStats::total_time_lost_dirty_air)
        .def_readonly("total_time_gained_drs_slip", &InteractionStats::total_time_gained_drs_slip);

    py::class_<LapRecord>(m, "LapRecord")
        .def_readonly("lap", &LapRecord::lap)
        .def_readonly("leader_name", &LapRecord::leader_name)
        .def_readonly("car_times", &LapRecord::car_times)
        .def_readonly("car_tire_ages", &LapRecord::car_tire_ages)
        .def_readonly("car_stats", &LapRecord::car_stats);

    py::class_<RaceSimulator>(m, "RaceSimulator")
        .def(py::init<>())
        .def("add_car", &RaceSimulator::add_car)
        .def("simulate_race", &RaceSimulator::simulate_race)
        .def("print_results", &RaceSimulator::print_results)
        .def_readonly("race_history", &RaceSimulator::race_history);
}