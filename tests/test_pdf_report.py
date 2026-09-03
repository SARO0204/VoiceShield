"""
Tests for PDF Forensic Report Generation & Download API.
"""

import io
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.services.report_service import report_service
from ml.preprocessing.audio_preprocessor import AudioPreprocessor


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def generate_sample_wav_bytes(duration_sec=2.0, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        num_frames = int(sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, num_frames, endpoint=False)
        audio = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        wav_file.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()


def test_pdf_report_service_direct():
    sample_analysis = {
        "id": "ANL-TEST-9921",
        "caller_label": "Suspect Target 01",
        "audio_duration_sec": 4.5,
        "timestamp": "2026-09-02T12:00:00Z",
        "prediction": {
            "classification": "SYNTHETIC",
            "ai_probability": 0.89,
            "genuine_probability": 0.11,
            "confidence": 0.94,
        },
        "risk": {
            "score": 92,
            "level": "CRITICAL",
            "recommended_action": "Do NOT transfer funds. Terminate transaction immediately.",
        },
        "model": {
            "name": "AASIST",
            "version": "1.0",
            "mode": "TRAINED_INFERENCE",
        },
        "audio_quality": {
            "snr_db": 28.5,
            "clipping_ratio": 0.0,
            "silence_ratio": 0.04,
        },
        "scam_context": {
            "score": 0.85,
            "indicators": {"financial_request": True, "emergency_distress": True, "urgency": True},
            "transcript": "Urgent police matter. Send funds to my account right away!",
            "detected_patterns": ["financial_demand", "urgency_coercion"],
        },
        "explanation": {
            "summary_reasons": [
                "AASIST neural graph attention detected artificial spectro-temporal artifacts",
                "Conversational urgency and financial demand identified",
            ]
        },
        "verification_status": "UNVERIFIED",
        "disclaimer": "VoiceShield forensic report generated via neural spectro-temporal modeling.",
    }

    pdf_bytes = report_service.generate_pdf_report(sample_analysis)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_download_endpoint(client):
    # 1. Run an audio analysis to create an analysis record
    wav_bytes = generate_sample_wav_bytes(duration_sec=2.0)
    files = {"file": ("test_sample_report.wav", wav_bytes, "audio/wav")}
    data = {
        "transcript": "Please send 50000 rupees to my account immediately for bail.",
        "caller_label": "Report Test Caller",
    }
    analyze_res = client.post("/api/analyze", files=files, data=data)
    assert analyze_res.status_code == 200
    analysis_id = analyze_res.json()["id"]

    # 2. Download the PDF report via GET /api/analyses/{id}/report
    report_res = client.get(f"/api/analyses/{analysis_id}/report")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert "attachment" in report_res.headers.get("content-disposition", "")
    assert report_res.content.startswith(b"%PDF-")

    # 3. Test alias endpoint GET /api/reports/{id}/pdf
    alias_res = client.get(f"/api/reports/{analysis_id}/pdf")
    assert alias_res.status_code == 200
    assert alias_res.content.startswith(b"%PDF-")


def test_audio_quality_estimation():
    preprocessor = AudioPreprocessor()
    sine_wave = np.sin(2 * np.pi * 440 * np.linspace(0, 2, 32000, endpoint=False)).astype(np.float32)
    quality = preprocessor.compute_audio_quality_metrics(sine_wave, 16000)
    assert "snr_db" in quality
    assert "clipping_ratio" in quality
    assert "rms" in quality
    assert "silence_ratio" in quality
    assert quality["rms"] > 0.1
