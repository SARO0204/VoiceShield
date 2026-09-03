"""
Wav2Vec2 Voice Spoofing Detector Adapter.
Future-compatible adapter for self-supervised speech representation deepfake detection.
"""

import torch
import torch.nn as nn
from typing import Optional
from ml.models.base_detector import BaseVoiceDetector


class Wav2Vec2Detector(BaseVoiceDetector):
    """
    Wav2Vec2-based voice spoofing detector adapter.
    Processes 16kHz audio waveforms through 1D convolutional feature encoder and classification head.
    """

    def __init__(
        self,
        model_name: str = "Wav2Vec2-AntiSpoof",
        model_version: str = "1.0",
        sample_rate: int = 16000,
        expected_samples: int = 64600,
        num_classes: int = 2,
    ):
        super().__init__(
            model_name=model_name,
            model_version=model_version,
            sample_rate=sample_rate,
            expected_samples=expected_samples,
        )

        # 1D Temporal CNN Feature Extractor
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=10, stride=5, padding=2, bias=False),
            nn.BatchNorm1d(64),
            nn.GELU(),
            nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Conv1d(128, 256, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm1d(256),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(64),
        )

        # Classifier readout
        self.classifier = nn.Sequential(
            nn.Linear(256 * 64, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            x = x.unsqueeze(1)
        feat = self.feature_extractor(x)
        flat = feat.view(feat.size(0), -1)
        logits = self.classifier(flat)
        return logits
