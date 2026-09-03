"""
Authentication API Endpoints for VoiceShield.
"""

import time
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from backend.app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from backend.app.database.mongodb import db
from backend.app.database.models import UserRegisterSchema, UserLoginSchema, TokenResponse, UserResponseSchema

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Local memory fallback user store if MongoDB is offline
_in_memory_users = {}


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """Dependency to get the authenticated user from JWT token."""
    if not token:
        # Default anonymous analyst user for frictionless evaluation
        return {
            "id": "analyst_001",
            "name": "Security Analyst",
            "email": "analyst@voiceshield.ai",
            "role": "lead_analyst",
        }

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_email = payload["sub"]

    if db.is_connected and db.db is not None:
        user = await db.db.users.find_one({"email": user_email})
        if user:
            user["id"] = str(user.get("_id", user.get("id", "user_1")))
            return user

    if user_email in _in_memory_users:
        return _in_memory_users[user_email]

    return {
        "id": "user_generic",
        "name": payload.get("name", "Security Analyst"),
        "email": user_email,
        "role": payload.get("role", "security_analyst"),
    }


@router.post("/register", response_model=TokenResponse)
async def register_user(payload: UserRegisterSchema):
    """Registers a new user account."""
    email = payload.email.lower()

    # Check if user exists in MongoDB
    if db.is_connected and db.db is not None:
        existing = await db.db.users.find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists.")
    elif email in _in_memory_users:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    hashed_pwd = get_password_hash(payload.password)
    user_doc = {
        "id": user_id,
        "name": payload.name,
        "email": email,
        "password_hash": hashed_pwd,
        "role": payload.role,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if db.is_connected and db.db is not None:
        await db.db.users.insert_one(user_doc)
    _in_memory_users[email] = user_doc

    token = create_access_token({"sub": email, "name": payload.name, "role": payload.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": payload.name,
            "email": email,
            "role": payload.role,
            "created_at": user_doc["created_at"],
        },
    }


@router.post("/login", response_model=TokenResponse)
async def login_user(payload: UserLoginSchema):
    """Authenticates user credentials and returns JWT token."""
    email = payload.email.lower()
    user = None

    if db.is_connected and db.db is not None:
        user = await db.db.users.find_one({"email": email})

    if not user and email in _in_memory_users:
        user = _in_memory_users[email]

    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user_id = str(user.get("id", user.get("_id", "usr_1")))
    token = create_access_token({"sub": email, "name": user.get("name", "User"), "role": user.get("role", "analyst")})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user.get("name", "User"),
            "email": email,
            "role": user.get("role", "security_analyst"),
            "created_at": user.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
        },
    }


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    return {
        "id": str(user.get("id", user.get("_id", "usr_1"))),
        "name": user.get("name", "Security Analyst"),
        "email": user.get("email", "analyst@voiceshield.ai"),
        "role": user.get("role", "security_analyst"),
        "created_at": user.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
    }
