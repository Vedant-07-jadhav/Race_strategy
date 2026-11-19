"""Backward compatibility shim for train_v2."""

from race.training.train_v2 import train

if __name__ == "__main__":
    train()
