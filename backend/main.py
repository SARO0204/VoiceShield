"""
VoiceShield Main FastAPI Application.
Real-Time AI Voice Clone Detection & Scam Prevention Platform.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.database.mongodb import db
from ml.inference.model_manager import get_model_manager
from backend.app.api import auth, analyze, analyses, dashboard, calls, alerts, verification, analytics, system, training
from backend.app.websocket import live_stream

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voiceshield.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"=== Starting {settings.APP_NAME} v{settings.APP_VERSION} ===")

    # 1. Connect to MongoDB
    await db.connect()

    # 2. Initialize Model Manager (loads best model or pretrained checkpoint)
    model_mgr = get_model_manager()
    logger.info(f"Model status: {model_mgr.model_mode} on device: {model_mgr.device}")

    # 3. Check AUTO_TRAIN flag
    if settings.AUTO_TRAIN and model_mgr.model_mode not in ["TRAINED_INFERENCE"]:
        logger.info("AUTO_TRAIN is enabled. Initiating automatic training check...")
        from ml.data.validate_dataset import DatasetValidator
        val = DatasetValidator()
        rep = val.validate_dataset(settings.DATASET_DIR)
        if rep["valid_samples_count"] > 0:
            logger.info(f"Discovered {rep['valid_samples_count']} dataset samples. Auto-training ready.")
        else:
            logger.info("No training dataset present in dataset folder. Skipping auto-train.")

    yield

    # Shutdown
    logger.info("Shutting down VoiceShield...")
    await db.disconnect()


app = FastAPI(
    title="VoiceShield — Real-Time Voice Clone Detection API",
    description="Production-quality AI Voice Anti-Spoofing (AASIST), Scam Context Analysis & Risk Prevention Engine",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routers
app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(analyses.router)
app.include_router(dashboard.router)
app.include_router(calls.router)
app.include_router(alerts.router)
app.include_router(verification.router)
app.include_router(analytics.router)
app.include_router(system.router)
app.include_router(training.router)

# Register WebSocket Routers
app.include_router(live_stream.router)


@app.get("/")
async def root():
    """Root health verification endpoint."""
    model_mgr = get_model_manager()
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "OPERATIONAL",
        "database": "CONNECTED" if db.is_connected else "STANDBY",
        "active_model": model_mgr.default_model_name,
        "model_mode": model_mgr.model_mode,
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
