"""
MongoDB Async Database Client and Repository Layer for VoiceShield.
Supports MongoDB Atlas / local MongoDB with Motor async driver and high-availability fallback.
"""

import logging
from typing import Optional, Dict, Any, List
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING

from backend.app.core.config import settings

logger = logging.getLogger("voiceshield.database")


class Database:
    """
    Async MongoDB Database Handler with connection pooling and index creation.
    """

    client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    db = None
    is_connected: bool = False

    async def connect(self):
        """Initializes connection to MongoDB and creates optimal indexes."""
        try:
            logger.info("Connecting to MongoDB database '%s'...", settings.DATABASE_NAME)
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=10000,
                waitQueueTimeoutMS=5000,
            )
            # Verify server connection
            await self.client.admin.command("ping")
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            logger.info(f"Successfully connected to MongoDB database '{settings.DATABASE_NAME}'!")

            # Create Indexes
            await self._init_indexes()

        except Exception as e:
            self.is_connected = False
            if self.client:
                self.client.close()
            self.client = None
            self.db = None
            logger.warning(f"MongoDB connection ping failed ({e}). Database queries will operate in graceful fallback mode.")

    async def _init_indexes(self):
        """Creates indexes for queries."""
        if not self.is_connected or self.db is None:
            return
        try:
            # Users
            await self.db.users.create_index([("email", ASCENDING)], unique=True)
            # Analyses
            await self.db.analyses.create_index([("timestamp", DESCENDING)])
            await self.db.analyses.create_index([("user_id", ASCENDING)])
            await self.db.analyses.create_index([("risk_level", ASCENDING)])
            # Calls
            await self.db.calls.create_index([("started_at", DESCENDING)])
            await self.db.calls.create_index([("user_id", ASCENDING)])
            # Alerts
            await self.db.alerts.create_index([("created_at", DESCENDING)])
            await self.db.alerts.create_index([("severity", ASCENDING)])
            await self.db.alerts.create_index([("resolved", ASCENDING)])
            # Model Registry
            await self.db.model_registry.create_index([("created_at", DESCENDING)])
            logger.info("MongoDB indexes successfully verified and initialized.")
        except Exception as e:
            logger.warning(f"Index creation notice: {e}")

    async def disconnect(self):
        """Closes MongoDB connection."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed.")


db = Database()


def get_database():
    """Returns database instance."""
    return db
