"""
Training and Hardware Configuration for VoiceShield ML Pipeline.
Supports automated GPU / MPS / CPU detection and hardware-tuned defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import torch


@dataclass
class TrainingConfig:
    """Configuration for ML model training and evaluation."""

    # Model architecture
    model_name: str = "AASIST"
    model_version: str = "1.0"
    num_classes: int = 2
    sample_rate: int = 16000
    expected_samples: int = 64600  # ~4.0375s

    # Paths
    dataset_dir: str = "./datasets"
    manifest_dir: str = "./data/manifests"
    checkpoint_dir: str = "./checkpoints"
    model_dir: str = "./models"
    reports_dir: str = "./reports"

    # Optimization
    epochs: int = 20
    learning_rate: float = 0.0001
    weight_decay: float = 0.0001
    lr_scheduler_step: int = 5
    lr_scheduler_gamma: float = 0.5
    gradient_clip_norm: float = 3.0
    early_stopping_patience: int = 5

    # Hardware & Batching
    device_name: str = "auto"
    batch_size: int = 16
    eval_batch_size: int = 16
    num_workers: int = 0  # 0 for Windows multiprocessing safety
    mixed_precision: bool = True
    seed: int = 42

    # Thresholds
    classification_threshold: float = 0.50
    uncertainty_min: float = 0.45
    uncertainty_max: float = 0.55

    def __post_init__(self):
        # Auto-detect best compute device: CUDA -> MPS -> CPU
        if self.device_name == "auto":
            if torch.cuda.is_available():
                self.device_name = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device_name = "mps"
            else:
                self.device_name = "cpu"

        # Adapt batch size if running on CPU to prevent slowdown
        if self.device_name == "cpu" and self.batch_size > 8:
            self.batch_size = 4
            self.eval_batch_size = 4
            self.mixed_precision = False

        # Ensure output directories exist
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    @property
    def device(self) -> torch.device:
        return torch.device(self.device_name)

    def get_hardware_description(self) -> Dict[str, Any]:
        """Returns human-readable hardware metadata."""
        desc = {
            "device": self.device_name,
            "device_label": "CPU fallback",
            "gpu_name": None,
            "gpu_count": 0,
            "cuda_version": None,
            "is_gpu_available": False,
        }
        if self.device_name == "cuda" and torch.cuda.is_available():
            desc["device_label"] = "NVIDIA CUDA GPU"
            desc["gpu_name"] = torch.cuda.get_device_name(0)
            desc["gpu_count"] = torch.cuda.device_count()
            desc["cuda_version"] = torch.version.cuda
            desc["is_gpu_available"] = True
        elif self.device_name == "mps":
            desc["device_label"] = "Apple Silicon MPS"
            desc["is_gpu_available"] = True
        return desc
