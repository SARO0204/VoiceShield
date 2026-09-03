"""
Tests for AudioPreprocessor.
"""

import numpy as np
import pytest
from ml.preprocessing.audio_preprocessor import AudioPreprocessor


def test_audio_preprocessor_initialization():
    prep = AudioPreprocessor(target_sample_rate=16000, target_duration_sec=4.0375)
    assert prep.target_sample_rate == 16000
    assert prep.target_samples == 64600


def test_resample_and_normalize():
    prep = AudioPreprocessor(target_sample_rate=16000)
    # 1 second of 8kHz sine wave
    t = np.linspace(0, 1.0, 8000, endpoint=False)
    raw = (np.sin(2 * np.pi * 440 * t) * 0.8).astype(np.float32)

    resampled = prep.resample(raw, orig_sr=8000)
    assert len(resampled) == 16000

    normalized = prep.normalize(resampled)
    assert np.max(np.abs(normalized)) <= 0.96


def test_pad_or_truncate():
    prep = AudioPreprocessor(target_sample_rate=16000, target_duration_sec=4.0375)
    # Short audio
    short_audio = np.ones(1000, dtype=np.float32) * 0.5
    padded = prep.pad_or_truncate(short_audio, 64600)
    assert len(padded) == 64600

    # Long audio
    long_audio = np.ones(80000, dtype=np.float32) * 0.5
    truncated = prep.pad_or_truncate(long_audio, 64600)
    assert len(truncated) == 64600


def test_chunk_audio():
    prep = AudioPreprocessor(target_sample_rate=16000)
    # 8 seconds of audio
    audio_8s = np.zeros(16000 * 8, dtype=np.float32)
    chunks = prep.chunk_audio(audio_8s, chunk_size_sec=4.0, hop_size_sec=2.0)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c) == 64000
