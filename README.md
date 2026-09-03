# <<<<<<< HEAD

# 🛡️ VOICESHIELD — AI-Powered Voice Clone Detection & Real-Time Scam Prevention

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **VoiceShield** is an enterprise-grade AI cybersecurity SOC platform and real-time defense engine against adversarial voice deepfakes, AI voice clones, and social-engineering audio scams.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **AASIST Deepfake Voice Detector (Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks)**:
   - SincNet parametric bandpass filterbank frontend operating on raw 16kHz PCM audio.
   - Dual-branch Spectral and Temporal Graph Attention Network (GAT) capturing inter-frame phase incoherence, vocoder high-frequency artifacts, and synthetic boundary anomalies.
   - Continuous score output calibrated into **Genuine Human Speech**, **AI Synthetic / Voice Clone**, or **Uncertain Verification Zone**.

2. **Multi-Factor Threat Risk Engine (0–100 Scoring)**:
   - Evaluates AI probability, acoustic confidence, NLP conversational context, urgency triggers, and financial/OTP theft markers.
   - Categorizes threat levels into **LOW (0–30)**, **MEDIUM (31–60)**, **HIGH (61–80)**, and **CRITICAL (81–100)** with actionable incident response directives.

3. **Sub-100ms Real-Time Streaming Audio Processor**:
   - WebSocket streaming endpoint (`/ws/live-analysis`) accepting live browser microphone audio in 2-second sliding windows.
   - Live oscilloscope waveform visualizer with color-coded threat gradient shift.

4. **Automated ML Training, Evaluation & Quality Gate Supervisor**:
   - 10-step automated pipeline (`scripts/train_pipeline.py`) with strict speaker-disjoint splitting (0% speaker leakage).
   - Real-time Equal Error Rate (EER), F1-Score, Precision, Recall, and ROC-AUC evaluation.
   - Automated model promotion gate: new models are promoted to production only if $F_1 \ge F_{1,\text{active}}$ and $\text{EER} \le \text{EER}_{\text{active}}$.

5. **Out-of-Band Identity Verification Challenge Hub**:
   - Automated dispatch of pre-agreed secret challenge questions when deepfake probability escalates.
   - Directives for safe call-back and financial freeze.

6. **Privacy-Preserving Ephemeral Audio Handling**:
   - Zero-retention policy automatically purges raw voice buffers post-feature extraction.

---

## 📁 Repository Structure

```
VOICESHIELD - SIH/
├── backend/                  # FastAPI async backend & security services
│   ├── app/
│   │   ├── api/              # REST Endpoints (Auth, Analyze, Dashboard, Calls, Alerts, etc.)
│   │   ├── core/             # Configuration, JWT authentication, bcrypt security
│   │   ├── database/         # Motor async MongoDB client & fallback repository
│   │   ├── services/         # Risk engine, scam NLP heuristics, explainability
│   │   └── websocket/        # Real-time /ws/live-analysis audio streamer
│   └── main.py               # Master FastAPI application entrypoint
├── ml/                       # Machine Learning core
│   ├── models/               # PyTorch AASIST, RawNet2, and BaseVoiceDetector
│   ├── preprocessing/        # Resampling (16kHz), peak/RMS normalizer, VAD chunker
│   ├── data/                 # Speaker-disjoint splitter & manifest generator
│   ├── training/             # PyTorch training loop, StepLR, AdamW, EarlyStopping
│   ├── evaluation/           # EER calculation, F1, ROC-AUC, confusion matrix
│   └── inference/            # Singleton ModelManager & multi-chunk inference service
├── frontend/                 # React 19 + TypeScript + Vite + Tailwind CSS v4
│   ├── src/
│   │   ├── components/       # Waveform visualizer, RiskBadge, EmergencyAlertModal
│   │   ├── pages/            # Dashboard, Live Protection, Audio Analyzer, Studio, etc.
│   │   ├── services/         # Type-safe API client
│   │   └── types/            # Complete TypeScript interface definitions
├── scripts/                  # DevOps & Automation tools
│   ├── start_all.py          # Unified full-stack launcher
│   ├── health_check.py       # Infrastructure diagnostic tool
│   ├── train_pipeline.py     # Automated end-to-end ML lifecycle pipeline
│   └── generate_sample_dataset.py # Speaker-labeled audio synthesizer for testing
├── tests/                    # Comprehensive PyTest automated test suite
├── checkpoints/              # Model weights & active checkpoint registry
├── datasets/                 # Audio datasets and speaker-disjoint manifests
└── reports/                  # JSON performance reports & confusion matrices
```

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.10+** (Tested on Python 3.12)
- **Node.js 18+** & **npm**
- **MongoDB** (Local service or MongoDB Atlas connection)

### 1. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 2. Backend & ML Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

### 4. Launch Entire Platform (Unified Runner)

Run the automated orchestrator:

```bash
python scripts/start_all.py
```

This boots:

- FastAPI Backend on `http://localhost:8000` (API Docs at `http://localhost:8000/docs`)
- WebSocket Server on `ws://localhost:8000/ws/live-analysis`
- Frontend React SOC Dashboard on `http://localhost:5173`

---

## 🔬 Automated Machine Learning Lifecycle

### Generate Dataset & Train AASIST Model

To generate synthetic verification audio and run the complete 10-step training, evaluation, and checkpoint registry pipeline:

```bash
python scripts/train_pipeline.py --epochs 10 --batch-size 8 --lr 0.0001
```

### Hardware Compute Auto-Detection

The training and inference engines automatically detect and configure the optimal device:
$$\text{Device Priority: } \text{CUDA (NVIDIA GPU)} \longrightarrow \text{MPS (Apple Silicon)} \longrightarrow \text{CPU (Multi-Thread)}$$

---

## 🧪 Automated Testing

Run the full pytest suite:

```bash
pytest -v
```

Build and test frontend TypeScript compilation:

```bash
cd frontend
npm run build
```

---

## 🔒 Security & Privacy Notice

- **Zero Audio Retention**: Raw voice PCM data is processed ephemerally in RAM and purged immediately upon inference completion.
- **Probabilistic Disclaimer**: Voice anti-spoofing scores represent mathematical likelihoods of synthetic vocoder acoustic artifacts and are complemented by out-of-band verification challenges.

---

## 🏆 Smart India Hackathon (SIH) Compliance

VoiceShield strictly conforms to hackathon requirements:

- ✅ Zero hardcoded or random fake percentages; all predictions are calculated via neural inference.
- ✅ Mathematical separation of voice spoof likelihood from scam conversational context.
- ✅ Strict speaker-disjoint dataset splitting preventing data leakage.
- ✅ Production-grade dark cybersecurity SOC aesthetics with real-time HUD telemetry.
  > > > > > > > bddf6ca (Add VoiceShield application)
