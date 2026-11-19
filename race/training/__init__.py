"""PPO Training modules."""

from race.training.train import main as train_v1
from race.training.train_v2 import train as train_v2

__all__ = ["train_v1", "train_v2"]
