"""
Pydantic Schemas and Database Data Models for VoiceShield.
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = "security_analyst"


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseSchema


class AudioAnalysisCreate(BaseModel):
    user_id: Optional[str] = "default_user"
    call_id: Optional[str] = None
    caller_label: Optional[str] = "Unknown Caller"
    transcript: Optional[str] = None
    context_hints: Optional[Dict[str, Any]] = None


class AnalysisRecord(BaseModel):
    model_config = {"protected_namespaces": ()}
    id: str = Field(default_factory=lambda: f"ana_{int(time.time()*1000)}")
    user_id: str = "default_user"
    call_id: Optional[str] = None
    caller_label: str = "Unknown Caller"
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    audio_duration_sec: float
    model_name: str = "AASIST"
    model_version: str = "1.0"
    model_mode: str = "TRAINED_INFERENCE"
    ai_probability: float
    genuine_probability: float
    confidence: float
    classification: str  # GENUINE, SYNTHETIC, UNCERTAIN
    risk_score: int  # 0 to 100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    scam_context_score: float
    indicators: Dict[str, Any] = {}
    explanation: List[str] = []
    recommended_action: str
    action_code: str
    verification_status: str = "UNVERIFIED"
    inference_latency_ms: float = 0.0


class CallRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"call_{int(time.time()*1000)}")
    user_id: str = "default_user"
    caller_label: str = "Incoming Call"
    started_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    ended_at: Optional[str] = None
    duration_sec: float = 0.0
    overall_risk: int = 0
    risk_level: str = "LOW"
    overall_classification: str = "GENUINE"
    analysis_count: int = 0
    status: str = "ACTIVE"  # ACTIVE, COMPLETED, BLOCKED, FLAGGED
    transcript: Optional[str] = ""
    verification_status: str = "UNVERIFIED"


class AlertRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"alt_{int(time.time()*1000)}")
    user_id: str = "default_user"
    call_id: Optional[str] = None
    analysis_id: Optional[str] = None
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    title: str
    message: str
    ai_probability: float = 0.0
    risk_score: int = 0
    reasons: List[str] = []
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None


class VerificationRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"ver_{int(time.time()*1000)}")
    user_id: str = "default_user"
    call_id: Optional[str] = None
    caller_name: str = "Unknown Caller"
    status: str = "PENDING"  # PENDING, PASSED, FAILED, BYPASSED
    question: str
    expected_answer: Optional[str] = None
    options: List[str] = []
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    resolved_at: Optional[str] = None


class ModelRegistryRecord(BaseModel):
    model_config = {"protected_namespaces": ()}
    id: str = Field(default_factory=lambda: f"mod_{int(time.time()*1000)}")
    model_name: str = "AASIST"
    version: str = "1.0"
    checkpoint_path: str
    dataset: str = "ASVspoof"
    metrics: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    active: bool = True
    hardware: Dict[str, Any] = {}
