"""
Cliente unificado para OpenRouter API.
Suporta transcrição de áudio, análise de imagem e geração de texto.
"""

import base64
import httpx
from pathlib import Path
from typing import Optional, Any
import json

from src.config_manager import get_config
from src.utils.logger import setup_logger


class OpenRouterError(Exception):
    """Erro de API do OpenRouter."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class OpenRouterClient:
    """
    Cliente para API do OpenRouter.
    
    Suporta:
    - Transcrição de áudio (via Groq Whisper)
    - Análise de imagem (via Gemini, GPT-4o, etc)
    - Geração de texto (via qualquer modelo de chat)
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente.
        
        Args:
            api_key: API key do OpenRouter. Se None, usa da config.
        """
        config = get_config()
        self.api_key = api_key or config.get("openrouter.api_key")
        
        if not self.api_key:
            raise OpenRouterError("API key do OpenRouter não configurada")
        
        log_level = config.get("system.log_level", "INFO")
        self.logger = setup_logger("openrouter", log_level)
        
        # Modelos padrão da config
        self.models = {
            "transcription": config.get("models.transcription", "groq/whisper-large-v3"),
            "screen_analysis": config.get("models.screen_analysis", "google/gemini-2.0-flash-lite-001"),
            "summary": config.get("models.summary", "openai/gpt-4o-mini"),
        }
        
        # Cliente HTTP com timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(120.0, connect=10.0),
            headers=self._get_headers()
        )
        
        self.logger.info(f"OpenRouter client inicializado")
        self.logger.debug(f"Modelos: {self.models}")
    
    def _get_headers(self) -> dict:
        """Retorna headers padrão para requisições."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/voice-screen-assistant",
            "X-Title": "Voice Screen Assistant"
        }
    
    def _handle_response(self, response: httpx.Response) -> dict:
        """
        Processa resposta da API.
        
        Args:
            response: Resposta HTTP
            
        Returns:
            JSON da resposta
            
        Raises:
            OpenRouterError: Se erro na API
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise OpenRouterError(
                f"Resposta inválida da API: {response.text}",
                status_code=response.status_code
            )
        
        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", str(data))
            raise OpenRouterError(
                f"Erro na API: {error_msg}",
                status_code=response.status_code,
                response=data
            )
        
        return data
    
    def transcribe_audio(
        self,
        audio_path: str | Path,
        model: Optional[str] = None,
        language: str = "pt"
    ) -> str:
        """
        Transcreve arquivo de áudio para texto.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            model: Modelo a usar (default: config)
            language: Código do idioma (default: pt)
            
        Returns:
            Texto transcrito
            
        Raises:
            OpenRouterError: Se erro na transcrição
        """
        model = model or self.models["transcription"]
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise OpenRouterError(f"Arquivo de áudio não encontrado: {audio_path}")
        
        self.logger.info(f"Transcrevendo: {audio_path.name} com {model}")
        
        # Ler e codificar áudio
        with open(audio_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determinar MIME type
        suffix = audio_path.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
        }
        mime_type = mime_types.get(suffix, "audio/mpeg")
        
        # Para Groq Whisper, usar endpoint específico
        if "whisper" in model.lower():
            return self._transcribe_whisper(audio_path, audio_data, mime_type, model, language)
        
        # Para outros modelos, usar chat completion com áudio
        return self._transcribe_chat(audio_data, mime_type, model, language)
    
    def _transcribe_whisper(
        self,
        audio_path: Path,
        audio_data: str,
        mime_type: str,
        model: str,
        language: str
    ) -> str:
        """Transcrição via Whisper (Groq)."""
        # OpenRouter roteia para Groq automaticamente
        url = f"{self.BASE_URL}/audio/transcriptions"
        
        # Whisper usa multipart form
        files = {
            "file": (audio_path.name, open(audio_path, "rb"), mime_type),
        }
        data = {
            "model": model,
            "language": language,
        }
        
        # Request sem Content-Type (httpx define automaticamente para multipart)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        response = self.client.post(
            url,
            files=files,
            data=data,
            headers=headers
        )
        
        result = self._handle_response(response)
        text = result.get("text", "")
        
        self.logger.info(f"Transcrição concluída: {len(text)} caracteres")
        return text
    
    def _transcribe_chat(
        self,
        audio_data: str,
        mime_type: str,
        model: str,
        language: str
    ) -> str:
        """Transcrição via chat completion com áudio."""
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "audio": {
                            "data": audio_data,
                            "format": mime_type.split("/")[1]
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Transcreva este áudio em {language}. Retorne apenas a transcrição, sem comentários."
                    }
                ]
            }]
        }
        
        response = self.client.post(url, json=payload)
        result = self._handle_response(response)
        
        text = result["choices"][0]["message"]["content"]
        self.logger.info(f"Transcrição concluída: {len(text)} caracteres")
        return text
    
    def analyze_image(
        self,
        image_path: str | Path,
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """
        Analisa uma imagem usando modelo de visão.
        
        Args:
            image_path: Caminho para a imagem
            prompt: Instrução para análise
            model: Modelo a usar (default: config)
            
        Returns:
            Análise da imagem
            
        Raises:
            OpenRouterError: Se erro na análise
        """
        model = model or self.models["screen_analysis"]
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise OpenRouterError(f"Imagem não encontrada: {image_path}")
        
        self.logger.info(f"Analisando imagem: {image_path.name} com {model}")
        
        # Ler e codificar imagem
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determinar MIME type
        suffix = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/jpeg")
        
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }],
            "max_tokens": 500
        }
        
        response = self.client.post(url, json=payload)
        result = self._handle_response(response)
        
        analysis = result["choices"][0]["message"]["content"]
        self.logger.info(f"Análise concluída: {len(analysis)} caracteres")
        return analysis
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Gera texto usando modelo de linguagem.
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt de sistema (opcional)
            model: Modelo a usar (default: config)
            max_tokens: Máximo de tokens na resposta
            
        Returns:
            Texto gerado
            
        Raises:
            OpenRouterError: Se erro na geração
        """
        model = model or self.models["summary"]
        
        self.logger.info(f"Gerando texto com {model}")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        response = self.client.post(url, json=payload)
        result = self._handle_response(response)
        
        text = result["choices"][0]["message"]["content"]
        self.logger.info(f"Geração concluída: {len(text)} caracteres")
        return text
    
    def generate_summary(
        self,
        content: str,
        custom_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Gera resumo do conteúdo usando prompt personalizado.
        
        Args:
            content: Conteúdo a resumir (transcrições + análises)
            custom_prompt: Prompt personalizado (default: da config)
            model: Modelo a usar (default: config)
            
        Returns:
            Resumo gerado
        """
        model = model or self.models["summary"]
        
        if custom_prompt is None:
            config = get_config()
            custom_prompt = config.get_prompt()
        
        full_prompt = f"""{custom_prompt}

---
CONTEÚDO DO DIA:
---

{content}
"""
        
        return self.generate_text(
            prompt=full_prompt,
            model=model,
            max_tokens=3000
        )
    
    def test_connection(self) -> bool:
        """
        Testa conexão com a API.
        
        Returns:
            True se conexão OK
        """
        try:
            self.logger.info("Testando conexão com OpenRouter...")
            
            response = self.generate_text(
                prompt="Responda apenas: OK",
                max_tokens=10
            )
            
            success = "OK" in response.upper()
            if success:
                self.logger.info("Conexão OK!")
            else:
                self.logger.warning(f"Resposta inesperada: {response}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def close(self) -> None:
        """Fecha o cliente HTTP."""
        self.client.close()
        self.logger.info("Cliente OpenRouter fechado")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton para uso global
_client_instance: Optional[OpenRouterClient] = None


def get_openrouter_client() -> OpenRouterClient:
    """
    Obtém instância singleton do OpenRouterClient.
    
    Returns:
        Instância do cliente
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = OpenRouterClient()
    
    return _client_instance
