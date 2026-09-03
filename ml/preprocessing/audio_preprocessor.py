"""
Audio Preprocessor for VoiceShield.
Provides standardized audio ingestion, normalization, resampling (16kHz mono),
silence trimming, chunking, and tensor preparation for AASIST anti-spoofing model.
"""

import io
import os
import math
import logging
from typing import Tuple, List, Optional, Union, Dict, Any
import numpy as np

logger = logging.getLogger("voiceshield.audio_preprocessor")


class AudioPreprocessor:
    """
    Standardized audio preprocessing pipeline for voice spoofing detection.
    Enforces:
    - 16 kHz sample rate
    - Single channel (Mono)
    - Amplitude normalization
    - Duration alignment (pad/crop)
    - Sliding window chunking for streaming / long audio
    """

    def __init__(
        self,
        target_sample_rate: int = 16000,
        target_duration_sec: float = 4.0375,  # 64,600 samples at 16kHz (AASIST standard)
        normalize_method: str = "peak",
        peak_level: float = 0.95,
        silence_top_db: float = 30.0,
        min_duration_sec: float = 0.5,
        max_duration_sec: float = 300.0,  # 5 minutes
    ):
        self.target_sample_rate = target_sample_rate
        self.target_samples = round(target_sample_rate * target_duration_sec)
        self.normalize_method = normalize_method
        self.peak_level = peak_level
        self.silence_top_db = silence_top_db
        self.min_duration_sec = min_duration_sec
        self.max_duration_sec = max_duration_sec

    def load_audio(
        self,
        source: Union[str, bytes, io.BytesIO, np.ndarray],
        input_sample_rate: Optional[int] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Load audio from a file path, raw bytes, BytesIO, or numpy array.
        Returns:
            audio (np.ndarray): 1D float32 array
            sample_rate (int): original sample rate
        """
        if isinstance(source, np.ndarray):
            audio = source.astype(np.float32)
            sr = input_sample_rate or self.target_sample_rate
            if audio.ndim > 1:
                audio = np.mean(audio, axis=-1 if audio.shape[-1] <= 8 else 0)
            return audio, sr

        # Try soundfile first (pure Python / C library, fast and robust)
        try:
            import soundfile as sf

            if isinstance(source, (bytes, bytearray)):
                source_io = io.BytesIO(source)
                audio, sr = sf.read(source_io, dtype="float32")
            elif isinstance(source, io.BytesIO):
                source.seek(0)
                audio, sr = sf.read(source, dtype="float32")
            elif isinstance(source, str):
                if not os.path.exists(source):
                    raise FileNotFoundError(f"Audio file not found: {source}")
                audio, sr = sf.read(source, dtype="float32")
            else:
                raise ValueError(f"Unsupported audio source type: {type(source)}")

            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)

            return audio, sr

        except Exception as e_sf:
            logger.debug(f"Soundfile load failed ({e_sf}), falling back to librosa/scipy...")

        # Fallback to librosa
        try:
            import librosa

            if isinstance(source, (bytes, bytearray, io.BytesIO)):
                if isinstance(source, (bytes, bytearray)):
                    source = io.BytesIO(source)
                source.seek(0)
                audio, sr = librosa.load(source, sr=None, mono=True)
            elif isinstance(source, str):
                audio, sr = librosa.load(source, sr=None, mono=True)
            else:
                raise ValueError(f"Unsupported audio source type: {type(source)}")

            return audio.astype(np.float32), int(sr)

        except Exception as e_lib:
            # Fallback to scipy.io.wavfile for standard WAV bytes
            try:
                import scipy.io.wavfile as wavfile

                if isinstance(source, (bytes, bytearray)):
                    source = io.BytesIO(source)
                if isinstance(source, io.BytesIO):
                    source.seek(0)
                    sr, data = wavfile.read(source)
                elif isinstance(source, str):
                    sr, data = wavfile.read(source)
                else:
                    raise ValueError(f"Unsupported audio source type: {type(source)}")

                if data.dtype == np.int16:
                    audio = data.astype(np.float32) / 32768.0
                elif data.dtype == np.int32:
                    audio = data.astype(np.float32) / 2147483648.0
                elif data.dtype == np.uint8:
                    audio = (data.astype(np.float32) - 128.0) / 128.0
                else:
                    audio = data.astype(np.float32)

                if audio.ndim > 1:
                    audio = np.mean(audio, axis=1)

                return audio, int(sr)
            except Exception as e_wav:
                raise ValueError(
                    f"Failed to decode audio with all handlers (sf: {e_sf}, lib: {e_lib}, wav: {e_wav})"
                )

    def resample(self, audio: np.ndarray, orig_sr: int) -> np.ndarray:
        """Resample audio to target sample rate (16kHz)."""
        if orig_sr == self.target_sample_rate:
            return audio.astype(np.float32)

        try:
            import librosa
            resampled = librosa.resample(
                audio, orig_sr=orig_sr, target_sr=self.target_sample_rate, res_type="kaiser_fast"
            )
            return resampled.astype(np.float32)
        except Exception:
            # High-quality scipy resample fallback
            from scipy import signal
            num_samples = int(len(audio) * float(self.target_sample_rate) / orig_sr)
            resampled = signal.resample(audio, num_samples)
            return resampled.astype(np.float32)

    def normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normalize amplitude."""
        if len(audio) == 0:
            return audio

        if self.normalize_method == "peak":
            max_val = np.max(np.abs(audio))
            if max_val > 1e-6:
                return (audio / max_val * self.peak_level).astype(np.float32)
            return audio.astype(np.float32)
        elif self.normalize_method == "rms":
            rms = np.sqrt(np.mean(audio**2))
            if rms > 1e-6:
                target_rms = 0.1
                audio = audio * (target_rms / rms)
                # Clip to prevent clipping
                audio = np.clip(audio, -1.0, 1.0)
            return audio.astype(np.float32)

        return audio.astype(np.float32)

    def trim_silence(self, audio: np.ndarray) -> np.ndarray:
        """Trim leading and trailing silence using energy threshold."""
        if len(audio) == 0:
            return audio

        try:
            import librosa
            trimmed, _ = librosa.effects.trim(audio, top_db=self.silence_top_db)
            if len(trimmed) >= int(self.min_duration_sec * self.target_sample_rate):
                return trimmed.astype(np.float32)
            return audio.astype(np.float32)
        except Exception:
            # Simple energy-based trimming fallback
            frame_len = 512
            hop_len = 256
            if len(audio) < frame_len:
                return audio

            energy = np.array([
                np.sum(audio[i : i + frame_len] ** 2)
                for i in range(0, len(audio) - frame_len, hop_len)
            ])
            if len(energy) == 0:
                return audio

            threshold = np.max(energy) * 10 ** (-self.silence_top_db / 10.0)
            voiced = np.where(energy > threshold)[0]

            if len(voiced) > 0:
                start = max(0, voiced[0] * hop_len)
                end = min(len(audio), (voiced[-1] + 1) * hop_len + frame_len)
                trimmed = audio[start:end]
                if len(trimmed) >= int(self.min_duration_sec * self.target_sample_rate):
                    return trimmed.astype(np.float32)

            return audio.astype(np.float32)

    def pad_or_truncate(
        self,
        audio: np.ndarray,
        target_len: Optional[int] = None,
    ) -> np.ndarray:
        """
        Pad (by repeat-wrapping) or truncate audio to target number of samples.
        AASIST expects fixed-length input tensors (e.g. 64,600 samples).
        """
        target = target_len or self.target_samples
        curr_len = len(audio)

        if curr_len == target:
            return audio.astype(np.float32)
        elif curr_len > target:
            # Center crop or head crop
            start = (curr_len - target) // 2
            return audio[start : start + target].astype(np.float32)
        else:
            # Repeat wrap padding (standard in AASIST / ASVspoof benchmarks)
            if curr_len == 0:
                return np.zeros(target, dtype=np.float32)
            repeats = math.ceil(target / curr_len)
            tiled = np.tile(audio, repeats)
            return tiled[:target].astype(np.float32)

    def chunk_audio(
        self,
        audio: np.ndarray,
        chunk_size_sec: float = 4.0375,
        hop_size_sec: float = 2.0,
    ) -> List[np.ndarray]:
        """
        Slice audio into overlapping windows for temporal aggregation and streaming.
        """
        chunk_len = int(chunk_size_sec * self.target_sample_rate)
        hop_len = int(hop_size_sec * self.target_sample_rate)

        if len(audio) <= chunk_len:
            return [self.pad_or_truncate(audio, chunk_len)]

        chunks = []
        for start in range(0, len(audio) - chunk_len + 1, hop_len):
            chunk = audio[start : start + chunk_len]
            chunks.append(chunk.astype(np.float32))

        # Handle leftover tail if it has substantial length
        if len(audio) > chunk_len and (len(audio) - start - chunk_len) > (hop_len // 2):
            tail_chunk = audio[-chunk_len:]
            chunks.append(tail_chunk.astype(np.float32))

        return chunks if chunks else [self.pad_or_truncate(audio, chunk_len)]

    def compute_audio_quality_metrics(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Calculates audio quality indicators (SNR estimate, clipping ratio, RMS energy, silence ratio).
        """
        if len(audio) == 0:
            return {"snr_db": 0.0, "clipping_ratio": 0.0, "rms": 0.0, "silence_ratio": 1.0}

        rms = float(np.sqrt(np.mean(audio**2)))
        clipping_ratio = float(np.mean(np.abs(audio) >= 0.99))

        # Approximate SNR using bottom 10% energy frames as noise floor
        frame_len = int(0.025 * sr)
        hop_len = int(0.010 * sr)
        if len(audio) >= frame_len:
            frames_rms = np.array([
                np.sqrt(np.mean(audio[i : i + frame_len] ** 2))
                for i in range(0, len(audio) - frame_len, hop_len)
            ])
            sorted_rms = np.sort(frames_rms)
            noise_floor = np.mean(sorted_rms[: max(1, len(sorted_rms) // 10)]) + 1e-8
            signal_power = np.mean(sorted_rms[len(sorted_rms) // 2 :]) + 1e-8
            snr_db = float(20 * np.log10(signal_power / noise_floor))
            silence_ratio = float(np.mean(frames_rms < (noise_floor * 1.5)))
        else:
            snr_db = 20.0
            silence_ratio = 0.0

        return {
            "snr_db": round(max(-10.0, min(60.0, snr_db)), 2),
            "clipping_ratio": round(clipping_ratio, 4),
            "rms": round(rms, 4),
            "silence_ratio": round(silence_ratio, 4),
        }

    def prepare_for_model(
        self,
        source: Union[str, bytes, io.BytesIO, np.ndarray],
        input_sample_rate: Optional[int] = None,
        trim_silence: bool = True,
        pad_or_crop: bool = True,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Complete end-to-end preprocessing pipeline for ML model input.
        Returns:
            processed_audio (np.ndarray): Shape (target_samples,) at 16kHz
            metadata (dict): Audio duration, sample rate, quality metrics
        """
        raw_audio, orig_sr = self.load_audio(source, input_sample_rate)

        orig_duration = len(raw_audio) / float(orig_sr) if orig_sr > 0 else 0.0
        if orig_duration > self.max_duration_sec:
            raw_audio = raw_audio[: int(self.max_duration_sec * orig_sr)]

        # 1. Resample to 16 kHz
        resampled = self.resample(raw_audio, orig_sr)

        # 2. Trim silence if requested
        if trim_silence:
            trimmed = self.trim_silence(resampled)
        else:
            trimmed = resampled

        # 3. Normalize amplitude
        normalized = self.normalize(trimmed)

        # 4. Compute quality indicators
        quality = self.compute_audio_quality_metrics(normalized, self.target_sample_rate)

        # 5. Fixed length formatting (if requested)
        if pad_or_crop:
            final_audio = self.pad_or_truncate(normalized, self.target_samples)
        else:
            final_audio = normalized

        metadata = {
            "original_sample_rate": orig_sr,
            "target_sample_rate": self.target_sample_rate,
            "original_duration_sec": round(orig_duration, 3),
            "processed_duration_sec": round(len(final_audio) / self.target_sample_rate, 3),
            "sample_count": len(final_audio),
            "quality": quality,
        }

        return final_audio, metadata
