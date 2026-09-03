"""
Alerts & Incident Response API for VoiceShield.
"""

import time
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.api.auth import get_current_user
from backend.app.database.mongodb import db
from backend.app.api.analyze import _in_memory_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


class AlertResolveSchema(BaseModel):
    resolution: str  # MARK_SAFE, CONFIRM_SCAM, BLOCKED, FALSE_POSITIVE
    notes: Optional[str] = None


@router.get("")
async def list_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """Lists incident response alerts."""
    if db.is_connected and db.db is not None:
        query = {}
        if severity:
            query["severity"] = severity.upper()
        if resolved is not None:
            query["resolved"] = resolved
        cursor = db.db.alerts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await db.db.alerts.count_documents(query)
        return {"total": total, "items": items}

    filtered = _in_memory_alerts
    if severity:
        filtered = [a for a in filtered if a.get("severity") == severity.upper()]
    if resolved is not None:
        filtered = [a for a in filtered if a.get("resolved") == resolved]
    return {"total": len(filtered), "items": filtered[:limit]}


@router.patch("/{alert_id}")
async def resolve_alert(
    alert_id: str,
    payload: AlertResolveSchema,
    user: dict = Depends(get_current_user),
):
    """Marks an alert as resolved with specific disposition."""
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    update_data = {
        "resolved": True,
        "resolution": payload.resolution,
        "resolved_at": now_iso,
        "resolved_by": user.get("email", "analyst"),
        "resolution_notes": payload.notes or "",
    }

    if db.is_connected and db.db is not None:
        result = await db.db.alerts.update_one({"id": alert_id}, {"$set": update_data})
        if result.matched_count > 0:
            updated = await db.db.alerts.find_one({"id": alert_id}, {"_id": 0})
            return updated

    for a in _in_memory_alerts:
        if a.get("id") == alert_id:
            a.update(update_data)
            return a

    raise HTTPException(status_code=404, detail="Alert not found")
