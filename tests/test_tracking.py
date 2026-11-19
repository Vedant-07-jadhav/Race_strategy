import json
from pathlib import Path
import matplotlib.pyplot as plt
import pytest
from race.tracking.experiment_tracker import ExperimentTracker


def test_experiment_tracker_creation_and_dirs(tmp_path):
    exp_dir = tmp_path / "outputs" / "experiments"
    tracker = ExperimentTracker("test_exp", config={"laps": 10}, base_dir=exp_dir)

    assert tracker.run_dir.exists()
    assert tracker.plots_dir.exists()
    assert tracker.checkpoints_dir.exists()
    assert tracker.run_id.startswith("run_")

    # Check metadata and config
    assert (tracker.run_dir / "metadata.json").exists()
    assert (tracker.run_dir / "config.json").exists()

    with open(tracker.run_dir / "config.json") as f:
        cfg = json.load(f)
        assert cfg["laps"] == 10


def test_experiment_tracker_metrics_and_plots(tmp_path):
    exp_dir = tmp_path / "outputs" / "experiments"
    tracker = ExperimentTracker("plot_metric_test", base_dir=exp_dir)

    tracker.log_metric("accuracy", 0.95)
    tracker.log_metric("loss", 0.05, step=1)
    tracker.log_metric("loss", 0.02, step=2)

    # Test plot generation
    fig, ax = plt.subplots()
    ax.plot([1, 2], [0.05, 0.02])
    ax.set_title("Test Loss")
    plot_file = tracker.save_plot(fig, "loss_curve.png")
    assert plot_file.exists()

    # Finish run
    tracker.finish(status="Passed", summary_notes="Smoke test completed successfully")

    assert (tracker.run_dir / "metrics.json").exists()
    assert (tracker.run_dir / "summary.md").exists()
    assert (tracker.run_dir / "execution.log").exists()

    with open(tracker.run_dir / "metrics.json") as f:
        m = json.load(f)
        assert m["summary_metrics"]["accuracy"] == 0.95
        assert m["status"] == "Passed"


def test_experiment_telemetry_csv(tmp_path):
    exp_dir = tmp_path / "outputs" / "experiments"
    tracker = ExperimentTracker("csv_test", base_dir=exp_dir)

    tracker.log_simulation_lap({"lap": 1, "car": "Car_1", "time": 90.5, "tire_age": 1.0})
    tracker.log_simulation_lap({"lap": 2, "car": "Car_1", "time": 90.7, "tire_age": 2.0})
    tracker.finish()

    csv_path = tracker.run_dir / "results.csv"
    assert csv_path.exists()
    lines = csv_path.read_text().strip().split("\n")
    assert len(lines) == 3  # Header + 2 rows
    assert "Car_1" in lines[1]
