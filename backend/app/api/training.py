"""
ML Training Manager and Background Worker API for VoiceShield.
Provides background execution, status polling, epoch logs, and model registration.
"""

import os
import time
import json
import threading
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.app.core.config import settings
from ml.training.config import TrainingConfig
from ml.training.trainer import ModelTrainer
from ml.data.prepare_data import prepare_dataset_pipeline
from ml.data.validate_dataset import DatasetValidator
from ml.inference.model_manager import get_model_manager

logger = logging.getLogger("voiceshield.api.training")
router = APIRouter(prefix="/api/training", tags=["ML Training"])

# Global in-process training state supervisor
training_state: Dict[str, Any] = {
    "status": "NOT_STARTED",  # NOT_STARTED, PREPARING_DATA, TRAINING, VALIDATING, EVALUATING, COMPLETED, FAILED, NO_DATASET
    "current_epoch": 0,
    "total_epochs": 20,
    "progress_percent": 0.0,
    "train_loss": 0.0,
    "val_loss": 0.0,
    "val_f1": 0.0,
    "val_eer": 0.0,
    "best_f1": 0.0,
    "best_eer": 1.0,
    "message": "Ready to initiate training.",
    "dataset_status": "UNKNOWN",
    "gpu_status": "AVAILABLE" if TrainingConfig().device_name == "cuda" else "CPU_FALLBACK",
    "model_version": "aasist-v1.0",
    "logs": [],
    "history": [],
    "started_at": None,
    "completed_at": None,
    "error": None,
}

_training_lock = threading.Lock()


class StartTrainingRequest(BaseModel):
    epochs: Optional[int] = 20
    batch_size: Optional[int] = 16
    learning_rate: Optional[float] = 0.0001
    dataset_dir: Optional[str] = None
    force_restart: Optional[bool] = False


def _training_worker(config: TrainingConfig):
    """Background worker execution."""
    global training_state
    try:
        # Step 1: Validate Dataset
        with _training_lock:
            training_state["status"] = "PREPARING_DATA"
            training_state["message"] = "Validating and preparing anti-spoofing dataset..."
            training_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] Validating dataset at {config.dataset_dir}...")

        prep_result = prepare_dataset_pipeline(
            dataset_dir=config.dataset_dir,
            manifest_dir=config.manifest_dir,
        )

        if not prep_result["success"]:
            with _training_lock:
                training_state["status"] = "NO_DATASET"
                training_state["dataset_status"] = "NOT_FOUND"
                training_state["message"] = f"Training aborted: {prep_result.get('message', 'No valid audio dataset found')}"
                training_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {training_state['message']}")
            return

        with _training_lock:
            training_state["dataset_status"] = "READY"
            training_state["status"] = "TRAINING"
            training_state["total_epochs"] = config.epochs
            training_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] Dataset prepared. Starting AASIST training loop...")

        # Step 2: Callback function for real-time progress
        def on_epoch_progress(progress_dict: Dict[str, Any]):
            with _training_lock:
                training_state.update(progress_dict)
                training_state["logs"].append(
                    f"[{time.strftime('%H:%M:%S')}] Epoch {progress_dict['current_epoch']}/{progress_dict['total_epochs']} - "
                    f"Loss: {progress_dict['train_loss']} - Val F1: {progress_dict['val_f1']:.3f} - EER: {progress_dict['val_eer']:.3f}"
                )

        # Step 3: Train Model
        trainer = ModelTrainer(config=config, progress_callback=on_epoch_progress)
        summary = trainer.train()

        # Step 4: Quality Gate Check & Hot-Reload
        model_mgr = get_model_manager()
        saved_ckpt = summary.get("saved_checkpoint")
        if saved_ckpt and os.path.exists(saved_ckpt):
            model_mgr.load_checkpoint(saved_ckpt, mode="TRAINED_INFERENCE")

        with _training_lock:
            training_state["status"] = "COMPLETED"
            training_state["progress_percent"] = 100.0
            training_state["best_f1"] = summary["best_f1"]
            training_state["best_eer"] = summary["best_eer"]
            training_state["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            training_state["message"] = f"Training completed successfully! Best F1: {summary['best_f1']:.3f}, EER: {summary['best_eer']:.3f}"
            training_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {training_state['message']}")

    except Exception as e:
        logger.error(f"Training worker encountered error: {e}", exc_info=True)
        with _training_lock:
            training_state["status"] = "FAILED"
            training_state["error"] = str(e)
            training_state["message"] = f"Training failed: {str(e)}"
            training_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] ERROR: {str(e)}")


@router.post("/start")
async def start_training(req: StartTrainingRequest, background_tasks: BackgroundTasks):
    """
    Triggers asynchronous model training pipeline in a background thread.
    """
    global training_state

    with _training_lock:
        if training_state["status"] in ["PREPARING_DATA", "TRAINING"]:
            raise HTTPException(status_code=400, detail="Training job is already actively running.")

        # Reset state
        ds_dir = req.dataset_dir or settings.DATASET_DIR
        config = TrainingConfig(
            dataset_dir=ds_dir,
            epochs=req.epochs or 20,
            batch_size=req.batch_size or 16,
            learning_rate=req.learning_rate or 0.0001,
        )

        training_state["status"] = "PREPARING_DATA"
        training_state["current_epoch"] = 0
        training_state["total_epochs"] = config.epochs
        training_state["progress_percent"] = 0.0
        training_state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        training_state["completed_at"] = None
        training_state["error"] = None
        training_state["logs"] = [f"[{time.strftime('%H:%M:%S')}] Training job initialized by analyst."]
        training_state["history"] = []

    background_tasks.add_task(_training_worker, config)

    return {
        "status": "JOB_ACCEPTED",
        "message": "Training pipeline initiated in background worker.",
        "config": {
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "device": config.device_name,
            "dataset_dir": os.path.abspath(config.dataset_dir),
        },
    }


@router.get("/status")
async def get_training_status():
    """Returns real-time training progress, loss, metrics, and dataset status."""
    with _training_lock:
        # Check dataset presence if unknown
        if training_state["dataset_status"] == "UNKNOWN":
            val = DatasetValidator()
            rep = val.validate_dataset(settings.DATASET_DIR)
            training_state["dataset_status"] = "READY" if rep["valid_samples_count"] > 0 else "EMPTY"
            training_state["valid_samples_count"] = rep["valid_samples_count"]

        return dict(training_state)


@router.get("/logs")
async def get_training_logs():
    """Returns streaming logs from current or most recent training run."""
    with _training_lock:
        return {
            "status": training_state["status"],
            "logs": training_state["logs"][-100:],  # last 100 lines
        }
