"""
Tests for RiskEngine and ScamContextService.
"""

import pytest
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.scam_context_service import ScamContextService


def test_scam_context_detection():
    service = ScamContextService()

    # Normal text
    res_normal = service.analyze_transcript("Hello, this is Alice calling about our team lunch.")
    assert res_normal["score"] < 0.2
    assert len(res_normal["detected_patterns"]) == 0

    # Urgent financial demand
    scam_text = "I am in big trouble with the police. Send 50000 rupees to my UPI immediately and do not tell mom!"
    res_scam = service.analyze_transcript(scam_text)
    assert res_scam["score"] >= 0.6
    assert any("emergency" in p or "financial" in p or "secrecy" in p or "urgency" in p for p in res_scam["detected_patterns"])

    # OTP request
    otp_text = "Please share the 6 digit OTP you just received to verify your bank account."
    res_otp = service.analyze_transcript(otp_text)
    assert res_otp["score"] >= 0.30
    assert "credential_theft" in res_otp["detected_patterns"]


def test_risk_engine_calculation():
    engine = RiskEngine()

    # Low risk case: Genuine human voice + normal text
    risk_low = engine.calculate_risk(
        ai_probability=0.08,
        model_confidence=0.95,
        scam_context_score=0.05,
        scam_indicators={},
        verification_status="VERIFIED",
    )
    assert risk_low["score"] < 30
    assert risk_low["level"] == "LOW"

    # High / Critical risk case: AI voice + scam demand
    risk_critical = engine.calculate_risk(
        ai_probability=0.92,
        model_confidence=0.94,
        scam_context_score=0.85,
        scam_indicators={"financial_request": True, "emergency_distress": True},
        verification_status="UNVERIFIED",
    )
    assert risk_critical["score"] >= 80
    assert risk_critical["level"] == "CRITICAL"
    assert "Do NOT" in risk_critical["recommended_action"] or "Terminate" in risk_critical["recommended_action"] or "VERIFY" in risk_critical["recommended_action"]

    # Verification impact
    risk_verified = engine.calculate_risk(
        ai_probability=0.85,
        model_confidence=0.90,
        scam_context_score=0.70,
        scam_indicators={"financial_request": True},
        verification_status="VERIFIED",
    )
    assert risk_verified["score"] < risk_critical["score"]
