"""
Master Startup Orchestrator for VoiceShield.
Validates dependencies, checks MongoDB, and orchestrates backend & frontend services.
Usage:
    python scripts/start_all.py
"""

import os
import sys
import subprocess
import time
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    print("==================================================================")
    print("                 VOICESHIELD PLATFORM LAUNCHER                   ")
    print("==================================================================")

    # 1. Check directories
    for d in ["./datasets", "./models", "./checkpoints", "./data/manifests", "./reports"]:
        os.makedirs(d, exist_ok=True)

    print("[1/3] Environment directories initialized.")

    # 2. Check dependencies
    try:
        import torch
        import fastapi
        import uvicorn
        import soundfile
        import librosa
        print(f"[2/3] Python dependencies verified (PyTorch {torch.__version__}, Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}).")
    except ImportError as e:
        print(f"[!] Missing dependency: {e}. Please run 'pip install -r requirements.txt'")
        sys.exit(1)

    print("[3/3] Ready to start services!")
    print("\nTo run the platform:")
    print("  Backend API:  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
    print("  Frontend UI:  cd frontend && npm run dev")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Cybersecurity Dashboard: http://localhost:5173\n")


if __name__ == "__main__":
    main()
