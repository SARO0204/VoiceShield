"""
Base Voice Spoofing Detector Interface.
Provides an abstract base class for all neural anti-spoofing detectors in VoiceShield.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Union
import torch
import torch.nn as nn
import numpy as np


class BaseVoiceDetector(nn.Module, ABC):
    """
    Abstract base class for voice anti-spoofing and deepfake detectors.
    Standardized 2-class output:
    Index 0: Genuine / Bonafide speech
    Index 1: Synthetic / Voice-cloned / Spoofed speech
    """

    def __init__(
        self,
        model_name: str = "base_detector",
        model_version: str = "1.0",
        sample_rate: int = 16000,
        expected_samples: int = 64600,
    ):
        super().__init__()
        self.model_name = model_name
        self.model_version = model_version
        self.sample_rate = sample_rate
        self.expected_samples = expected_samples

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x (torch.Tensor): Audio waveform tensor of shape (batch_size, num_samples)
        Returns:
            torch.Tensor: Logits tensor of shape (batch_size, 2)
        """
        pass

    def get_num_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata dictionary."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "sample_rate": self.sample_rate,
            "expected_samples": self.expected_samples,
            "trainable_parameters": self.get_num_parameters(),
        }

    def predict_probabilities(
        self,
        x: Union[torch.Tensor, np.ndarray],
        device: Optional[torch.device] = None,
    ) -> Tuple[float, float]:
        """
        Run inference on a single audio sample and return (genuine_prob, synthetic_prob).
        """
        self.eval()
        dev = device or next(self.parameters()).device

        if isinstance(x, np.ndarray):
            x = torch.from_numpy(x).float()

        if x.dim() == 1:
            x = x.unsqueeze(0)  # (1, num_samples)

        x = x.to(dev)

        with torch.no_grad():
            logits = self.forward(x)  # (1, 2)
            probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        genuine_prob = float(probs[0])
        synthetic_prob = float(probs[1])
        return genuine_prob, synthetic_prob

    def predict_proba(
        self,
        x: Union[torch.Tensor, np.ndarray],
        device: Optional[torch.device] = None,
    ) -> Dict[str, float]:
        """
        Run inference and return dict with 'bonafide' and 'spoof' probabilities.
        """
        genuine, synthetic = self.predict_probabilities(x, device)
        return {"bonafide": genuine, "spoof": synthetic}

