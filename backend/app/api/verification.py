"""
Identity Verification Workflow API for VoiceShield.
"""

from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from backend.app.api.auth import get_current_user
from backend.app.database.mongodb import db
from backend.app.services.verification_service import VerificationService

router = APIRouter(prefix="/api/verification", tags=["Identity Verification"])
verification_service = VerificationService()

_in_memory_verifications = []


class CreateVerificationSchema(BaseModel):
    call_id: Optional[str] = None
    caller_name: Optional[str] = "Incoming Caller"
    secret_question: Optional[str] = None
    expected_answer: Optional[str] = None


class VerificationResponseSchema(BaseModel):
    answer: str


@router.post("")
async def create_verification(
    payload: CreateVerificationSchema,
    user: dict = Depends(get_current_user),
):
    """Initiates an identity challenge workflow for suspicious caller."""
    challenge = verification_service.create_verification_challenge(
        call_id=payload.call_id,
        caller_name=payload.caller_name,
        secret_question=payload.secret_question,
    )
    challenge["expected_answer"] = payload.expected_answer or "blue"
    challenge["user_id"] = str(user.get("id", "default_user"))

    if db.is_connected and db.db is not None:
        await db.db.verifications.insert_one(challenge)

    challenge.pop("_id", None)
    _in_memory_verifications.insert(0, challenge)
    return challenge


@router.get("/{verification_id}")
async def get_verification(verification_id: str, user: dict = Depends(get_current_user)):
    """Retrieves verification challenge status."""
    if db.is_connected and db.db is not None:
        doc = await db.db.verifications.find_one({"verification_id": verification_id}, {"_id": 0})
        if doc:
            return doc

    for v in _in_memory_verifications:
        if v.get("verification_id") == verification_id:
            return v

    raise HTTPException(status_code=404, detail="Verification challenge not found")


@router.post("/{verification_id}/respond")
async def respond_to_verification(
    verification_id: str,
    payload: VerificationResponseSchema,
    user: dict = Depends(get_current_user),
):
    """Submits caller answer to verification challenge."""
    target = None
    if db.is_connected and db.db is not None:
        target = await db.db.verifications.find_one({"verification_id": verification_id})

    if not target:
        for v in _in_memory_verifications:
            if v.get("verification_id") == verification_id:
                target = v
                break

    if not target:
        raise HTTPException(status_code=404, detail="Verification challenge not found")

    correct = target.get("expected_answer", "blue")
    result = verification_service.evaluate_challenge_response(target, payload.answer, correct)

    if db.is_connected and db.db is not None:
        await db.db.verifications.update_one({"verification_id": verification_id}, {"$set": result})

    return result
