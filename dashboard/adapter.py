"""Data adapter for converting simulator race history and experiment artifacts into standardized structures for UI and Plotly."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class LapSnapshot:
    lap: int
    leader_name: str
    safety_car_status: int
    safety_car_label: str
    positions: List[Dict[str, Any]]


class RaceDataAdapter:
    """Transforms C++ race_history and saved experiment outputs for UI consumption."""

    @staticmethod
    def parse_safety_car_label(sc_status: int) -> str:
        if sc_status == 1:
            return "VSC"
        elif sc_status == 2:
            return "Full SC"
        return "Green Flag"

    @classmethod
    def history_to_snapshots(
        cls,
        race_history,
        car_compounds: Optional[Dict[str, str]] = None,
        pit_counts: Optional[Dict[str, int]] = None,
    ) -> List[LapSnapshot]:
        """Converts raw C++ LapRecord vector into lap-by-lap timing and telemetry snapshots."""
        snapshots = []
        car_compounds = car_compounds or {}
        pit_counts = pit_counts or {}

        for record in race_history:
            lap = record.lap
            sc_status = record.safety_car_status
            sc_label = cls.parse_safety_car_label(sc_status)
            leader_name = record.leader_name
            leader_time = record.car_times.get(leader_name, 0.0)

            # Sort cars by cumulative race time
            sorted_cars = sorted(record.car_times.items(), key=lambda x: x[1])

            positions = []
            prev_time = leader_time
            for rank, (name, total_time) in enumerate(sorted_cars, start=1):
                gap_to_leader = total_time - leader_time
                interval = 0.0 if rank == 1 else (total_time - prev_time)
                prev_time = total_time

                tire_age = record.car_tire_ages.get(name, 0.0)
                compound = car_compounds.get(name, "Soft")
                pits = pit_counts.get(name, 0)

                # Extract interaction stats
                stats = record.car_stats.get(name, None)
                drs_count = stats.drs_count if stats else 0
                dirty_air_count = stats.dirty_air_count if stats else 0
                slip_count = stats.slipstream_count if stats else 0

                positions.append(
                    {
                        "rank": rank,
                        "driver": name,
                        "total_time": round(total_time, 3),
                        "gap_to_leader": round(gap_to_leader, 3),
                        "interval": round(interval, 3),
                        "tire_age": round(tire_age, 1),
                        "compound": compound,
                        "pit_stops": pits,
                        "drs_count": drs_count,
                        "dirty_air_count": dirty_air_count,
                        "slipstream_count": slip_count,
                    }
                )

            snapshots.append(
                LapSnapshot(
                    lap=lap,
                    leader_name=leader_name,
                    safety_car_status=sc_status,
                    safety_car_label=sc_label,
                    positions=positions,
                )
            )

        return snapshots

    @classmethod
    def snapshots_to_dataframe(cls, snapshots: List[LapSnapshot]) -> pd.DataFrame:
        """Flattens snapshots into a pandas DataFrame suitable for Plotly visualization."""
        rows = []
        for snap in snapshots:
            for pos in snap.positions:
                row = dict(pos)
                row["lap"] = snap.lap
                row["safety_car_status"] = snap.safety_car_status
                row["safety_car_label"] = snap.safety_car_label
                row["leader_name"] = snap.leader_name
                rows.append(row)
        return pd.DataFrame(rows)

    @classmethod
    def load_experiment_data(cls, run_dir: Path) -> Dict[str, Any]:
        """Loads an isolated experiment run directory into structured dictionary."""
        data = {
            "run_id": run_dir.name,
            "path": run_dir,
            "config": {},
            "metadata": {},
            "metrics": {},
            "summary_md": "",
            "plots": [],
            "telemetry_df": None,
        }

        config_file = run_dir / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                data["config"] = json.load(f)

        meta_file = run_dir / "metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                data["metadata"] = json.load(f)

        metrics_file = run_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                data["metrics"] = json.load(f)

        summary_file = run_dir / "summary.md"
        if summary_file.exists():
            data["summary_md"] = summary_file.read_text()

        plots_dir = run_dir / "plots"
        if plots_dir.exists():
            data["plots"] = list(plots_dir.glob("*.png"))

        csv_file = run_dir / "results.csv"
        if csv_file.exists():
            try:
                data["telemetry_df"] = pd.read_csv(csv_file)
            except Exception:
                data["telemetry_df"] = None

        return data

    @classmethod
    def list_saved_experiments(cls, base_dir: Path) -> List[Dict[str, Any]]:
        """Scans outputs/experiments/ and returns summary list of all runs sorted newest first."""
        runs = []
        if not base_dir.exists():
            return runs

        for run_path in sorted(base_dir.iterdir(), reverse=True):
            if run_path.is_dir() and run_path.name.startswith("run_"):
                exp_data = cls.load_experiment_data(run_path)
                runs.append(exp_data)

        return runs
