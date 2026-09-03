"""
End-to-End ML Training & Lifecycle Pipeline Orchestrator for VoiceShield.
Executes the full 10-step ML lifecycle:
1. Dataset validation
2. Dataset preparation
3. Split generation (Speaker-disjoint, zero data leakage)
4. Model training (AASIST)
5. Validation evaluation
6. Best checkpoint selection
7. Test evaluation
8. Metrics generation (Accuracy, F1, EER, ROC-AUC, Confusion Matrix)
9. Model registration
10. Inference readiness check

Usage:
    python scripts/train_pipeline.py --epochs 20 --batch_size 16
"""

import os
import sys
import argparse
import json
import logging
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.data.validate_dataset import DatasetValidator
from ml.data.prepare_data import prepare_dataset_pipeline
from ml.training.config import TrainingConfig
from ml.training.trainer import ModelTrainer
from ml.evaluation.evaluate import evaluate_model
from ml.inference.model_manager import get_model_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("voiceshield.pipeline")


def run_full_pipeline(
    dataset_dir: str = "./datasets",
    manifest_dir: str = "./data/manifests",
    checkpoint_dir: str = "./checkpoints",
    reports_dir: str = "./reports",
    epochs: int = 20,
    batch_size: int = 16,
    learning_rate: float = 0.0001,
    device: str = "auto",
) -> dict:
    """
    Executes the 10-step automated ML lifecycle.
    """
    start_time = time.time()
    logger.info("=================================================================")
    logger.info("       VOICESHIELD — AUTOMATED ML TRAINING & LIFECYCLE PIPELINE  ")
    logger.info("=================================================================")

    # Step 1 & 2 & 3: Dataset Validation, Preparation & Speaker-Disjoint Split
    logger.info("[STEP 1-3] Validating, Preparing, and Splitting Dataset (Speaker-Disjoint)...")
    prep_res = prepare_dataset_pipeline(
        dataset_dir=dataset_dir,
        manifest_dir=manifest_dir,
    )

    if not prep_res["success"]:
        logger.warning(f"Dataset preparation halted: {prep_res.get('message')}")
        return {
            "success": False,
            "stage": "DATASET_PREPARATION",
            "message": prep_res.get("message"),
            "details": prep_res,
        }

    logger.info(f"Dataset splits created successfully: {prep_res['split_stats']}")

    # Step 4, 5 & 6: Training, Validation & Best Checkpoint Selection
    logger.info("[STEP 4-6] Training AASIST Neural Architecture...")
    config = TrainingConfig(
        dataset_dir=dataset_dir,
        manifest_dir=manifest_dir,
        checkpoint_dir=checkpoint_dir,
        reports_dir=reports_dir,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        device_name=device,
    )

    trainer = ModelTrainer(config=config)
    train_summary = trainer.train()
    logger.info(f"Training completed. Best Val F1: {train_summary['best_f1']:.4f}, Best Val EER: {train_summary['best_eer']:.4f}")

    # Step 7 & 8: Test Evaluation & Metrics Generation
    logger.info("[STEP 7-8] Running Evaluation on Held-Out Test Split...")
    test_manifest = os.path.join(manifest_dir, "test.csv")
    best_ckpt = os.path.join(checkpoint_dir, "best_model.pth")

    test_metrics = evaluate_model(
        checkpoint_path=best_ckpt,
        test_manifest=test_manifest,
        reports_dir=reports_dir,
        device_name=config.device_name,
        threshold=config.classification_threshold,
    )

    # Step 9: Model Registration & Quality Gate Check
    logger.info("[STEP 9] Registering Model in Model Registry & Quality Gate Evaluation...")
    
    prev_meta_path = os.path.join(checkpoint_dir, "registered_model.json")
    quality_gate_passed = True
    gate_reason = "Initial model registration or quality benchmark met."

    if os.path.exists(prev_meta_path):
        try:
            with open(prev_meta_path, "r", encoding="utf-8") as f:
                prev_entry = json.load(f)
            prev_f1 = prev_entry.get("test_metrics", {}).get("f1", 0.0)
            prev_eer = prev_entry.get("test_metrics", {}).get("eer", 1.0)
            new_f1 = test_metrics.get("f1", 0.0)
            new_eer = test_metrics.get("eer", 1.0)

            # Quality Gate: Candidate must not severely degrade F1 or EER
            if new_f1 < (prev_f1 - 0.15) and new_eer > (prev_eer + 0.15):
                quality_gate_passed = False
                gate_reason = f"REJECT_NEW_MODEL: Candidate F1 ({new_f1:.3f}) / EER ({new_eer:.3f}) degraded vs Active F1 ({prev_f1:.3f}) / EER ({prev_eer:.3f})"
                logger.warning(f"[QUALITY GATE] {gate_reason}")
            else:
                gate_reason = f"PROMOTED: Candidate model met quality gate (F1: {new_f1:.3f}, EER: {new_eer:.3f})"
                logger.info(f"[QUALITY GATE] {gate_reason}")
        except Exception as e_gate:
            logger.warning(f"Quality gate comparison skipped due to read error: {e_gate}")

    registry_entry = {
        "model_name": "AASIST",
        "version": config.model_version,
        "checkpoint_path": os.path.abspath(best_ckpt),
        "test_metrics": test_metrics,
        "hardware": config.get_hardware_description(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "quality_gate": {
            "passed": quality_gate_passed,
            "verdict": "PROMOTED" if quality_gate_passed else "REJECT_NEW_MODEL",
            "reason": gate_reason,
        },
        "active": quality_gate_passed,
    }

    reg_path = os.path.join(checkpoint_dir, "registered_model.json")
    if quality_gate_passed or not os.path.exists(reg_path):
        with open(reg_path, "w", encoding="utf-8") as f:
            json.dump(registry_entry, f, indent=2)

    # Step 10: Inference Readiness Check
    logger.info("[STEP 10] Verifying Inference Readiness...")
    model_mgr = get_model_manager()
    if quality_gate_passed:
        model_mgr.load_checkpoint(best_ckpt, mode="TRAINED_INFERENCE")
    status = model_mgr.get_status()

    total_time = round(time.time() - start_time, 2)
    logger.info("=================================================================")
    logger.info(f" PIPELINE COMPLETED IN {total_time}s! Model Ready: {status['model_mode']}")
    logger.info("=================================================================")

    return {
        "success": True,
        "pipeline_duration_sec": total_time,
        "dataset_stats": prep_res["split_stats"],
        "train_summary": {
            "best_epoch": train_summary["best_epoch"],
            "best_f1": train_summary["best_f1"],
            "best_eer": train_summary["best_eer"],
        },
        "test_metrics": test_metrics,
        "registered_model": registry_entry,
        "inference_status": status,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VoiceShield Master Training Pipeline")
    parser.add_argument("--dataset_dir", type=str, default="./datasets")
    parser.add_argument("--manifest_dir", type=str, default="./data/manifests")
    parser.add_argument("--checkpoint_dir", type=str, default="./checkpoints")
    parser.add_argument("--reports_dir", type=str, default="./reports")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    res = run_full_pipeline(
        dataset_dir=args.dataset_dir,
        manifest_dir=args.manifest_dir,
        checkpoint_dir=args.checkpoint_dir,
        reports_dir=args.reports_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        device=args.device,
    )
    print(json.dumps(res, indent=2))
