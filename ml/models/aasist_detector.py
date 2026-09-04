"""
AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks.
State-of-the-art neural architecture for voice deepfake, clone, and synthetic speech detection.
Implements:
- SincNet parametric bandpass filter frontend
- Residual Spectro-Temporal Feature Encoder
- Spectral Graph Attention Module (GAT)
- Temporal Graph Attention Module (GAT)
- Integrated Graph Pooling & Readout Classifier
"""

import math
from typing import Dict, Any, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from ml.models.base_detector import BaseVoiceDetector


class SincConv(nn.Module):
    """
    Sinc-based convolution layer for raw audio frontend.
    Learns bandpass filters with parameterized cutoff frequencies.
    """

    @classmethod
    def to_mel(cls, hz: float) -> float:
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    @classmethod
    def to_hz(cls, mel: float) -> float:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    def __init__(
        self,
        out_channels: int = 70,
        kernel_size: int = 129,
        sample_rate: int = 16000,
        min_low_hz: float = 0.0,
        min_band_hz: float = 50.0,
    ):
        super().__init__()
        if kernel_size % 2 == 0:
            kernel_size += 1

        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.sample_rate = sample_rate
        self.min_low_hz = min_low_hz
        self.min_band_hz = min_band_hz

        # Initialize filterbanks along Mel scale
        low_hz = 0.0
        high_hz = sample_rate / 2.0 - (min_low_hz + min_band_hz)

        mel = np.linspace(self.to_mel(low_hz), self.to_mel(high_hz), out_channels + 1)
        hz = self.to_hz(mel)

        self.low_hz_ = nn.Parameter(torch.Tensor(hz[:-1]).view(-1, 1))
        self.band_hz_ = nn.Parameter(torch.Tensor(np.diff(hz)).view(-1, 1))

        # Hamming window
        n_lin = torch.linspace(0, (kernel_size / 2) - 1, steps=int((kernel_size / 2)))
        window = 0.54 - 0.46 * torch.cos(2 * math.pi * n_lin / kernel_size)
        full_window = torch.cat([window, torch.tensor([1.0]), window.flip(0)])
        self.register_buffer("window_", full_window)

        n_ = 2 * math.pi * torch.arange(-(kernel_size - 1) / 2.0, (kernel_size - 1) / 2.0 + 1) / sample_rate
        half_k = int((kernel_size - 1) / 2)
        n_left = n_[:half_k] / 2.0
        n_right = n_[half_k + 1:] / 2.0
        self.register_buffer("n_left", n_left)
        self.register_buffer("n_right", n_right)

    def forward(self, waveforms: torch.Tensor) -> torch.Tensor:
        """
        Args:
            waveforms (torch.Tensor): Shape (batch_size, 1, num_samples) or (batch_size, num_samples)
        Returns:
            torch.Tensor: Filtered features of shape (batch_size, out_channels, time_frames)
        """
        if waveforms.dim() == 2:
            waveforms = waveforms.unsqueeze(1)

        low = self.min_low_hz + torch.abs(self.low_hz_)
        high = torch.clamp(low + self.min_band_hz + torch.abs(self.band_hz_), self.min_low_hz, self.sample_rate / 2.0)
        band = high - low

        # Left side
        f_low_left = torch.matmul(low, (self.n_left * 2.0).view(1, -1))
        f_high_left = torch.matmul(high, (self.n_left * 2.0).view(1, -1))
        band_pass_left = (torch.sin(f_high_left) - torch.sin(f_low_left)) / (self.n_left.view(1, -1) + 1e-12)

        # Center element
        band_pass_center = (2.0 * band).view(-1, 1)

        # Right side
        f_low_right = torch.matmul(low, (self.n_right * 2.0).view(1, -1))
        f_high_right = torch.matmul(high, (self.n_right * 2.0).view(1, -1))
        band_pass_right = (torch.sin(f_high_right) - torch.sin(f_low_right)) / (self.n_right.view(1, -1) + 1e-12)

        band_pass = torch.cat([band_pass_left, band_pass_center, band_pass_right], dim=1)
        band_pass = band_pass / (2.0 * band.view(-1, 1) + 1e-8)

        # Windowing
        band_pass = band_pass * self.window_.view(1, -1)
        filters = band_pass.view(self.out_channels, 1, self.kernel_size)

        return F.conv1d(waveforms, filters, stride=1, padding=self.kernel_size // 2)


class ResBlock(nn.Module):
    """Residual convolutional block with SeLU activations and 2D MaxPool."""

    def __init__(self, in_channels: int, out_channels: int, pool_size: tuple = (2, 2)):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.selu = nn.SELU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

        self.pool = nn.MaxPool2d(pool_size) if pool_size else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.shortcut(x)
        x = self.selu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        x = self.selu(x + res)
        x = self.pool(x)
        return x


class GraphAttentionLayer(nn.Module):
    """
    Graph Attention Network (GAT) layer for spectro-temporal node modeling.
    """

    def __init__(self, in_features: int, out_features: int, alpha: float = 0.2):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.W = nn.Linear(in_features, out_features, bias=False)
        self.a = nn.Linear(2 * out_features, 1, bias=False)
        self.leakyrelu = nn.LeakyReLU(alpha)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h: Node feature tensor of shape (batch_size, num_nodes, in_features)
        Returns:
            torch.Tensor: Updated node tensor (batch_size, num_nodes, out_features)
        """
        B, N, _ = h.shape
        Wh = self.W(h)  # (B, N, out_features)

        # Preserve pairwise additive attention while bounding its peak memory use.
        query_chunk_size = 64
        output_chunks = []
        keys = Wh.unsqueeze(1)
        for start in range(0, N, query_chunk_size):
            queries = Wh[:, start : start + query_chunk_size].unsqueeze(2)
            all_combinations = torch.cat(
                [queries.expand(-1, -1, N, -1), keys.expand(-1, queries.shape[1], -1, -1)],
                dim=-1,
            )
            scores = self.leakyrelu(self.a(all_combinations).squeeze(-1))
            attention = F.softmax(scores, dim=-1)
            output_chunks.append(torch.bmm(attention, Wh))

        h_prime = torch.cat(output_chunks, dim=1)
        return F.elu(h_prime)


class AASISTDetector(BaseVoiceDetector):
    """
    Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks (AASIST).
    Full PyTorch model processing raw 16kHz audio waveforms directly into genuine/spoof logits.
    """

    def __init__(
        self,
        model_name: str = "AASIST",
        model_version: str = "1.0",
        sample_rate: int = 16000,
        expected_samples: int = 64600,
        sinc_channels: int = 70,
        sinc_kernel: int = 129,
        num_classes: int = 2,
    ):
        super().__init__(
            model_name=model_name,
            model_version=model_version,
            sample_rate=sample_rate,
            expected_samples=expected_samples,
        )

        # 1. SincNet Frontend Filterbank
        self.sinc_conv = SincConv(
            out_channels=sinc_channels,
            kernel_size=sinc_kernel,
            sample_rate=sample_rate,
        )
        self.sinc_pool = nn.MaxPool1d(kernel_size=3, stride=3)
        self.sinc_bn = nn.BatchNorm1d(sinc_channels)
        self.selu = nn.SELU(inplace=True)

        # 2. Residual Spectro-Temporal Feature Encoder
        # Input to 2D conv: (B, 1, Freq=70, Time)
        self.res_block1 = ResBlock(1, 32, pool_size=(2, 3))
        self.res_block2 = ResBlock(32, 32, pool_size=(2, 3))
        self.res_block3 = ResBlock(32, 64, pool_size=(2, 2))
        self.res_block4 = ResBlock(64, 64, pool_size=(2, 2))

        # 3. Spectral & Temporal Graph Modules
        hidden_dim = 64
        self.proj_spectral = nn.Linear(64, hidden_dim)
        self.gat_spectral = GraphAttentionLayer(hidden_dim, hidden_dim)

        self.proj_temporal = nn.Linear(64, hidden_dim)
        self.gat_temporal = GraphAttentionLayer(hidden_dim, hidden_dim)

        # 4. Readout and Classifier
        self.fc_pool = nn.Sequential(
            nn.Linear(hidden_dim * 4, 128),
            nn.SELU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.SELU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x (torch.Tensor): Raw waveform tensor of shape (B, num_samples) or (B, 1, num_samples)
        Returns:
            torch.Tensor: Logits tensor of shape (B, 2) [0: bonafide, 1: spoof]
        """
        if x.dim() == 2:
            x = x.unsqueeze(1)  # (B, 1, T)

        # 1. SincNet frontend
        sinc_feats = self.sinc_conv(x)  # (B, 70, T')
        sinc_feats = self.sinc_pool(sinc_feats)
        sinc_feats = self.sinc_bn(sinc_feats)
        sinc_feats = torch.abs(sinc_feats)  # Absolute magnitude

        # 2. ResNet Encoder
        x_res = sinc_feats.unsqueeze(1)  # (B, 1, F=70, T')
        x_res = self.res_block1(x_res)
        x_res = self.res_block2(x_res)
        x_res = self.res_block3(x_res)
        x_res = self.res_block4(x_res)  # (B, C=64, F', T')

        B, C, F_dim, T_dim = x_res.shape

        # 3. Spectral Graph Attention
        # Collapse time dimension to form Spectral Nodes (B, F_dim, C)
        x_spec = torch.mean(x_res, dim=-1).transpose(1, 2)  # (B, F_dim, C)
        x_spec = self.proj_spectral(x_spec)
        x_spec = self.gat_spectral(x_spec)  # (B, F_dim, C)

        # Spectral Graph Pooling (mean + max)
        spec_mean = torch.mean(x_spec, dim=1)  # (B, C)
        spec_max = torch.max(x_spec, dim=1)[0]  # (B, C)

        # 4. Temporal Graph Attention
        # Collapse freq dimension to form Temporal Nodes (B, T_dim, C)
        x_temp = torch.mean(x_res, dim=2).transpose(1, 2)  # (B, T_dim, C)
        x_temp = self.proj_temporal(x_temp)
        x_temp = self.gat_temporal(x_temp)  # (B, T_dim, C)

        # Temporal Graph Pooling (mean + max)
        temp_mean = torch.mean(x_temp, dim=1)  # (B, C)
        temp_max = torch.max(x_temp, dim=1)[0]  # (B, C)

        # 5. Integrated Graph Fusion
        integrated = torch.cat([spec_mean, spec_max, temp_mean, temp_max], dim=-1)  # (B, 64 * 4)

        # 6. Readout Classifier
        logits = self.fc_pool(integrated)  # (B, 2)
        return logits
