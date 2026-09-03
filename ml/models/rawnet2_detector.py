"""
RawNet2 Detector Adapter.
Modular voice anti-spoofing detector based on RawNet2 architecture.
"""

import torch
import torch.nn as nn
from ml.models.base_detector import BaseVoiceDetector


class RawNet2Detector(BaseVoiceDetector):
    """
    RawNet2 voice anti-spoofing detector.
    Processes raw audio waveforms with SincConv frontend and GRU/Residual blocks.
    """

    def __init__(
        self,
        model_name: str = "RawNet2",
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
        self.conv = nn.Sequential(
            nn.Conv1d(1, 128, kernel_size=251, stride=3, padding=125),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.MaxPool1d(3),
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2),
            nn.MaxPool1d(3),
            nn.Conv1d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm1d(512),
            nn.LeakyReLU(0.2),
        )
        self.gru = nn.GRU(512, 256, num_layers=2, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(512, 128),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            x = x.unsqueeze(1)
        feat = self.conv(x)  # (B, 512, T')
        feat = feat.transpose(1, 2)  # (B, T', 512)
        out, _ = self.gru(feat)
        pooled = torch.mean(out, dim=1)  # (B, 512)
        logits = self.fc(pooled)
        return logits
