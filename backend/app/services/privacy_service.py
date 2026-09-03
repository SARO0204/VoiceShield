"""
Privacy Service for VoiceShield.
Enforces zero-retention ephemeral audio processing, ensures raw audio
recordings are discarded immediately after feature extraction, and manages privacy audit policies.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("voiceshield.privacy")


class PrivacyService:
    """
    Privacy Enforcement & Audio Purge Engine.
    """

    def __init__(self, retain_raw_audio_default: bool = False):
        self.retain_raw_audio = retain_raw_audio_default

    def purge_temporary_audio(self, temp_file_path: Optional[str]) -> bool:
        """
        Safely removes temporary audio file from disk after ML inference.
        """
        if not temp_file_path or not os.path.exists(temp_file_path):
            return True

        if not self.retain_raw_audio:
            try:
                os.remove(temp_file_path)
                logger.debug(f"Purged temporary audio: {temp_file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to purge audio file {temp_file_path}: {e}")
                return False
        return True

    def sanitize_metadata_for_storage(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strips sensitive audio buffers, retaining only numerical metrics, predictions, and risk indicators.
        """
        sanitized = dict(analysis_result)
        # Ensure no raw binary audio or full waveform arrays are persisted in MongoDB
        sanitized.pop("raw_audio_bytes", None)
        sanitized.pop("audio_tensor", None)
        sanitized["privacy_status"] = "RAW_AUDIO_PURGED"
        return sanitized
