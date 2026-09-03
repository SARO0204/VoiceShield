"""
Tests for Speaker-Disjoint Dataset Splitter and Validation.
"""

import os
import shutil
import tempfile
import pandas as pd
import pytest
from ml.data.split_dataset import split_dataset_speaker_disjoint
from scripts.generate_sample_dataset import generate_sample_dataset


def test_speaker_disjoint_split():
    temp_dir = tempfile.mkdtemp()
    try:
        data_dir = os.path.join(temp_dir, "audio")
        output_dir = os.path.join(temp_dir, "manifests")

        # Generate 6 speakers with 4 audio files each
        generate_sample_dataset(dataset_dir=data_dir, num_speakers=6, samples_per_speaker=4)

        # Run speaker-disjoint split (60% train, 20% val, 20% test)
        splits = split_dataset_speaker_disjoint(
            dataset_dir=data_dir,
            output_dir=output_dir,
            train_ratio=0.60,
            val_ratio=0.20,
            test_ratio=0.20,
            seed=42,
        )

        assert os.path.exists(os.path.join(output_dir, "train.csv"))
        assert os.path.exists(os.path.join(output_dir, "validation.csv"))
        assert os.path.exists(os.path.join(output_dir, "test.csv"))

        train_df = pd.read_csv(os.path.join(output_dir, "train.csv"))
        val_df = pd.read_csv(os.path.join(output_dir, "validation.csv"))
        test_df = pd.read_csv(os.path.join(output_dir, "test.csv"))

        train_speakers = set(train_df["speaker_id"])
        val_speakers = set(val_df["speaker_id"])
        test_speakers = set(test_df["speaker_id"])

        # Strictly 0% speaker overlap
        assert len(train_speakers.intersection(val_speakers)) == 0, "Speaker leakage in train vs val!"
        assert len(train_speakers.intersection(test_speakers)) == 0, "Speaker leakage in train vs test!"
        assert len(val_speakers.intersection(test_speakers)) == 0, "Speaker leakage in val vs test!"

    finally:
        shutil.rmtree(temp_dir)
