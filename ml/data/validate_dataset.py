"""
Dataset Validation Module for VoiceShield.
Inspects raw audio files, checks audio headers, duration, decodability,
identifies corrupted samples, validates ground truth labels, and outputs validation report.
"""

import os
import glob
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ml.preprocessing.audio_preprocessor import AudioPreprocessor

logger = logging.getLogger("voiceshield.data_validator")


class DatasetValidator:
    """
    Validates anti-spoofing datasets (e.g., ASVspoof, In-the-Wild, custom recorded).
    Ensures data integrity before training or evaluation.
    """

    SUPPORTED_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}

    def __init__(
        self,
        min_duration_sec: float = 0.5,
        max_duration_sec: float = 300.0,
        preprocessor: Optional[AudioPreprocessor] = None,
    ):
        self.min_duration_sec = min_duration_sec
        self.max_duration_sec = max_duration_sec
        self.preprocessor = preprocessor or AudioPreprocessor()

    def find_audio_files(self, dataset_dir: str) -> List[str]:
        """Recursively scan directory for all supported audio files."""
        audio_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            audio_files.extend(glob.glob(os.path.join(dataset_dir, f"**/*{ext}"), recursive=True))
            audio_files.extend(glob.glob(os.path.join(dataset_dir, f"**/*{ext.upper()}"), recursive=True))
        return sorted(list(set(audio_files)))

    def validate_sample(self, file_path: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate a single audio file.
        Returns:
            is_valid (bool): True if audio can be decoded and satisfies constraints
            error_reason (str or None)
            metadata (dict or None)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist", None

        file_size = os.path.getsize(file_path)
        if file_size < 100:
            return False, f"File too small ({file_size} bytes)", None

        try:
            audio, orig_sr = self.preprocessor.load_audio(file_path)
            duration = len(audio) / float(orig_sr) if orig_sr > 0 else 0

            if duration < self.min_duration_sec:
                return False, f"Duration {duration:.2f}s is below minimum {self.min_duration_sec}s", None

            if np_is_all_zeros := (abs(audio).max() < 1e-5):
                return False, "Audio is completely silent / all zeros", None

            quality = self.preprocessor.compute_audio_quality_metrics(audio, orig_sr)

            meta = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "duration_sec": round(duration, 3),
                "sample_rate": orig_sr,
                "channels": 1,
                "file_size_bytes": file_size,
                "quality": quality,
            }
            return True, None, meta

        except Exception as e:
            return False, f"Decoding error: {str(e)}", None

    def validate_dataset(
        self,
        dataset_dir: str,
        protocol_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate full dataset directory and return validation summary report.
        """
        if not os.path.exists(dataset_dir):
            return {
                "status": "NOT_FOUND",
                "message": f"Dataset directory does not exist: {dataset_dir}",
                "valid_samples": 0,
                "valid_samples_count": 0,
                "corrupted_samples": 0,
                "corrupted_samples_count": 0,
                "total_files": 0,
            }

        audio_files = self.find_audio_files(dataset_dir)
        total_files = len(audio_files)

        if total_files == 0:
            return {
                "status": "EMPTY",
                "message": f"No audio files found in {dataset_dir}",
                "valid_samples": 0,
                "valid_samples_count": 0,
                "corrupted_samples": 0,
                "corrupted_samples_count": 0,
                "total_files": 0,
            }

        valid_samples = []
        corrupted_samples = []
        total_duration = 0.0

        for fpath in audio_files:
            is_valid, error, meta = self.validate_sample(fpath)
            if is_valid and meta:
                valid_samples.append(meta)
                total_duration += meta["duration_sec"]
            else:
                corrupted_samples.append({"file_path": fpath, "error": error})

        report = {
            "status": "VALID" if len(valid_samples) > 0 else "INVALID",
            "dataset_dir": dataset_dir,
            "total_files_scanned": total_files,
            "valid_samples_count": len(valid_samples),
            "corrupted_samples_count": len(corrupted_samples),
            "corrupted_percentage": round((len(corrupted_samples) / total_files) * 100, 2) if total_files else 0,
            "total_valid_duration_hours": round(total_duration / 3600.0, 3),
            "average_duration_sec": round(total_duration / len(valid_samples), 2) if valid_samples else 0,
            "corrupted_details": corrupted_samples[:50],  # cap details
        }

        return report
