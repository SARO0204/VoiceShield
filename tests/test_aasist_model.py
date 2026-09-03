"""
Tests for AASIST Deepfake Voice Detector Model Architecture.
"""

import torch
import pytest
from ml.models.aasist_detector import AASISTDetector


def test_aasist_model_instantiation():
    model = AASISTDetector()
    assert model.model_name == "AASIST"
    assert model.model_version == "1.0"


def test_aasist_forward_pass_shape():
    model = AASISTDetector()
    model.eval()

    # Batch of 2, 64600 samples (~4.0375s at 16kHz)
    x = torch.randn(2, 64600)
    with torch.no_grad():
        out = model(x)

    # Expected shape (2, 2) corresponding to logits for [bonafide, spoof]
    assert out.shape == (2, 2)
    assert not torch.isnan(out).any()


def test_aasist_predict_proba():
    model = AASISTDetector()
    x = torch.randn(1, 64600)
    res = model.predict_proba(x)

    assert "bonafide" in res
    assert "spoof" in res
    assert 0.0 <= res["bonafide"] <= 1.0
    assert 0.0 <= res["spoof"] <= 1.0
    assert pytest.approx(res["bonafide"] + res["spoof"], 0.01) == 1.0
