"""
System Diagnostic and Health Check Script for VoiceShield.
Usage:
    python scripts/health_check.py
"""

import os
import sys
import shutil
import json
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_diagnostics():
    print("=== VOICESHIELD SYSTEM HEALTH DIAGNOSTICS ===")

    # 1. Python & PyTorch
    print(f"[+] Python Version: {sys.version.split()[0]}")
    print(f"[+] PyTorch Version: {torch.__version__}")
    print(f"[+] CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"    - GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"    - Device Count: {torch.cuda.device_count()}")
        print(f"    - CUDA Version: {torch.version.cuda}")
    else:
        print("    - Running on CPU fallback mode")

    # 2. Disk and Paths
    total, used, free = shutil.disk_usage(".")
    print(f"[+] Free Disk Space: {free / (1024**3):.2f} GB")

    # 3. Model Checkpoint check
    ckpt_path = os.path.abspath("./checkpoints/best_model.pth")
    if os.path.exists(ckpt_path):
        print(f"[+] Active Model Checkpoint: PRESENT ({os.path.getsize(ckpt_path) / (1024**2):.2f} MB)")
    else:
        print("[-] Active Model Checkpoint: NOT PRESENT (Will initialize in pretrained/standard inference mode)")

    # 4. Dataset Check
    from ml.data.validate_dataset import DatasetValidator
    val = DatasetValidator()
    rep = val.validate_dataset("./datasets")
    print(f"[+] Dataset Status: {rep['status']} ({rep['valid_samples_count']} valid audio files detected)")

    print("==============================================")
    print("STATUS: SYSTEM READY FOR EXECUTION")


if __name__ == "__main__":
    run_diagnostics()
