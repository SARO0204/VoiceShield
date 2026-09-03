"""
Identity Verification Service for VoiceShield.
Implements out-of-band verification procedures when risk is elevated:
1. Pre-agreed Secret Question & Answer challenge
2. Trusted Contact Call-back verification
3. Safe Action Directives (Do not share OTP / passwords / money transfers)
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("voiceshield.verification")


class VerificationService:
    """
    Manages identity verification challenges and trusted caller registry.
    """

    DEFAULT_SECRET_QUESTIONS = [
        "What was the name of your first family pet?",
        "In what city did we meet last summer?",
        "What is our family secret vacation keyword?",
        "What is the nickname we only use at home?",
    ]

    def create_verification_challenge(
        self,
        call_id: Optional[str] = None,
        caller_name: Optional[str] = None,
        secret_question: Optional[str] = None,
        expected_answer_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates an active verification challenge ticket."""
        challenge_id = f"verif_{uuid.uuid4().hex[:10]}"
        return {
            "verification_id": challenge_id,
            "call_id": call_id or f"call_{uuid.uuid4().hex[:8]}",
            "caller_name": caller_name or "Unknown Caller",
            "status": "PENDING",  # PENDING, PASSED, FAILED, BYPASSED
            "question": secret_question or self.DEFAULT_SECRET_QUESTIONS[0],
            "options": [
                "Ask pre-agreed secret security question",
                "Call back using trusted saved contact number",
                "Contact mutual family / trusted person",
                "Require in-person or video verification before authorizing transactions",
            ],
            "prevention_guidelines": [
                "NEVER share OTPs or one-time verification codes under any circumstances.",
                "NEVER wire money, purchase gift cards, or make urgent crypto transfers.",
                "Do NOT rely solely on caller voice or incoming caller ID.",
                "If caller insists on immediate secrecy ('don't tell anyone'), hang up immediately.",
            ],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "resolved_at": None,
        }

    def evaluate_challenge_response(
        self,
        challenge: Dict[str, Any],
        provided_answer: str,
        correct_answer: str,
    ) -> Dict[str, Any]:
        """Validates provided challenge response."""
        is_correct = provided_answer.strip().lower() == correct_answer.strip().lower()
        challenge["status"] = "PASSED" if is_correct else "FAILED"
        challenge["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        challenge["result_message"] = (
            "Caller identity verified successfully."
            if is_correct
            else "Security answer mismatch! High probability of impersonation."
        )
        return challenge
