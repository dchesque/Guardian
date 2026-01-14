"""
Módulo de API - Cliente OpenRouter.
"""

from src.api.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    get_openrouter_client
)
from src.api.models import (
    TRANSCRIPTION_MODELS,
    VISION_MODELS,
    TEXT_MODELS,
    get_model_info,
    list_models_by_type
)

__all__ = [
    "OpenRouterClient",
    "OpenRouterError",
    "get_openrouter_client",
    "TRANSCRIPTION_MODELS",
    "VISION_MODELS",
    "TEXT_MODELS",
    "get_model_info",
    "list_models_by_type",
]
