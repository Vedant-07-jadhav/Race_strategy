"""Centralized Experiment Tracking, Simulation Logging & Research Journaling System.

Manages reproducible run directories, metadata, telemetry metrics, automated
Matplotlib plot generation, and Markdown summary reports under outputs/experiments/.
"""

import csv
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional
import uuid
import matplotlib.pyplot as plt
import numpy as np


class ExperimentTracker:
    """Manages an isolated experiment run in outputs/experiments/run_YYYYMMDD_HHMMSS_id."""

    def __init__(
        self,
        experiment_name: str,
        config: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None,
    ):
        self.experiment_name = experiment_name
        self.config = config or {}
        self.start_time = datetime.now()

        # Generate unique run ID: run_YYYYMMDD_HHMMSS_<6char_uuid>
        timestamp_str = self.start_time.strftime("%Y%m%d_%H%M%S")
        unique_suffix = uuid.uuid4().hex[:6]
        self.run_id = f"run_{timestamp_str}_{unique_suffix}"

        # Root directory
        if base_dir is None:
            self.project_root = Path(__file__).resolve().parents[2]
            self.base_dir = self.project_root / "outputs" / "experiments"
        else:
            self.base_dir = Path(base_dir)
            self.project_root = self.base_dir.parent.parent

        self.run_dir = self.base_dir / self.run_id
        self.plots_dir = self.run_dir / "plots"
        self.checkpoints_dir = self.run_dir / "checkpoints"

        # Create isolated directories
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        # Logging setup
        self.log_file = self.run_dir / "execution.log"
        self.logger = logging.getLogger(self.run_id)
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_file)
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        self.logger.addHandler(fh)

        # Telemetry & metrics state
        self.metrics: Dict[str, Any] = {}
        self.series_metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.simulation_records: List[Dict[str, Any]] = []
        self.csv_file = self.run_dir / "results.csv"

        # Record initial configuration & environment metadata
        self._record_metadata()
        self._record_config()
        self.logger.info(f"Initialized Experiment {self.experiment_name} with Run ID: {self.run_id}")

    def _get_git_commit(self) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            return res.stdout.strip() or "uncommitted"
        except Exception:
            return "unknown"

    def _get_git_branch(self) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            return res.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def _record_metadata(self):
        metadata = {
            "run_id": self.run_id,
            "experiment_name": self.experiment_name,
            "start_time": self.start_time.isoformat(),
            "git_commit": self._get_git_commit(),
            "git_branch": self._get_git_branch(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
        }
        with open(self.run_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def _record_config(self):
        with open(self.run_dir / "config.json", "w") as f:
            json.dump(self.config, f, indent=2)

    def log_metric(self, key: str, value: Any, step: Optional[int] = None):
        """Record a scalar or time-series metric."""
        if step is not None:
            if key not in self.series_metrics:
                self.series_metrics[key] = []
            self.series_metrics[key].append({"step": step, "value": value})
        else:
            self.metrics[key] = value
        self.logger.info(f"Metric - {key}: {value} (step={step})")

    def log_simulation_lap(self, lap_data: Dict[str, Any]):
        """Record granular telemetry for a driver/car at a given lap."""
        self.simulation_records.append(lap_data)

    def save_checkpoint_path(self, filename: str) -> Path:
        """Returns isolated checkpoint path."""
        return self.checkpoints_dir / filename

    def save_plot(self, fig: plt.Figure, filename: str) -> Path:
        """Save a Matplotlib figure into the experiment plots directory."""
        if not filename.endswith((".png", ".svg", ".pdf")):
            filename += ".png"
        plot_path = self.plots_dir / filename
        fig.savefig(plot_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        self.logger.info(f"Saved plot: {plot_path.name}")
        return plot_path

    def _flush_csv(self):
        if not self.simulation_records:
            return
        fieldnames = list(self.simulation_records[0].keys())
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.simulation_records)

    def finish(self, status: str = "Passed", summary_notes: str = ""):
        """Finalize the run: flush data, save metrics, generate summary.md, update journal."""
        end_time = datetime.now()
        duration_s = (end_time - self.start_time).total_seconds()

        # Flush metrics
        final_metrics = {
            "summary_metrics": self.metrics,
            "series_metrics": self.series_metrics,
            "status": status,
            "duration_seconds": duration_s,
            "end_time": end_time.isoformat(),
        }
        with open(self.run_dir / "metrics.json", "w") as f:
            json.dump(final_metrics, f, indent=2)

        # Flush telemetry CSV
        self._flush_csv()

        # Generate summary.md
        summary_content = self._generate_summary_markdown(status, duration_s, summary_notes)
        with open(self.run_dir / "summary.md", "w") as f:
            f.write(summary_content)

        # Update docs/EXPERIMENT_JOURNAL.md
        self._append_to_journal(status, duration_s, summary_notes)
        self.logger.info(f"Experiment {self.run_id} finalized with status: {status}")

    def _generate_summary_markdown(self, status: str, duration_s: float, notes: str) -> str:
        lines = [
            f"# Experiment Summary: {self.experiment_name}",
            f"- **Run ID:** `{self.run_id}`",
            f"- **Status:** `{status}`",
            f"- **Duration:** {duration_s:.2f} seconds",
            f"- **Timestamp:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Configuration",
            "```json",
            json.dumps(self.config, indent=2),
            "```",
            "",
            "## Key Metrics",
        ]
        for k, v in self.metrics.items():
            lines.append(f"- **{k}:** {v}")

        plot_files = list(self.plots_dir.glob("*.png"))
        if plot_files:
            lines.append("\n## Generated Visualizations")
            for pf in plot_files:
                lines.append(f"- ![{pf.stem}](plots/{pf.name})")

        if notes:
            lines.append(f"\n## Notes & Conclusions\n{notes}\n")

        return "\n".join(lines)

    def _append_to_journal(self, status: str, duration_s: float, notes: str):
        journal_path = self.project_root / "docs" / "EXPERIMENT_JOURNAL.md"
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        entry = (
            f"| {self.start_time.strftime('%Y-%m-%d %H:%M')} "
            f"| `{self.run_id}` "
            f"| {self.experiment_name} "
            f"| **{status}** "
            f"| {duration_s:.1f}s "
            f"| [Summary](file://{self.run_dir}/summary.md) "
            f"| {notes.replace('|', '/')} |\n"
        )
        if not journal_path.exists():
            header = (
                "# Permanent Research Experiment Journal\n\n"
                "Chronological ledger of every simulated race, DP baseline benchmark, and RL training experiment.\n\n"
                "| Date | Run ID | Experiment | Status | Duration | Report | Notes |\n"
                "|---|---|---|---|---|---|---|\n"
            )
            journal_path.write_text(header + entry)
        else:
            with open(journal_path, "a") as f:
                f.write(entry)
