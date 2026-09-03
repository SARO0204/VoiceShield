"""
Training CLI Entrypoint for VoiceShield.
Usage:
    python ml/training/train.py --dataset_dir ./datasets --epochs 20 --batch_size 16
"""

import os
import argparse
import json
import logging
from ml.training.config import TrainingConfig
from ml.training.trainer import ModelTrainer
from ml.models.aasist_detector import AASISTDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("voiceshield.train")


def run_training(
    dataset_dir: str = "./datasets",
    manifest_dir: str = "./data/manifests",
    checkpoint_dir: str = "./checkpoints",
    epochs: int = 20,
    batch_size: int = 16,
    learning_rate: float = 0.0001,
    device: str = "auto",
) -> dict:
    """Configures and runs training session."""
    config = TrainingConfig(
        dataset_dir=dataset_dir,
        manifest_dir=manifest_dir,
        checkpoint_dir=checkpoint_dir,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        device_name=device,
    )

    trainer = ModelTrainer(config=config)
    summary = trainer.train()
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AASIST voice deepfake detector")
    parser.add_argument("--dataset_dir", type=str, default="./datasets")
    parser.add_argument("--manifest_dir", type=str, default="./data/manifests")
    parser.add_argument("--checkpoint_dir", type=str, default="./checkpoints")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    result = run_training(
        dataset_dir=args.dataset_dir,
        manifest_dir=args.manifest_dir,
        checkpoint_dir=args.checkpoint_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        device=args.device,
    )
    print(json.dumps(result, indent=2))
