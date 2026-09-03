"""
Tests for FastAPI REST Endpoints.
"""

import os
import io
import wave
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def generate_test_wav_bytes(duration_sec=2.0, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        num_frames = int(sample_rate * duration_sec)
        import numpy as np
        t = np.linspace(0, duration_sec, num_frames, endpoint=False)
        audio = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        wav_file.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()


def test_system_status_endpoint(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert data["backend"] == "ONLINE"
    assert "gpu" in data
    assert "ml_model" in data


def test_dashboard_endpoint(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_calls_analyzed" in data
    assert "risk_distribution" in data
    assert "model_health" in data


def test_audio_analyze_endpoint(client):
    wav_bytes = generate_test_wav_bytes(duration_sec=2.0)
    files = {"file": ("test_sample.wav", wav_bytes, "audio/wav")}
    data = {
        "transcript": "Hello, this is a test audio for deepfake detection.",
        "caller_label": "Test Caller",
    }
    response = client.post("/api/analyze", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert "prediction" in res_data
    assert "risk" in res_data
    assert "explanation" in res_data
    assert "disclaimer" in res_data
    assert 0.0 <= res_data["prediction"]["ai_probability"] <= 1.0


def test_training_status_endpoint(client):
    response = client.get("/api/training/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_version" in data


def test_auth_and_protected_route(client):
    # Register test user
    reg_payload = {
        "email": "analyst_test@voiceshield.ai",
        "password": "SecurePassword123!",
        "name": "SOC Analyst Test",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code in [200, 400]  # 400 if user already registered

    # Login
    login_payload = {
        "email": "analyst_test@voiceshield.ai",
        "password": "SecurePassword123!",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Verify protected route /api/auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "analyst_test@voiceshield.ai"
