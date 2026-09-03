"""
Inference Service for VoiceShield.
Performs audio loading, preprocessing, sliding-window chunk inference,
temporal aggregation, and feature extraction.
"""

import io
import time
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np

from ml.preprocessing.audio_preprocessor import AudioPreprocessor
from ml.inference.model_manager import get_model_manager

logger = logging.getLogger("voiceshield.inference_service")


class InferenceService:
    """
    High-level inference engine for audio files, streams, and live microphone buffers.
    """

    def __init__(self, preprocessor: Optional[AudioPreprocessor] = None):
        self.preprocessor = preprocessor or AudioPreprocessor()
        self.model_manager = get_model_manager()

    def analyze_audio_stream(
        self,
        audio_source: Union[str, bytes, io.BytesIO, np.ndarray],
        chunk_size_sec: float = 4.0375,
        hop_size_sec: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Processes full audio file with multi-chunk sliding window analysis.
        Returns aggregated probabilities and chunk-by-chunk evolution.
        """
        t0 = time.perf_counter()

        # 1. Load and resample audio
        raw_audio, orig_sr = self.preprocessor.load_audio(audio_source)
        resampled = self.preprocessor.resample(raw_audio, orig_sr)
        normalized = self.preprocessor.normalize(resampled)

        duration_sec = round(len(normalized) / float(self.preprocessor.target_sample_rate), 3)
        quality = self.preprocessor.compute_audio_quality_metrics(normalized, self.preprocessor.target_sample_rate)

        # 2. Slice into chunks
        chunks = self.preprocessor.chunk_audio(normalized, chunk_size_sec=chunk_size_sec, hop_size_sec=hop_size_sec)

        chunk_results = []
        spoof_scores = []
        latencies = []

        # 3. Perform inference per chunk
        for idx, chunk in enumerate(chunks):
            chunk_padded = self.preprocessor.pad_or_truncate(chunk, self.preprocessor.target_samples)
            pred = self.model_manager.predict_audio(chunk_padded)

            chunk_info = {
                "chunk_index": idx,
                "timestamp_sec": round(idx * hop_size_sec, 2),
                "ai_probability": pred["ai_probability"],
                "genuine_probability": pred["genuine_probability"],
                "classification": pred["classification"],
                "confidence": pred["confidence"],
                "latency_ms": pred["inference_latency_ms"],
            }
            chunk_results.append(chunk_info)
            spoof_scores.append(pred["ai_probability"])
            latencies.append(pred["inference_latency_ms"])

        # 4. Temporal Aggregation (Exponential / Moving Average weighting giving more weight to peak suspicious segments)
        if len(spoof_scores) == 1:
            agg_ai_prob = spoof_scores[0]
        else:
            # Weighted average: 60% mean + 40% max to catch localized cloning / spliced speech
            mean_prob = float(np.mean(spoof_scores))
            max_prob = float(np.max(spoof_scores))
            agg_ai_prob = float(0.60 * mean_prob + 0.40 * max_prob)

        agg_ai_prob = round(float(np.clip(agg_ai_prob, 0.0, 1.0)), 4)
        agg_genuine_prob = round(1.0 - agg_ai_prob, 4)

        # Audio Quality Gate Check
        is_low_quality = (quality.get("snr_db", 20.0) < 3.0) or (quality.get("rms", 0.1) < 0.003) or (quality.get("clipping_ratio", 0.0) > 0.40)
        quality["quality_flag"] = "LOW_AUDIO_QUALITY" if is_low_quality else "ACCEPTABLE"

        # Calibration
        thresh = self.model_manager.classification_threshold
        u_min = self.model_manager.uncertainty_min
        u_max = self.model_manager.uncertainty_max

        if is_low_quality:
            overall_classification = "UNCERTAIN"
            overall_confidence = 0.40
        elif u_min <= agg_ai_prob <= u_max:
            overall_classification = "UNCERTAIN"
            overall_confidence = round(1.0 - abs(agg_ai_prob - 0.5) * 4.0, 3)
        elif agg_ai_prob > thresh:
            overall_classification = "SYNTHETIC"
            overall_confidence = round(agg_ai_prob, 3)
        else:
            overall_classification = "GENUINE"
            overall_confidence = round(agg_genuine_prob, 3)

        total_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "prediction": {
                "classification": overall_classification,
                "ai_probability": agg_ai_prob,
                "genuine_probability": agg_genuine_prob,
                "confidence": max(0.50, min(1.0, overall_confidence)),
            },
            "audio_metadata": {
                "duration_sec": duration_sec,
                "sample_rate": self.preprocessor.target_sample_rate,
                "chunk_count": len(chunks),
                "quality": quality,
            },
            "model": {
                "name": self.model_manager.default_model_name,
                "version": self.model_manager.active_version,
                "mode": self.model_manager.model_mode,
            },
            "chunks": chunk_results,
            "performance": {
                "total_processing_ms": total_time_ms,
                "avg_inference_latency_ms": round(float(np.mean(latencies)), 2) if latencies else 0.0,
            },
        }

    def analyze_live_chunk(self, chunk_pcm_bytes: bytes, input_sr: int = 16000) -> Dict[str, Any]:
        """
        Fast single-chunk inference for WebSocket real-time stream.
        """
        t0 = time.perf_counter()

        # Decode raw PCM 16-bit or float bytes
        try:
            audio_np = np.frombuffer(chunk_pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            audio_np = np.frombuffer(chunk_pcm_bytes, dtype=np.float32)

        if input_sr != self.preprocessor.target_sample_rate:
            audio_np = self.preprocessor.resample(audio_np, input_sr)

        normalized = self.preprocessor.normalize(audio_np)
        padded = self.preprocessor.pad_or_truncate(normalized, self.preprocessor.target_samples)

        pred = self.model_manager.predict_audio(padded)
        pred["chunk_duration_sec"] = round(len(audio_np) / self.preprocessor.target_sample_rate, 3)
        pred["rms_energy"] = round(float(np.sqrt(np.mean(normalized**2))), 4)
        pred["total_chunk_time_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
        return pred
