"""
WavLM / Self-Supervised Speech Detector Adapter.
Modular voice anti-spoofing detector leveraging self-supervised speech representations.
"""

import torch
import torch.nn as nn
from ml.models.base_detector import BaseVoiceDetector


class WavLMDetector(BaseVoiceDetector):
    """
    Self-Supervised WavLM / Wav2Vec2 adapter detector.
    Extracts acoustic embeddings and classifies through an attention pooling classification head.
    """

    def __init__(
        self,
        model_name: str = "WavLM-Detector",
        model_version: str = "1.0",
        sample_rate: int = 16000,
        expected_samples: int = 64600,
        num_classes: int = 2,
        embedding_dim: int = 256,
    ):
        super().__init__(
            model_name=model_name,
            model_version=model_version,
            sample_rate=sample_rate,
            expected_samples=expected_samples,
        )
        # Lightweight convolutional projection when SSL backbone is in feature extraction mode
        self.frontend = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=10, stride=5, padding=2),
            nn.BatchNorm1d(64),
            nn.GELU(),
            nn.Conv1d(64, 128, kernel_size=8, stride=4, padding=2),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Conv1d(128, embedding_dim, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm1d(embedding_dim),
            nn.GELU(),
        )
        self.attn = nn.Sequential(
            nn.Linear(embedding_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            x = x.unsqueeze(1)
        feat = self.frontend(x)  # (B, D, T')
        feat_t = feat.transpose(1, 2)  # (B, T', D)
        weights = torch.softmax(self.attn(feat_t), dim=1)  # (B, T', 1)
        pooled = torch.sum(feat_t * weights, dim=1)  # (B, D)
        logits = self.classifier(pooled)
        return logits
