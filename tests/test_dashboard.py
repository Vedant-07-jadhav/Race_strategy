import json
from pathlib import Path
import pandas as pd
import pytest
from dashboard.adapter import LapSnapshot, RaceDataAdapter
from dashboard.charts import build_gap_chart, build_position_chart, build_stint_timeline_bars, build_tire_stint_chart
from race._bootstrap import ensure_project_paths

ensure_project_paths()
import race_engine


def test_adapter_history_to_snapshots():
    sim = race_engine.RaceSimulator()
    sim.set_seed(42)
    sim.add_car("Driver_1", lambda s, g: race_engine.Action(False, "Soft"), 110.0)
    sim.add_car("Driver_2", lambda s, g: race_engine.Action(False, "Medium"), 110.0)
    sim.simulate_race(3)

    snapshots = RaceDataAdapter.history_to_snapshots(
        sim.race_history,
        car_compounds={"Driver_1": "Soft", "Driver_2": "Medium"},
        pit_counts={"Driver_1": 0, "Driver_2": 0},
    )

    assert len(snapshots) == 3
    assert snapshots[0].lap == 1
    assert len(snapshots[0].positions) == 2
    assert snapshots[0].positions[0]["rank"] == 1
    assert snapshots[0].positions[0]["driver"] in ["Driver_1", "Driver_2"]


def test_snapshots_to_dataframe():
    snapshots = [
        LapSnapshot(
            lap=1,
            leader_name="Car_A",
            safety_car_status=0,
            safety_car_label="Green Flag",
            positions=[
                {
                    "rank": 1,
                    "driver": "Car_A",
                    "total_time": 90.0,
                    "gap_to_leader": 0.0,
                    "interval": 0.0,
                    "tire_age": 1.0,
                    "compound": "Soft",
                    "pit_stops": 0,
                },
                {
                    "rank": 2,
                    "driver": "Car_B",
                    "total_time": 91.5,
                    "gap_to_leader": 1.5,
                    "interval": 1.5,
                    "tire_age": 1.0,
                    "compound": "Medium",
                    "pit_stops": 0,
                },
            ],
        )
    ]

    df = RaceDataAdapter.snapshots_to_dataframe(snapshots)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "gap_to_leader" in df.columns
    assert "safety_car_label" in df.columns


def test_dashboard_charts_generation():
    df = pd.DataFrame(
        [
            {
                "lap": 1,
                "driver": "Car_1",
                "gap_to_leader": 0.0,
                "rank": 1,
                "tire_age": 1.0,
                "compound": "Soft",
                "safety_car_status": 0,
                "safety_car_label": "Green",
            },
            {
                "lap": 2,
                "driver": "Car_1",
                "gap_to_leader": 0.0,
                "rank": 1,
                "tire_age": 2.0,
                "compound": "Soft",
                "safety_car_status": 0,
                "safety_car_label": "Green",
            },
            {
                "lap": 1,
                "driver": "Car_2",
                "gap_to_leader": 1.2,
                "rank": 2,
                "tire_age": 1.0,
                "compound": "Medium",
                "safety_car_status": 0,
                "safety_car_label": "Green",
            },
            {
                "lap": 2,
                "driver": "Car_2",
                "gap_to_leader": 0.8,
                "rank": 2,
                "tire_age": 2.0,
                "compound": "Medium",
                "safety_car_status": 0,
                "safety_car_label": "Green",
            },
        ]
    )

    fig_gap = build_gap_chart(df)
    assert fig_gap is not None

    fig_pos = build_position_chart(df)
    assert fig_pos is not None

    fig_stint = build_tire_stint_chart(df)
    assert fig_stint is not None

    fig_bars = build_stint_timeline_bars(df)
    assert fig_bars is not None


def test_load_experiment_data(tmp_path):
    run_dir = tmp_path / "run_20261119_120000_abc123"
    run_dir.mkdir()
    (run_dir / "config.json").write_text(json.dumps({"laps": 50}))
    (run_dir / "metadata.json").write_text(json.dumps({"python": "3.15"}))
    (run_dir / "summary.md").write_text("# Test Summary")

    exp_data = RaceDataAdapter.load_experiment_data(run_dir)
    assert exp_data["run_id"] == "run_20261119_120000_abc123"
    assert exp_data["config"]["laps"] == 50
    assert exp_data["metadata"]["python"] == "3.15"
    assert "Test Summary" in exp_data["summary_md"]
