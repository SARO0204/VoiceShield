"""
Speaker-Disjoint Dataset Splitter for VoiceShield.
Prevents data leakage by ensuring that all audio samples from any single speaker
exist exclusively in either Train, Validation, or Test split, with 0% speaker overlap.
Generates standardized manifest CSVs: train.csv, validation.csv, test.csv.
"""

import os
import csv
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("voiceshield.dataset_splitter")


class DatasetSplitter:
    """
    Splits anti-spoofing datasets with strict speaker-disjoint isolation.
    """

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ):
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-4, "Ratios must sum to 1.0"
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def extract_speaker_and_label(
        self,
        file_path: str,
        label_hint: Optional[str] = None,
        speaker_hint: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Infers (speaker_id, label, attack_type) from file path or directory structure.
        Standard labels: 'bonafide' (genuine) or 'spoof' (synthetic/cloned).
        """
        path_lower = file_path.lower().replace("\\", "/")
        file_name = os.path.basename(file_path)

        # 1. Determine Label
        if label_hint:
            label = "bonafide" if label_hint.lower() in ("bonafide", "genuine", "real", "0") else "spoof"
        elif any(k in path_lower for k in ["/bonafide/", "/real/", "/genuine/", "bonafide_", "genuine_"]):
            label = "bonafide"
        elif any(k in path_lower for k in ["/spoof/", "/fake/", "/synthetic/", "/cloned/", "spoof_", "fake_"]):
            label = "spoof"
        else:
            label = "spoof" if "spoof" in file_name.lower() else "bonafide"

        # 2. Determine Speaker ID
        if speaker_hint:
            speaker_id = speaker_hint
        else:
            # Extract speaker if path is structured: .../speaker_id/audio.wav
            parts = file_path.replace("\\", "/").split("/")
            if len(parts) >= 2 and parts[-2] not in ("bonafide", "spoof", "real", "fake", "audio", "wav"):
                speaker_id = parts[-2]
            else:
                # Infer from filename prefix (e.g. LA_0001_A01 -> LA_0001)
                base = os.path.splitext(file_name)[0]
                tokens = base.split("_")
                speaker_id = tokens[0] if len(tokens) > 1 else f"spk_{hash(base) % 1000:04d}"

        # 3. Determine Attack Type (if spoof)
        attack_type = "-"
        if label == "spoof":
            for atk in ["tts", "vc", "replay", "cloning", "neural", "diffwave", "vits", "elevenlabs"]:
                if atk in path_lower:
                    attack_type = atk.upper()
                    break
            if attack_type == "-":
                attack_type = "AI_CLONE"

        return speaker_id, label, attack_type

    def create_speaker_disjoint_splits(
        self,
        samples: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Group samples by speaker and allocate full speaker sets into Train/Val/Test.
        Ensures 0 speaker overlap across splits.
        """
        random.seed(self.seed)

        speaker_to_samples = defaultdict(list)
        for s in samples:
            speaker_id = s.get("speaker_id") or self.extract_speaker_and_label(s["audio_path"])[0]
            s["speaker_id"] = speaker_id
            speaker_to_samples[speaker_id].append(s)

        speakers = list(speaker_to_samples.keys())
        random.shuffle(speakers)

        total_samples = len(samples)
        target_train_count = int(total_samples * self.train_ratio)
        target_val_count = int(total_samples * self.val_ratio)

        train_speakers = set()
        val_speakers = set()
        test_speakers = set()

        curr_train_count = 0
        curr_val_count = 0

        for spk in speakers:
            spk_count = len(speaker_to_samples[spk])
            if curr_train_count + spk_count <= target_train_count or (not train_speakers):
                train_speakers.add(spk)
                curr_train_count += spk_count
            elif curr_val_count + spk_count <= target_val_count or (not val_speakers):
                val_speakers.add(spk)
                curr_val_count += spk_count
            else:
                test_speakers.add(spk)

        # Build final split lists
        train_samples = [s for spk in train_speakers for s in speaker_to_samples[spk]]
        val_samples = [s for spk in val_speakers for s in speaker_to_samples[spk]]
        test_samples = [s for spk in test_speakers for s in speaker_to_samples[spk]]

        # Safety verification: ensure disjoint speakers
        overlap_train_val = train_speakers.intersection(val_speakers)
        overlap_train_test = train_speakers.intersection(test_speakers)
        overlap_val_test = val_speakers.intersection(test_speakers)
        assert len(overlap_train_val) == 0, f"Speaker leakage between Train & Val: {overlap_train_val}"
        assert len(overlap_train_test) == 0, f"Speaker leakage between Train & Test: {overlap_train_test}"
        assert len(overlap_val_test) == 0, f"Speaker leakage between Val & Test: {overlap_val_test}"

        stats = {
            "total_speakers": len(speakers),
            "train_speakers_count": len(train_speakers),
            "val_speakers_count": len(val_speakers),
            "test_speakers_count": len(test_speakers),
            "train_samples_count": len(train_samples),
            "val_samples_count": len(val_samples),
            "test_samples_count": len(test_samples),
            "train_bonafide": sum(1 for s in train_samples if s["label"] == "bonafide"),
            "train_spoof": sum(1 for s in train_samples if s["label"] == "spoof"),
            "val_bonafide": sum(1 for s in val_samples if s["label"] == "bonafide"),
            "val_spoof": sum(1 for s in val_samples if s["label"] == "spoof"),
            "test_bonafide": sum(1 for s in test_samples if s["label"] == "bonafide"),
            "test_spoof": sum(1 for s in test_samples if s["label"] == "spoof"),
            "speaker_leakage_detected": False,
        }

        return train_samples, val_samples, test_samples, stats

    split = create_speaker_disjoint_splits

    def export_manifests(
        self,
        output_dir: str,
        train_samples: List[Dict[str, Any]],
        val_samples: List[Dict[str, Any]],
        test_samples: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        """
        Write manifests to train.csv, validation.csv, test.csv.
        """
        os.makedirs(output_dir, exist_ok=True)
        fieldnames = ["audio_path", "label", "speaker_id", "dataset", "attack_type", "duration"]

        manifest_paths = {
            "train": os.path.join(output_dir, "train.csv"),
            "validation": os.path.join(output_dir, "validation.csv"),
            "test": os.path.join(output_dir, "test.csv"),
        }

        splits = [
            ("train", train_samples, manifest_paths["train"]),
            ("validation", val_samples, manifest_paths["validation"]),
            ("test", test_samples, manifest_paths["test"]),
        ]

        for name, sample_list, out_csv in splits:
            with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for s in sample_list:
                    writer.writerow({
                        "audio_path": s.get("audio_path", ""),
                        "label": s.get("label", "bonafide"),
                        "speaker_id": s.get("speaker_id", "unknown"),
                        "dataset": s.get("dataset", "custom"),
                        "attack_type": s.get("attack_type", "-"),
                        "duration": s.get("duration_sec", 0.0),
                    })

        return manifest_paths


def split_dataset_speaker_disjoint(
    dataset_dir: str,
    output_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Dict[str, str]:
    """
    Convenience function to scan a directory and export speaker-disjoint train/val/test CSV manifests.
    """
    splitter = DatasetSplitter(
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )
    samples = []
    for root, _, files in os.walk(dataset_dir):
        for f in files:
            if f.lower().endswith((".wav", ".mp3", ".flac", ".ogg")):
                fpath = os.path.join(root, f)
                spk, label, attack_type = splitter.extract_speaker_and_label(fpath)
                samples.append({
                    "audio_path": fpath,
                    "speaker_id": spk,
                    "label": label,
                    "dataset": "custom",
                    "attack_type": attack_type,
                })

    train_s, val_s, test_s, _ = splitter.create_speaker_disjoint_splits(samples)
    return splitter.export_manifests(output_dir, train_s, val_s, test_s)


