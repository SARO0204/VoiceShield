"""
Multi-Factor Risk Engine for VoiceShield.
Fuses AI voice clone probability, scam context indicators, confidence calibration,
audio quality metrics, and caller verification status into a composite 0-100 Risk Score.
Assigns standardized risk tiers: LOW, MEDIUM, HIGH, CRITICAL.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("voiceshield.risk_engine")


class RiskEngine:
    """
    Composite Risk Calculation Engine.
    Enforces risk level thresholds:
      0-30:   LOW
      31-60:  MEDIUM
      61-80:  HIGH
      81-100: CRITICAL
    """

    def __init__(
        self,
        weight_ai_prob: float = 0.55,
        weight_scam_context: float = 0.35,
        weight_verification: float = 0.10,
        low_threshold: int = 30,
        medium_threshold: int = 60,
        high_threshold: int = 80,
    ):
        self.weight_ai_prob = weight_ai_prob
        self.weight_scam_context = weight_scam_context
        self.weight_verification = weight_verification
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold

    def calculate_risk(
        self,
        ai_probability: float,
        model_confidence: float = 0.90,
        scam_context_score: float = 0.0,
        scam_indicators: Optional[Dict[str, Any]] = None,
        verification_status: str = "UNVERIFIED",
        audio_quality: Optional[Dict[str, Any]] = None,
        duration_sec: float = 4.0,
    ) -> Dict[str, Any]:
        """
        Calculates normalized risk score (0-100) and actionable safety recommendations.
        """
        indicators = scam_indicators or {}
        financial_req = indicators.get("financial_request", False)
        urgency = indicators.get("urgency", False)
        credential_req = indicators.get("credential_request", False)
        secrecy = indicators.get("secrecy_coercion", False)

        # 1. Base AI Voice synthetic component (0 to 100)
        ai_component = ai_probability * 100.0 * self.weight_ai_prob

        # 2. Scam context component (0 to 100)
        context_component = scam_context_score * 100.0 * self.weight_scam_context

        # 3. Verification status modifier
        verification_penalty = 0.0
        if verification_status == "FAILED":
            verification_penalty = 15.0
        elif verification_status == "UNVERIFIED" and (ai_probability > 0.60 or scam_context_score > 0.50):
            verification_penalty = 8.0
        elif verification_status == "VERIFIED":
            verification_penalty = -20.0  # Trust discount

        # 4. Critical Escalation Modifiers
        escalation = 0.0
        # If synthetic voice is high AND financial/OTP is requested -> emergency escalate
        if ai_probability >= 0.70 and (financial_req or credential_req):
            escalation += 20.0
        if ai_probability >= 0.75 and urgency:
            escalation += 10.0
        if credential_req:
            escalation += 12.0
        if secrecy:
            escalation += 8.0

        # Raw combined score
        raw_score = ai_component + context_component + verification_penalty + escalation

        # Quality modifier: very noisy/short audio has slight uncertainty buffer
        if duration_sec < 1.0:
            raw_score = raw_score * 0.85

        # Final clamped score
        risk_score = int(round(max(0, min(100, raw_score))))

        # 5. Risk Level classification
        if risk_score <= self.low_threshold:
            risk_level = "LOW"
            recommended_action = "Routine Monitoring. Call appears safe."
            action_code = "ALLOW"
        elif risk_score <= self.medium_threshold:
            risk_level = "MEDIUM"
            recommended_action = "Exercise Caution. Verify unexpected requests before proceeding."
            action_code = "MONITOR_CALL"
        elif risk_score <= self.high_threshold:
            risk_level = "HIGH"
            recommended_action = "Potential Voice Spoofing / Impersonation. Verify caller identity via trusted out-of-band channel."
            action_code = "VERIFY_CALLER_IDENTITY"
        else:
            risk_level = "CRITICAL"
            recommended_action = "High-Risk Voice Scam Detected! Do NOT transfer funds, share OTPs, or passwords. Terminate or freeze transaction immediately."
            action_code = "EMERGENCY_FREEZE_TRANSACTIONS"

        return {
            "score": risk_score,
            "level": risk_level,
            "recommended_action": recommended_action,
            "action_code": action_code,
            "breakdown": {
                "ai_voice_contribution": round(ai_component, 1),
                "scam_context_contribution": round(context_component, 1),
                "verification_modifier": round(verification_penalty, 1),
                "escalation_modifier": round(escalation, 1),
            },
            "flags": {
                "financial_risk": financial_req,
                "urgency_risk": urgency,
                "credential_risk": credential_req,
                "secrecy_risk": secrecy,
                "verification_status": verification_status,
            },
        }
