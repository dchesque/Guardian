"""
Constantes e helpers para modelos disponíveis no OpenRouter.
"""

# Modelos de transcrição
TRANSCRIPTION_MODELS = {
    "groq/whisper-large-v3": {
        "name": "Whisper Large V3 (Groq)",
        "price_per_hour": 0.03,
        "languages": ["pt", "en", "es", "fr", "de", "it", "ja", "ko", "zh"],
        "description": "Rápido e preciso, melhor custo-benefício"
    },
    "groq/whisper-large-v3-turbo": {
        "name": "Whisper Large V3 Turbo (Groq)",
        "price_per_hour": 0.04,
        "languages": ["pt", "en", "es", "fr", "de", "it", "ja", "ko", "zh"],
        "description": "Versão mais rápida do Whisper"
    },
    "groq/distil-whisper-large-v3-en": {
        "name": "Distil Whisper (Groq)",
        "price_per_hour": 0.02,
        "languages": ["en"],
        "description": "Mais barato, apenas inglês"
    },
}

# Modelos de análise de imagem
VISION_MODELS = {
    "google/gemini-2.0-flash-lite-001": {
        "name": "Gemini 2.0 Flash Lite",
        "price_input": 0.075,  # por 1M tokens
        "price_output": 0.30,
        "description": "Mais barato, bom para OCR e análise básica"
    },
    "google/gemini-2.0-flash-001": {
        "name": "Gemini 2.0 Flash",
        "price_input": 0.10,
        "price_output": 0.40,
        "description": "Balanceado entre custo e qualidade"
    },
    "google/gemini-2.5-flash-lite": {
        "name": "Gemini 2.5 Flash Lite",
        "price_input": 0.10,
        "price_output": 0.40,
        "description": "Versão mais recente, melhor qualidade"
    },
    "openai/gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "price_input": 0.15,
        "price_output": 0.60,
        "description": "Boa qualidade, custo moderado"
    },
}

# Modelos de texto/resumo
TEXT_MODELS = {
    "openai/gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "price_input": 0.15,
        "price_output": 0.60,
        "description": "Melhor custo-benefício para resumos"
    },
    "openai/gpt-4o": {
        "name": "GPT-4o",
        "price_input": 2.50,
        "price_output": 10.00,
        "description": "Alta qualidade, custo maior"
    },
    "anthropic/claude-3.5-haiku": {
        "name": "Claude 3.5 Haiku",
        "price_input": 0.25,
        "price_output": 1.25,
        "description": "Rápido e eficiente"
    },
    "google/gemini-2.0-flash-lite-001": {
        "name": "Gemini 2.0 Flash Lite",
        "price_input": 0.075,
        "price_output": 0.30,
        "description": "Mais barato disponível"
    },
}


def get_model_info(model_id: str) -> dict:
    """
    Obtém informações sobre um modelo.
    
    Args:
        model_id: ID do modelo no OpenRouter
        
    Returns:
        Dict com informações ou None se não encontrado
    """
    all_models = {
        **TRANSCRIPTION_MODELS,
        **VISION_MODELS,
        **TEXT_MODELS
    }
    return all_models.get(model_id)


def list_models_by_type(model_type: str) -> dict:
    """
    Lista modelos por tipo.
    
    Args:
        model_type: "transcription", "vision" ou "text"
        
    Returns:
        Dict de modelos
    """
    models_map = {
        "transcription": TRANSCRIPTION_MODELS,
        "vision": VISION_MODELS,
        "text": TEXT_MODELS,
    }
    return models_map.get(model_type, {})
