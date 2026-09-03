"""
VoiceShield Neural Model Architecture Registry.
Exports primary AASIST detector and future-compatible adapters.
"""

from typing import Dict, Type
from ml.models.base_detector import BaseVoiceDetector
from ml.models.aasist_detector import AASISTDetector
from ml.models.rawnet2_detector import RawNet2Detector
from ml.models.wav2vec2_detector import Wav2Vec2Detector
from ml.models.wavlm_detector import WavLMDetector

MODEL_REGISTRY: Dict[str, Type[BaseVoiceDetector]] = {
    "AASIST": AASISTDetector,
    "aasist": AASISTDetector,
    "RawNet2": RawNet2Detector,
    "rawnet2": RawNet2Detector,
    "Wav2Vec2": Wav2Vec2Detector,
    "wav2vec2": Wav2Vec2Detector,
    "WavLM": WavLMDetector,
    "wavlm": WavLMDetector,
}


def get_model_class(model_name: str = "AASIST") -> Type[BaseVoiceDetector]:
    """Retrieves neural model architecture class by name."""
    clean_name = model_name.strip()
    if clean_name in MODEL_REGISTRY:
        return MODEL_REGISTRY[clean_name]
    return AASISTDetector


def create_detector(model_name: str = "AASIST", **kwargs) -> BaseVoiceDetector:
    """Instantiates a deepfake voice detector architecture."""
    cls = get_model_class(model_name)
    return cls(**kwargs)


__all__ = [
    "BaseVoiceDetector",
    "AASISTDetector",
    "RawNet2Detector",
    "Wav2Vec2Detector",
    "WavLMDetector",
    "MODEL_REGISTRY",
    "get_model_class",
    "create_detector",
]
