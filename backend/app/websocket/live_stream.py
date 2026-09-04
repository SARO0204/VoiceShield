"""
Real-Time Live Voice Analysis WebSocket for VoiceShield.
Streams live microphone / audio chunks, performs AASIST neural inference,
computes sliding-window temporal aggregation and scam risk, and broadcasts live metrics.
"""

import json
import base64
import time
import logging
from typing import Dict, Any, List
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ml.preprocessing.audio_preprocessor import AudioPreprocessor
from ml.inference.model_manager import get_model_manager
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.scam_context_service import ScamContextService
from backend.app.services.explainability_service import ExplainabilityService

logger = logging.getLogger("voiceshield.websocket")
router = APIRouter(tags=["Real-Time Streaming"])

preprocessor = AudioPreprocessor(target_duration_sec=0.25)
risk_engine = RiskEngine()
scam_service = ScamContextService()
explain_service = ExplainabilityService()


@router.websocket("/ws/live-analysis")
async def websocket_live_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time live streaming audio analysis.
    Accepts:
      - Binary PCM / WAV bytes
      - JSON messages with { "audio_base64": "...", "transcript": "...", "context": {...} }
    Broadcasts real-time prediction, waveform energy, risk metrics, and instant emergency alerts.
    """
    await websocket.accept()
    logger.info("WebSocket client connected to live analysis stream.")

    model_mgr = get_model_manager()
    session_id = f"stream_{int(time.time()*1000)}"

    # Stream state across chunks
    chunk_count = 0
    recent_spoof_scores: List[float] = []
    accumulated_transcript = ""

    try:
        while True:
            t_start = time.perf_counter()
            message = await websocket.receive()

            audio_data: Optional[np.ndarray] = None
            transcript_update = None
            context_hints = {}

            # Handle Binary vs JSON Text
            if "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                try:
                    # Int16 PCM array at 16kHz
                    pcm = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    audio_data = pcm
                except Exception:
                    try:
                        audio_data, _ = preprocessor.load_audio(raw_bytes)
                    except Exception as e:
                        logger.warning(f"Error decoding binary audio chunk: {e}")
                        continue

            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    if "audio_base64" in payload and payload["audio_base64"]:
                        b64_str = payload["audio_base64"]
                        if "," in b64_str:
                            b64_str = b64_str.split(",")[1]
                        decoded_bytes = base64.b64decode(b64_str)
                        audio_data, _ = preprocessor.load_audio(decoded_bytes)

                    transcript_update = payload.get("transcript")
                    if transcript_update:
                        accumulated_transcript += f" {transcript_update}"

                    context_hints = payload.get("context", {})

                except Exception as e:
                    logger.warning(f"Error parsing JSON websocket frame: {e}")
                    continue

            if audio_data is None or len(audio_data) < 100:
                # Heartbeat or empty packet
                await websocket.send_json({"type": "HEARTBEAT", "status": "READY"})
                continue

            chunk_count += 1

            # 1. Normalize and pad to AASIST input length (64,600 samples)
            normalized = preprocessor.normalize(audio_data)
            padded = preprocessor.pad_or_truncate(normalized, preprocessor.target_samples)

            # 2. AASIST Neural Inference
            pred = model_mgr.predict_audio(padded)
            raw_ai_prob = pred["ai_probability"]
            inference_latency = pred["inference_latency_ms"]

            recent_spoof_scores.append(raw_ai_prob)
            if len(recent_spoof_scores) > 10:
                recent_spoof_scores.pop(0)

            # 3. Temporal Smoothing (moving window)
            rolling_ai_prob = float(np.mean(recent_spoof_scores))
            # Boost peak if recent spikes occur
            peak_ai_prob = float(np.max(recent_spoof_scores))
            agg_ai_prob = round(0.70 * rolling_ai_prob + 0.30 * peak_ai_prob, 4)

            # 4. Scam Context NLP Analysis
            scam_data = scam_service.analyze_transcript(
                transcript=accumulated_transcript,
                context_hints=context_hints,
            )

            # 5. Live Risk Engine Scoring
            rms_energy = float(np.sqrt(np.mean(normalized**2)))
            risk_result = risk_engine.calculate_risk(
                ai_probability=agg_ai_prob,
                model_confidence=pred["confidence"],
                scam_context_score=scam_data["score"],
                scam_indicators=scam_data["indicators"],
                verification_status="UNVERIFIED",
                duration_sec=round(len(audio_data) / 16000.0, 2),
            )

            # 6. Explainability rationale
            explanation_data = explain_service.generate_explanation(
                ai_probability=agg_ai_prob,
                classification=pred["classification"],
                scam_context=scam_data,
                risk_data=risk_result,
                verification_status="UNVERIFIED",
            )

            # Total cycle latency
            total_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

            # 7. Generate Waveform sample points for frontend canvas visualization
            downsampled_waveform = [
                round(float(val), 3)
                for val in normalized[:: max(1, len(normalized) // 64)][:64]
            ]

            response_payload = {
                "type": "STREAM_UPDATE",
                "session_id": session_id,
                "chunk_index": chunk_count,
                "timestamp": time.strftime("%H:%M:%S"),
                "prediction": {
                    "classification": pred["classification"],
                    "ai_probability": agg_ai_prob,
                    "genuine_probability": round(1.0 - agg_ai_prob, 4),
                    "confidence": pred["confidence"],
                    "is_uncertain": pred["is_uncertain"],
                },
                "risk": {
                    "score": risk_result["score"],
                    "level": risk_result["level"],
                    "action_code": risk_result["action_code"],
                    "recommended_action": risk_result["recommended_action"],
                },
                "scam_context": {
                    "score": scam_data["score"],
                    "detected_patterns": scam_data["detected_patterns"],
                    "financial_request": scam_data["financial_request"],
                    "urgency": scam_data["urgency"],
                    "credential_request": scam_data["credential_request"],
                },
                "audio_metrics": {
                    "rms_energy": round(rms_energy, 4),
                    "waveform_samples": downsampled_waveform,
                },
                "performance": {
                    "inference_latency_ms": inference_latency,
                    "total_latency_ms": total_latency_ms,
                },
                "explanation": explanation_data["summary_reasons"][:3],
                "critical_alert": risk_result["level"] == "CRITICAL",
            }

            await websocket.send_json(response_payload)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally.")
    except Exception as e:
        logger.error(f"WebSocket session error: {e}", exc_info=True)
