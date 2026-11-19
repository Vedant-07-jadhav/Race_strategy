cmake_minimum_required(VERSION 3.18)
project(RaceEngine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. Prioritize active virtual environment for Python & PyBind11 discovery on macOS
if(DEFINED ENV{VIRTUAL_ENV})
    set(Python_EXECUTABLE "$ENV{VIRTUAL_ENV}/bin/python")
endif()

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# 2. Build the Python Extension Module (.so file)
pybind11_add_module(race_engine MODULE
  backend/bindings/bindings.cpp
  backend/engine/engine.cpp
  backend/simulator/simulator.cpp
)
target_include_directories(race_engine PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/backend/engine
  ${CMAKE_CURRENT_SOURCE_DIR}/backend/simulator
  ${CMAKE_CURRENT_SOURCE_DIR}/backend/bindings
)

# 3. Pure C++ static library for native linking
add_library(race_engine_core STATIC
  backend/engine/engine.cpp
  backend/simulator/simulator.cpp
)
target_include_directories(race_engine_core PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/backend/engine
  ${CMAKE_CURRENT_SOURCE_DIR}/backend/simulator
  ${CMAKE_CURRENT_SOURCE_DIR}/backend/bindings
)