"""
Model Evaluation CLI & Execution Script for VoiceShield.
Usage:
    python ml/evaluation/evaluate.py --checkpoint ./checkpoints/best_model.pth --manifest ./data/manifests/test.csv
"""

import os
import argparse
import json
import logging
import torch
from torch.utils.data import DataLoader

from ml.preprocessing.audio_preprocessor import AudioPreprocessor
from ml.models.aasist_detector import AASISTDetector
from ml.training.trainer import AntiSpoofingDataset
from ml.evaluation.metrics import compute_full_metrics
from ml.evaluation.reports import EvaluationReporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("voiceshield.evaluate")


def evaluate_model(
    checkpoint_path: str = "./checkpoints/best_model.pth",
    test_manifest: str = "./data/manifests/test.csv",
    reports_dir: str = "./reports",
    device_name: str = "auto",
    threshold: float = 0.50,
) -> dict:
    """
    Evaluates a saved checkpoint on a test manifest and outputs reports/model_evaluation.json.
    """
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")
    if not os.path.exists(test_manifest):
        raise FileNotFoundError(f"Test manifest not found at: {test_manifest}")

    device = torch.device("cuda" if torch.cuda.is_available() and device_name != "cpu" else "cpu")

    model = AASISTDetector()
    checkpoint = torch.load(checkpoint_path, map_location=device)
    if "state_dict" in checkpoint:
        model.load_state_dict(checkpoint["state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()

    preprocessor = AudioPreprocessor()
    test_dataset = AntiSpoofingDataset(test_manifest, preprocessor)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    all_labels = []
    all_scores = []

    logger.info(f"Evaluating {len(test_dataset)} test samples on {device}...")
    with torch.no_grad():
        for waveforms, labels, _ in test_loader:
            waveforms = waveforms.to(device)
            logits = model(waveforms)
            probs = torch.softmax(logits, dim=-1)
            spoof_probs = probs[:, 1].cpu().numpy()

            all_labels.extend(labels.numpy().tolist())
            all_scores.extend(spoof_probs.tolist())

    metrics = compute_full_metrics(all_labels, all_scores, threshold=threshold)
    logger.info(f"Evaluation complete: Accuracy: {metrics['accuracy']}, F1: {metrics['f1']}, EER: {metrics['eer']}")

    reporter = EvaluationReporter(reports_dir=reports_dir)
    reporter.generate_report(
        model_metadata=checkpoint.get("config", {"model_name": "AASIST", "model_version": "1.0"}),
        metrics=metrics,
        dataset_info={"test_manifest": os.path.abspath(test_manifest), "test_samples": len(test_dataset)},
    )

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AASIST model checkpoint")
    parser.add_argument("--checkpoint", type=str, default="./checkpoints/best_model.pth")
    parser.add_argument("--manifest", type=str, default="./data/manifests/test.csv")
    parser.add_argument("--reports_dir", type=str, default="./reports")
    parser.add_argument("--threshold", type=float, default=0.50)
    args = parser.parse_args()

    metrics = evaluate_model(
        checkpoint_path=args.checkpoint,
        test_manifest=args.manifest,
        reports_dir=args.reports_dir,
        threshold=args.threshold,
    )
    print(json.dumps(metrics, indent=2))
