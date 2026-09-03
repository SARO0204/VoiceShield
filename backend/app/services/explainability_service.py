"""
Explainability & Evidence Generation Service for VoiceShield.
Produces human-readable, forensic explanations detailing why speech was flagged,
specific acoustic / contextual evidence items, and probabilistic disclaimers.
"""

from typing import Dict, Any, List, Optional


class ExplainabilityService:
    """
    Generates transparent evidence lists and explanatory rationale for forensic auditing.
    """

    DISCLAIMER = (
        "AI voice detection is probabilistic and may produce false positives or false negatives. "
        "Always verify caller identity independently through trusted out-of-band channels before authorizing sensitive transactions."
    )

    def generate_explanation(
        self,
        ai_probability: float,
        classification: str,
        scam_context: Dict[str, Any],
        risk_data: Dict[str, Any],
        verification_status: str = "UNVERIFIED",
    ) -> Dict[str, Any]:
        """
        Synthesizes model predictions, context patterns, and risk factors into structured evidence.
        """
        reasons = []
        evidence_tags = []

        # 1. Voice Authenticity Evidence
        if classification == "SYNTHETIC" or ai_probability >= 0.70:
            pct = int(ai_probability * 100)
            reasons.append(f"High synthetic speech probability ({pct}% likelihood of AI voice synthesis / cloning)")
            evidence_tags.append("AI_VOICE_CLONE_DETECTED")
        elif classification == "UNCERTAIN":
            reasons.append("Speech spectro-temporal characteristics fall in the uncertainty boundary (insufficient confidence)")
            evidence_tags.append("UNCERTAIN_AUTHENTICITY")
        else:
            reasons.append(f"Speech exhibits natural human acoustic dynamics ({int((1.0 - ai_probability) * 100)}% genuine likelihood)")
            evidence_tags.append("GENUINE_ACOUSTIC_SIGNATURE")

        # 2. Contextual Scam Evidence
        indicators = scam_context.get("indicators", {})
        matched_excerpts = scam_context.get("matched_excerpts", [])

        if indicators.get("financial_request"):
            reasons.append("Financial transfer / fund movement demand detected in conversation")
            evidence_tags.append("FINANCIAL_REQUEST")
        if indicators.get("credential_theft"):
            reasons.append("High-risk credential harvesting detected (OTP / PIN / Password request)")
            evidence_tags.append("CREDENTIAL_HARVESTING")
        if indicators.get("urgency_pressure"):
            reasons.append("Coercive urgency tactics detected (demanding immediate action without delay)")
            evidence_tags.append("URGENCY_PRESSURE")
        if indicators.get("secrecy_coercion"):
            reasons.append("Social engineering isolation detected (instructing caller not to disclose or verify)")
            evidence_tags.append("SECRECY_COERCION")
        if indicators.get("emergency_distress"):
            reasons.append("Distress / emergency situation claimed to induce panic")
            evidence_tags.append("EMERGENCY_CLAIM")
        if indicators.get("impersonation_authority"):
            reasons.append("Authority / relation impersonation pattern detected")
            evidence_tags.append("IMPERSONATION_ATTEMPT")

        # 3. Identity Verification Status
        if verification_status == "UNVERIFIED" and risk_data.get("score", 0) > 40:
            reasons.append("Caller identity has not been independently verified through out-of-band challenge")
            evidence_tags.append("IDENTITY_UNVERIFIED")
        elif verification_status == "FAILED":
            reasons.append("Caller failed identity challenge verification (secret question / callback)")
            evidence_tags.append("VERIFICATION_FAILED")
        elif verification_status == "VERIFIED":
            reasons.append("Caller has passed identity challenge response")
            evidence_tags.append("IDENTITY_VERIFIED")

        return {
            "summary_reasons": reasons,
            "evidence_tags": evidence_tags,
            "matched_excerpts": matched_excerpts,
            "disclaimer": self.DISCLAIMER,
            "confidence_level": "HIGH" if (ai_probability > 0.85 or ai_probability < 0.15) else "MODERATE",
        }
