"""Entry point for clean-air strategy benchmarks."""

from race.benchmarks.benchmark_suite import run_clean_air_benchmarks

if __name__ == "__main__":
    run_clean_air_benchmarks(total_laps=50, initial_fuel=110.0, trials=30)
