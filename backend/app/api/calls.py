"""
Calls Monitoring API for VoiceShield.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.api.auth import get_current_user
from backend.app.database.mongodb import db
from backend.app.api.analyze import _in_memory_calls, _in_memory_analyses

router = APIRouter(prefix="/api/calls", tags=["Calls"])


@router.get("")
async def list_calls(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Lists monitored incoming & past calls."""
    if db.is_connected and db.db is not None:
        query = {}
        if status:
            query["status"] = status.upper()
        cursor = db.db.calls.find(query, {"_id": 0}).sort("started_at", -1).skip(offset).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await db.db.calls.count_documents(query)
        return {"total": total, "items": items}

    filtered = _in_memory_calls
    if status:
        filtered = [c for c in filtered if c.get("status") == status.upper()]
    return {"total": len(filtered), "items": filtered[offset : offset + limit]}


@router.get("/{call_id}")
async def get_call_detail(call_id: str, user: dict = Depends(get_current_user)):
    """Retrieves full call details, associated chunk analyses, and timeline."""
    call_doc = None
    if db.is_connected and db.db is not None:
        call_doc = await db.db.calls.find_one({"id": call_id}, {"_id": 0})
        analyses = await db.db.analyses.find({"call_id": call_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    else:
        for c in _in_memory_calls:
            if c.get("id") == call_id:
                call_doc = c
                break
        analyses = [a for a in _in_memory_analyses if a.get("call_id") == call_id]

    if not call_doc:
        raise HTTPException(status_code=404, detail="Call record not found")

    return {
        "call": call_doc,
        "analyses": analyses,
        "timeline_events": [
            {
                "timestamp": a.get("timestamp"),
                "event": f"Analysis: {a.get('prediction', {}).get('classification')} (Risk {a.get('risk', {}).get('score')})",
                "ai_probability": a.get("prediction", {}).get("ai_probability"),
                "risk_level": a.get("risk", {}).get("level"),
            }
            for a in analyses
        ],
    }
