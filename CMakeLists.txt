cmake_minimum_required(VERSION 3.14)
project(RaceEngine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. Force CMake to find the Python and PyBind11 linked to your Virtual Environment
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# 2. Build the Python Extension Module (.so file)
pybind11_add_module(race_engine MODULE
  backend/src/cpp/bindings.cpp
  backend/src/cpp/engine.cpp
  backend/src/cpp/simulator.cpp
)
target_include_directories(race_engine PRIVATE ${CMAKE_SOURCE_DIR}/backend/src/cpp)

# 3. (Optional) Build a pure C++ library just in case
add_library(race_engine_core SHARED
  backend/src/cpp/engine.cpp
  backend/src/cpp/simulator.cpp
)
target_include_directories(race_engine_core PRIVATE ${CMAKE_SOURCE_DIR}/backend/src/cpp)