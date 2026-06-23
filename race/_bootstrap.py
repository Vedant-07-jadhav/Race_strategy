from pathlib import Path
import sys


def ensure_project_paths() -> Path:
    root = Path(__file__).resolve().parents[1]
    for candidate in (root, root / "build", root / "backend" / "src" / "cpp"):
        if candidate.exists():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
    return root
