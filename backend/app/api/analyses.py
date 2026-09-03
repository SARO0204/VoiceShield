"""
Analyses Query & Forensic Detail API for VoiceShield.
Includes real-time PDF forensic report download.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from backend.app.api.auth import get_current_user
from backend.app.database.mongodb import db
from backend.app.api.analyze import _in_memory_analyses
from backend.app.services.report_service import report_service

router = APIRouter(prefix="/api", tags=["Analyses & Reports"])


@router.get("/analyses")
async def list_analyses(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    risk_level: Optional[str] = None,
    classification: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Lists historical voice clone analyses with filtering."""
    user_id = str(user.get("id", "default_user"))

    if db.is_connected and db.db is not None:
        query = {}
        if risk_level:
            query["risk.level"] = risk_level.upper()
        if classification:
            query["prediction.classification"] = classification.upper()

        cursor = db.db.analyses.find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
        results = await cursor.to_list(length=limit)
        total = await db.db.analyses.count_documents(query)
        return {"total": total, "items": results}

    # Fallback in-memory
    filtered = _in_memory_analyses
    if risk_level:
        filtered = [a for a in filtered if a.get("risk", {}).get("level") == risk_level.upper()]
    if classification:
        filtered = [a for a in filtered if a.get("prediction", {}).get("classification") == classification.upper()]

    return {"total": len(filtered), "items": filtered[offset : offset + limit]}


@router.get("/analyses/{analysis_id}")
async def get_analysis_by_id(analysis_id: str, user: dict = Depends(get_current_user)):
    """Retrieves full forensic details for an analysis ID."""
    if db.is_connected and db.db is not None:
        doc = await db.db.analyses.find_one({"id": analysis_id}, {"_id": 0})
        if doc:
            return doc

    for a in _in_memory_analyses:
        if a.get("id") == analysis_id:
            return a

    raise HTTPException(status_code=404, detail="Analysis record not found")


@router.get("/analyses/{analysis_id}/report")
@router.get("/reports/{analysis_id}/pdf")
async def download_analysis_pdf_report(analysis_id: str, user: dict = Depends(get_current_user)):
    """
    Generates and returns an official, cryptographically stamped PDF forensic report
    for the given analysis ID.
    """
    analysis_record = None

    if db.is_connected and db.db is not None:
        analysis_record = await db.db.analyses.find_one({"id": analysis_id}, {"_id": 0})

    if not analysis_record:
        for a in _in_memory_analyses:
            if a.get("id") == analysis_id:
                analysis_record = a
                break

    if not analysis_record:
        raise HTTPException(status_code=404, detail=f"Analysis record '{analysis_id}' not found for report generation.")

    try:
        pdf_bytes = report_service.generate_pdf_report(analysis_record)
        filename = f"VoiceShield_Forensic_Report_{analysis_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
