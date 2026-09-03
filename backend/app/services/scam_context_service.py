"""
Scam Context Analysis Service for VoiceShield.
Analyzes conversational transcripts and acoustic contextual signals to detect social engineering,
financial demands, credential harvesting, urgency coercion, secrecy pressure, and impersonation.
Maintains clear mathematical separation between Voice Authenticity Score and Scam Context Score.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("voiceshield.scam_context")


class ScamContextService:
    """
    NLP & Heuristic Context Analyzer detecting fraud patterns and scam intent.
    """

    PATTERNS = {
        "emergency_distress": {
            "weight": 0.25,
            "regex": r"\b(in trouble|hospital|accident|emergency|police|arrested|jail|bail|kidnapped|danger|save me|help me)\b",
            "label": "Emergency / Distress Claim",
        },
        "financial_request": {
            "weight": 0.30,
            "regex": r"\b(send money|transfer|wire|pay|cash|funds|gift card|crypto|bitcoin|rupees|dollars|rs\.?|₹|\$|\b\d{4,6}\b|account number|upi|gpay|phonepe|paytm)\b",
            "label": "Financial Demand / Money Transfer",
        },
        "credential_theft": {
            "weight": 0.35,
            "regex": r"\b(otp|one.time.password|verification code|pin|password|cvv|card number|login|security code)\b",
            "label": "Credential / OTP Request",
        },
        "urgency_pressure": {
            "weight": 0.20,
            "regex": r"\b(immediately|right now|hurry|urgent|asap|within \d+ minutes|don't wait|act now|fast|last chance)\b",
            "label": "Urgency & Time Pressure",
        },
        "secrecy_coercion": {
            "weight": 0.25,
            "regex": r"\b(don't tell anyone|keep this secret|don't call|don't hang up|stay on the line|between us|don't tell mom|don't tell dad)\b",
            "label": "Secrecy & Isolation Coercion",
        },
        "impersonation_authority": {
            "weight": 0.20,
            "regex": r"\b(customs|tax department|income tax|cbi|fbi|police officer|bank manager|grandson|granddaughter|lawyer|fedex|courier parcel)\b",
            "label": "Authority / Family Impersonation",
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            category: {
                "weight": data["weight"],
                "label": data["label"],
                "compiled": re.compile(data["regex"], re.IGNORECASE),
            }
            for category, data in self.PATTERNS.items()
        }

    def analyze_transcript(
        self,
        transcript: Optional[str] = None,
        context_hints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes transcript text or simulated STT output.
        Returns:
            scam_context_score: float (0.0 to 1.0)
            risk_category: str
            indicators: dict of detected categories
            detected_keywords: list of strings
        """
        if not transcript or not transcript.strip():
            # If no transcript is provided, check any passed context hints
            hints = context_hints or {}
            financial = hints.get("financial_request", False)
            urgency = hints.get("urgency", False)
            otp = hints.get("otp_request", False)

            score = 0.0
            indicators = {}
            if financial:
                score += 0.35
                indicators["financial_request"] = True
            if urgency:
                score += 0.25
                indicators["urgency_pressure"] = True
            if otp:
                score += 0.40
                indicators["credential_theft"] = True

            score = round(min(1.0, score), 3)
            return {
                "score": score,
                "transcript": "",
                "indicators": indicators,
                "detected_patterns": list(indicators.keys()),
                "financial_request": financial,
                "urgency": urgency,
                "credential_request": otp,
                "secrecy_coercion": False,
                "impersonation": False,
                "matched_excerpts": [],
            }

        text = transcript.strip()
        matched_indicators = {}
        matched_excerpts = []
        raw_score = 0.0

        for cat, data in self.compiled_patterns.items():
            matches = data["compiled"].findall(text)
            if matches:
                matched_indicators[cat] = True
                raw_score += data["weight"]
                for m in set(matches):
                    matched_excerpts.append(f"{data['label']}: '{m}'")
            else:
                matched_indicators[cat] = False

        # Non-linear scaling: multiple simultaneous triggers compound the scam severity
        num_triggers = sum(1 for v in matched_indicators.values() if v)
        compound_multiplier = 1.0 + (0.15 * max(0, num_triggers - 1))
        final_score = round(min(1.0, raw_score * compound_multiplier), 3)

        return {
            "score": final_score,
            "transcript": text,
            "indicators": matched_indicators,
            "detected_patterns": [k for k, v in matched_indicators.items() if v],
            "financial_request": matched_indicators.get("financial_request", False),
            "urgency": matched_indicators.get("urgency_pressure", False),
            "credential_request": matched_indicators.get("credential_theft", False),
            "secrecy_coercion": matched_indicators.get("secrecy_coercion", False),
            "impersonation": matched_indicators.get("impersonation_authority", False),
            "matched_excerpts": matched_excerpts,
        }
