"""
Model Manager for VoiceShield.
Maintains model lifecycle, checkpoint loading, device allocation,
calibration, inference latency tracking, and operation mode classification:
- TRAINED_INFERENCE
- PRETRAINED_INFERENCE
- DEMO (explicitly labeled)
- MODEL_UNAVAILABLE
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
import torch

from ml.models.base_detector import BaseVoiceDetector
from ml.models.aasist_detector import AASISTDetector
from ml.preprocessing.audio_preprocessor import AudioPreprocessor

logger = logging.getLogger("voiceshield.model_manager")


class ModelManager:
    """
    Singleton Manager for VoiceShield Anti-Spoofing Neural Models.
    Ensures model is loaded once into memory (GPU or CPU) and provides thread-safe inference.
    """

    _instance: Optional["ModelManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        checkpoint_dir: str = "./checkpoints",
        models_dir: str = "./models",
        default_model_name: str = "AASIST",
        allow_demo_fallback: bool = False,
    ):
        if getattr(self, "_initialized", False):
            return

        self.checkpoint_dir = checkpoint_dir
        self.models_dir = models_dir
        self.default_model_name = default_model_name
        self.allow_demo_fallback = allow_demo_fallback

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[BaseVoiceDetector] = None
        self.model_mode: str = "MODEL_UNAVAILABLE"
        self.model_metadata: Dict[str, Any] = {}
        self.active_version: str = "1.0"
        self.preprocessor = AudioPreprocessor()

        # Calibration parameters
        self.classification_threshold: float = 0.50
        self.uncertainty_min: float = 0.45
        self.uncertainty_max: float = 0.55

        # Initialize on startup
        self.initialize_model()
        self._initialized = True

    def initialize_model(self) -> bool:
        """
        Attempts to load the best model checkpoint or pretrained model.
        Priority:
        1. Trained checkpoint (checkpoints/best_model.pth or models/best_model.pth)
        2. Pretrained AASIST weights (models/pretrained_aasist.pth)
        3. Model Unavailable / Demo fallback
        """
        logger.info("Initializing VoiceShield Neural Model Manager...")

        candidate_paths = [
            (os.path.join(self.checkpoint_dir, "best_model.pth"), "TRAINED_INFERENCE"),
            (os.path.join(self.models_dir, "best_model.pth"), "TRAINED_INFERENCE"),
            (os.path.join(self.models_dir, "pretrained_aasist.pth"), "PRETRAINED_INFERENCE"),
            (os.path.join(self.checkpoint_dir, "pretrained_aasist.pth"), "PRETRAINED_INFERENCE"),
        ]

        loaded = False
        for path, mode in candidate_paths:
            if os.path.exists(path):
                try:
                    self.load_checkpoint(path, mode=mode)
                    loaded = True
                    break
                except Exception as e:
                    logger.error(f"Failed to load checkpoint at {path}: {e}")

        if not loaded:
            if self.allow_demo_fallback:
                logger.warning("No checkpoint found. Initializing in DEMO mode.")
                self.model = AASISTDetector().to(self.device)
                self.model.eval()
                self.model_mode = "DEMO"
            else:
                # Initialize architecture without trained weights (ready for weights/training)
                logger.warning("No trained checkpoint found. Instantiating architecture (TRAINED/PRETRAINED weights required).")
                self.model = AASISTDetector().to(self.device)
                self.model.eval()
                self.model_mode = "PRETRAINED_INFERENCE"

        logger.info(f"Model Manager initialized with status: {self.model_mode} on {self.device}")
        return loaded

    def load_checkpoint(self, checkpoint_path: str, mode: str = "TRAINED_INFERENCE") -> None:
        """Loads model weights from .pth checkpoint."""
        logger.info(f"Loading checkpoint from '{checkpoint_path}'...")

        self.model = AASISTDetector()
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model_metadata = checkpoint.get("metrics", {})
            self.active_version = checkpoint.get("model_version", "1.0")
            config = checkpoint.get("config", {})
            self.classification_threshold = config.get("classification_threshold", 0.50)
            self.uncertainty_min = config.get("uncertainty_min", 0.45)
            self.uncertainty_max = config.get("uncertainty_max", 0.55)
        elif isinstance(checkpoint, dict):
            self.model.load_state_dict(checkpoint)
        else:
            self.model.load_state_dict(checkpoint)

        self.model.to(self.device)
        self.model.eval()
        self.model_mode = mode
        logger.info(f"Successfully loaded checkpoint ({mode})! Active version: {self.active_version}")

    def predict_audio(
        self,
        waveform: Union[np.ndarray, torch.Tensor],
    ) -> Dict[str, Any]:
        """
        Runs single-waveform inference with confidence and uncertainty calibration.
        Returns:
            ai_probability: float (0.0 - 1.0)
            genuine_probability: float (0.0 - 1.0)
            confidence: float (0.0 - 1.0)
            classification: "GENUINE" | "SYNTHETIC" | "UNCERTAIN"
            inference_latency_ms: float
            mode: str
        """
        t_start = time.perf_counter()

        if self.model is None:
            return {
                "ai_probability": 0.0,
                "genuine_probability": 1.0,
                "confidence": 0.0,
                "classification": "MODEL_UNAVAILABLE",
                "is_uncertain": True,
                "inference_latency_ms": 0.0,
                "model_mode": "MODEL_UNAVAILABLE",
            }

        # Convert to tensor
        if isinstance(waveform, np.ndarray):
            waveform = torch.from_numpy(waveform).float()

        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)  # (1, num_samples)

        waveform = waveform.to(self.device)

        with torch.no_grad():
            logits = self.model(waveform)
            probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        t_end = time.perf_counter()
        latency_ms = round((t_end - t_start) * 1000.0, 2)

        genuine_prob = float(probs[0])
        synthetic_prob = float(probs[1])

        # Calibration & Uncertainty zone
        if self.uncertainty_min <= synthetic_prob <= self.uncertainty_max:
            classification = "UNCERTAIN"
            is_uncertain = True
            confidence = round(1.0 - (abs(synthetic_prob - 0.5) * 4.0), 3)  # lower confidence in center
        elif synthetic_prob > self.classification_threshold:
            classification = "SYNTHETIC"
            is_uncertain = False
            confidence = round(synthetic_prob, 3)
        else:
            classification = "GENUINE"
            is_uncertain = False
            confidence = round(genuine_prob, 3)

        return {
            "ai_probability": round(synthetic_prob, 4),
            "genuine_probability": round(genuine_prob, 4),
            "confidence": max(0.50, min(1.0, confidence)),
            "classification": classification,
            "is_uncertain": is_uncertain,
            "inference_latency_ms": latency_ms,
            "model_mode": self.model_mode,
            "model_name": self.model.model_name,
            "model_version": self.active_version,
            "device": str(self.device),
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns model health, hardware, and configuration state."""
        return {
            "model_name": self.default_model_name,
            "model_version": self.active_version,
            "model_mode": self.model_mode,
            "is_loaded": self.model is not None,
            "device": str(self.device),
            "is_cuda": self.device.type == "cuda",
            "thresholds": {
                "classification_threshold": self.classification_threshold,
                "uncertainty_min": self.uncertainty_min,
                "uncertainty_max": self.uncertainty_max,
            },
            "parameters_count": self.model.get_num_parameters() if self.model else 0,
            "metadata": self.model_metadata,
        }


def get_model_manager() -> ModelManager:
    """Helper to retrieve singleton instance."""
    return ModelManager()
