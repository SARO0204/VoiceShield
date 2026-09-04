"""
Audio Analysis API Endpoint for VoiceShield.
Implements multi-part audio upload, AASIST neural inference, scam context extraction,
multi-factor risk evaluation, explainability synthesis, and MongoDB persistence.
"""

import os
import uuid
import time
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from backend.app.api.auth import get_current_user
from backend.app.services.scam_context_service import ScamContextService
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.explainability_service import ExplainabilityService
from backend.app.services.privacy_service import PrivacyService
from backend.app.database.mongodb import db
from backend.app.core.config import settings
from ml.inference.inference_service import InferenceService

logger = logging.getLogger("voiceshield.api.analyze")
router = APIRouter(prefix="/api", tags=["Audio Analysis"])

inference_service = InferenceService()
scam_service = ScamContextService()
risk_engine = RiskEngine()
explain_service = ExplainabilityService()
privacy_service = PrivacyService()

# In-memory store fallback if MongoDB is not connected
_in_memory_analyses = []
_in_memory_calls = []
_in_memory_alerts = []


@router.post("/simulate")
async def simulate_scam_call(user: dict = Depends(get_current_user)):
    """Runs the real model against a bundled sample and persists a test call."""
    sample_path = os.path.join(settings.DATASET_DIR, "spk_001", "spk_001_spoof_02.wav")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=503, detail="Simulation sample is unavailable in this deployment.")

    try:
        inference = inference_service.analyze_audio_stream(sample_path)
        prediction = inference["prediction"]
        scam_data = scam_service.analyze_transcript(
            transcript="Send money immediately. I am in trouble with police. Tell no one and share the OTP.",
        )
        risk_result = risk_engine.calculate_risk(
            ai_probability=prediction["ai_probability"],
            model_confidence=prediction["confidence"],
            scam_context_score=scam_data["score"],
            scam_indicators=scam_data["indicators"],
            verification_status="UNVERIFIED",
            duration_sec=inference["audio_metadata"]["duration_sec"],
        )
        explanation = explain_service.generate_explanation(
            ai_probability=prediction["ai_probability"],
            classification=prediction["classification"],
            scam_context=scam_data,
            risk_data=risk_result,
        )
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        user_id = str(user.get("id", "default_user"))
        analysis_id = f"ana_{uuid.uuid4().hex[:10]}"
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        caller_label = "Simulated Grandson / Unknown Caller"
        analysis_doc = {
            "id": analysis_id, "user_id": user_id, "call_id": call_id,
            "caller_label": caller_label, "timestamp": now_iso,
            "audio_duration_sec": inference["audio_metadata"]["duration_sec"],
            "audio_filename": os.path.basename(sample_path), "model": inference["model"],
            "prediction": prediction, "risk": risk_result, "scam_context": scam_data,
            "explanation": explanation["summary_reasons"],
            "evidence_tags": explanation["evidence_tags"], "disclaimer": explanation["disclaimer"],
            "verification_status": "UNVERIFIED", "chunks": inference["chunks"],
            "performance": inference["performance"],
        }
        call_doc = {
            "id": call_id, "user_id": user_id, "caller_label": caller_label,
            "started_at": now_iso, "ended_at": now_iso,
            "duration_sec": inference["audio_metadata"]["duration_sec"],
            "overall_risk": risk_result["score"], "risk_level": risk_result["level"],
            "overall_classification": prediction["classification"], "analysis_count": 1,
            "status": "FLAGGED" if risk_result["level"] in ["HIGH", "CRITICAL"] else "COMPLETED",
            "transcript": scam_data["transcript"], "verification_status": "UNVERIFIED",
        }
        alert_doc = None
        if risk_result["level"] in ["HIGH", "CRITICAL"]:
            alert_doc = {
                "id": f"alt_{uuid.uuid4().hex[:8]}", "user_id": user_id,
                "call_id": call_id, "analysis_id": analysis_id,
                "severity": risk_result["level"], "title": "Potential Voice Scam Detected",
                "message": "Simulated call flagged by the real audio and scam risk pipeline.",
                "ai_probability": prediction["ai_probability"], "risk_score": risk_result["score"],
                "reasons": explanation["summary_reasons"], "created_at": now_iso,
                "resolved": False,
            }
        if db.is_connected and db.db is not None:
            await db.db.analyses.insert_one(analysis_doc)
            await db.db.calls.insert_one(call_doc)
            if alert_doc:
                await db.db.alerts.insert_one(alert_doc)
        analysis_doc.pop("_id", None)
        call_doc.pop("_id", None)
        if alert_doc:
            alert_doc.pop("_id", None)
        _in_memory_analyses.insert(0, analysis_doc)
        _in_memory_calls.insert(0, call_doc)
        if alert_doc:
            _in_memory_alerts.insert(0, alert_doc)
        return {"analysis": analysis_doc, "call": call_doc, "alert": alert_doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Simulation pipeline error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation pipeline error: {e}")


@router.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    transcript: Optional[str] = Form(None),
    caller_label: Optional[str] = Form("Unknown Caller"),
    financial_hint: Optional[bool] = Form(False),
    urgency_hint: Optional[bool] = Form(False),
    otp_hint: Optional[bool] = Form(False),
    user: dict = Depends(get_current_user),
):
    """
    Analyzes uploaded audio file (.wav, .mp3, .flac, .ogg, .m4a) for voice cloning,
    deepfake synthesis, scam markers, and calculates risk score.
    """
    user_id = str(user.get("id", "default_user"))
    analysis_id = f"ana_{uuid.uuid4().hex[:10]}"
    call_id = f"call_{uuid.uuid4().hex[:8]}"

    # Validate file format
    filename = file.filename or "audio.wav"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm", ".aac"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Please upload WAV, MP3, FLAC, OGG, or M4A.",
        )

    # Save audio temporarily for preprocessing
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"{analysis_id}_{filename}")

    try:
        content = await file.read()
        if len(content) < 100:
            raise HTTPException(status_code=400, detail="Uploaded file is empty or corrupted.")

        with open(temp_file_path, "wb") as f:
            f.write(content)

        # 1. Run AASIST Neural Model Inference & Sliding-Window Aggregation
        inf_result = inference_service.analyze_audio_stream(temp_file_path)

        ai_prob = inf_result["prediction"]["ai_probability"]
        genuine_prob = inf_result["prediction"]["genuine_probability"]
        confidence = inf_result["prediction"]["confidence"]
        classification = inf_result["prediction"]["classification"]
        duration_sec = inf_result["audio_metadata"]["duration_sec"]
        quality = inf_result["audio_metadata"]["quality"]

        # 2. Scam Context NLP & Pattern Analysis
        context_hints = {
            "financial_request": financial_hint,
            "urgency": urgency_hint,
            "otp_request": otp_hint,
        }
        scam_data = scam_service.analyze_transcript(transcript=transcript, context_hints=context_hints)

        # 3. Multi-Factor Risk Calculation
        risk_result = risk_engine.calculate_risk(
            ai_probability=ai_prob,
            model_confidence=confidence,
            scam_context_score=scam_data["score"],
            scam_indicators=scam_data["indicators"],
            verification_status="UNVERIFIED",
            audio_quality=quality,
            duration_sec=duration_sec,
        )

        # 4. Generate Explainability and Forensic Rationale
        explanation_data = explain_service.generate_explanation(
            ai_probability=ai_prob,
            classification=classification,
            scam_context=scam_data,
            risk_data=risk_result,
            verification_status="UNVERIFIED",
        )

        # 5. Build Record Documents
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        analysis_doc = {
            "id": analysis_id,
            "user_id": user_id,
            "call_id": call_id,
            "caller_label": caller_label,
            "timestamp": now_iso,
            "audio_duration_sec": duration_sec,
            "audio_filename": filename,
            "model": inf_result["model"],
            "prediction": {
                "classification": classification,
                "ai_probability": ai_prob,
                "genuine_probability": genuine_prob,
                "confidence": confidence,
            },
            "risk": {
                "score": risk_result["score"],
                "level": risk_result["level"],
                "action_code": risk_result["action_code"],
                "recommended_action": risk_result["recommended_action"],
                "breakdown": risk_result["breakdown"],
            },
            "scam_context": {
                "score": scam_data["score"],
                "transcript": scam_data["transcript"],
                "financial_request": scam_data["financial_request"],
                "urgency": scam_data["urgency"],
                "credential_request": scam_data["credential_request"],
                "secrecy_coercion": scam_data["secrecy_coercion"],
                "impersonation": scam_data["impersonation"],
                "matched_excerpts": scam_data["matched_excerpts"],
            },
            "explanation": explanation_data["summary_reasons"],
            "evidence_tags": explanation_data["evidence_tags"],
            "disclaimer": explanation_data["disclaimer"],
            "verification_status": "UNVERIFIED",
            "chunks": inf_result["chunks"],
            "performance": inf_result["performance"],
        }

        call_doc = {
            "id": call_id,
            "user_id": user_id,
            "caller_label": caller_label,
            "started_at": now_iso,
            "ended_at": now_iso,
            "duration_sec": duration_sec,
            "overall_risk": risk_result["score"],
            "risk_level": risk_result["level"],
            "overall_classification": classification,
            "analysis_count": 1,
            "status": "FLAGGED" if risk_result["level"] in ["HIGH", "CRITICAL"] else "COMPLETED",
            "transcript": scam_data.get("transcript", ""),
            "verification_status": "UNVERIFIED",
        }

        # If Risk is HIGH or CRITICAL, generate an automatic incident Alert
        if risk_result["level"] in ["HIGH", "CRITICAL"]:
            alert_doc = {
                "id": f"alt_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "call_id": call_id,
                "analysis_id": analysis_id,
                "severity": risk_result["level"],
                "title": f"Potential Voice Scam Detected ({risk_result['level']})",
                "message": f"Caller '{caller_label}' flagged with {int(ai_prob*100)}% synthetic voice probability and scam markers.",
                "ai_probability": ai_prob,
                "risk_score": risk_result["score"],
                "reasons": explanation_data["summary_reasons"],
                "created_at": now_iso,
                "resolved": False,
                "resolution": None,
            }
            if db.is_connected and db.db is not None:
                await db.db.alerts.insert_one(alert_doc)
            _in_memory_alerts.insert(0, alert_doc)

        # 6. Save in MongoDB & In-Memory Fallback
        if db.is_connected and db.db is not None:
            await db.db.analyses.insert_one(analysis_doc)
            await db.db.calls.insert_one(call_doc)

        analysis_doc.pop("_id", None)
        call_doc.pop("_id", None)

        _in_memory_analyses.insert(0, analysis_doc)
        _in_memory_calls.insert(0, call_doc)

        logger.info(f"Analysis completed for {filename}: {classification} (AI: {ai_prob}, Risk: {risk_result['score']} {risk_result['level']})")

        # 7. Zero-retention ephemeral privacy cleanup
        privacy_service.purge_temporary_audio(temp_file_path)

        return analysis_doc

    except Exception as e:
        privacy_service.purge_temporary_audio(temp_file_path)
        logger.error(f"Analysis execution error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")
