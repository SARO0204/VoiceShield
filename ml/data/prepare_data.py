"""
Dataset Preparation CLI & Orchestration Script for VoiceShield.
Usage:
    python ml/data/prepare_data.py --dataset_dir ./datasets --output_dir ./data/manifests
"""

import os
import argparse
import json
import logging
from typing import Dict, Any

from ml.data.validate_dataset import DatasetValidator
from ml.data.split_dataset import DatasetSplitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("voiceshield.prepare_data")


def prepare_dataset_pipeline(
    dataset_dir: str = "./datasets",
    manifest_dir: str = "./data/manifests",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes dataset preparation:
    1. Validates dataset existence and file integrity.
    2. Filters corrupted/unsupported files.
    3. Infers speaker IDs and attack types.
    4. Computes speaker-disjoint Train/Val/Test splits.
    5. Saves manifest CSVs (train.csv, validation.csv, test.csv).
    """
    logger.info(f"Initiating dataset preparation from '{dataset_dir}' to '{manifest_dir}'...")

    validator = DatasetValidator()
    validation_report = validator.validate_dataset(dataset_dir)

    if validation_report["status"] != "VALID" or validation_report["valid_samples_count"] == 0:
        logger.warning(f"Dataset validation returned status: {validation_report['status']}. Valid samples: {validation_report['valid_samples_count']}")
        return {
            "success": False,
            "status": validation_report["status"],
            "message": validation_report.get("message", "No valid samples found"),
            "validation_report": validation_report,
        }

    logger.info(f"Discovered {validation_report['valid_samples_count']} valid audio samples ({validation_report['total_valid_duration_hours']} hours).")

    # Build sample records with speaker & labels
    splitter = DatasetSplitter(train_ratio=train_ratio, val_ratio=val_ratio, test_ratio=test_ratio, seed=seed)
    samples = []
    audio_files = validator.find_audio_files(dataset_dir)

    for fpath in audio_files:
        is_valid, _, meta = validator.validate_sample(fpath)
        if not is_valid or not meta:
            continue

        spk_id, label, atk_type = splitter.extract_speaker_and_label(fpath)
        samples.append({
            "audio_path": os.path.abspath(fpath),
            "label": label,
            "speaker_id": spk_id,
            "dataset": os.path.basename(dataset_dir),
            "attack_type": atk_type,
            "duration_sec": meta["duration_sec"],
        })

    train_samples, val_samples, test_samples, split_stats = splitter.create_speaker_disjoint_splits(samples)
    manifest_paths = splitter.export_manifests(manifest_dir, train_samples, val_samples, test_samples)

    summary = {
        "success": True,
        "status": "PREPARED",
        "dataset_dir": os.path.abspath(dataset_dir),
        "manifest_dir": os.path.abspath(manifest_dir),
        "manifest_paths": manifest_paths,
        "split_stats": split_stats,
        "validation_report": {
            "total_files": validation_report["total_files_scanned"],
            "corrupted_files": validation_report["corrupted_samples_count"],
        },
    }

    # Save summary report
    summary_path = os.path.join(manifest_dir, "dataset_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Dataset prepared successfully! Manifests written to '{manifest_dir}'. Split stats: {split_stats}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare and split anti-spoofing dataset")
    parser.add_argument("--dataset_dir", type=str, default="./datasets", help="Directory containing raw audio files")
    parser.add_argument("--output_dir", type=str, default="./data/manifests", help="Directory for generated manifests")
    parser.add_argument("--train_ratio", type=float, default=0.70)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--test_ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    res = prepare_dataset_pipeline(
        dataset_dir=args.dataset_dir,
        manifest_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    print(json.dumps(res, indent=2))
