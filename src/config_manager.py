"""
Gerenciador de configurações.
Carrega, valida e fornece acesso às configurações do app.
"""

import os
from pathlib import Path
from typing import Any, Optional
import yaml

from src.utils.logger import setup_logger
from src.utils.helpers import get_project_root


class ConfigError(Exception):
    """Erro de configuração."""
    pass


class ConfigManager:
    """Gerencia todas as configurações do aplicativo."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o gerenciador de configuração.
        
        Args:
            config_path: Caminho para o arquivo de configuração.
                        Se None, usa config/settings.yaml
        """
        self.root = get_project_root()
        
        if config_path is None:
            config_path = self.root / "config" / "settings.yaml"
        
        self.config_path = Path(config_path)
        self._config: dict = {}
        self._load()
        self._validate()
        
        # Setup logger com nível da config
        log_level = self.get("system.log_level", "INFO")
        self.logger = setup_logger("config", log_level)
        self.logger.info(f"Configuração carregada de {self.config_path}")
    
    def _load(self) -> None:
        """Carrega configurações do arquivo YAML."""
        if not self.config_path.exists():
            raise ConfigError(f"Arquivo de configuração não encontrado: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Erro ao parsear YAML: {e}")
    
    def _validate(self) -> None:
        """Valida configurações obrigatórias."""
        required = [
            "openrouter.api_key",
            "models.transcription",
            "models.screen_analysis", 
            "models.summary",
        ]
        
        errors = []
        for key in required:
            value = self.get(key)
            if value is None or value == "":
                errors.append(f"Configuração obrigatória ausente: {key}")
            elif key == "openrouter.api_key" and value == "YOUR_OPENROUTER_API_KEY":
                errors.append("Configure sua API key do OpenRouter em settings.yaml")
        
        if errors:
            raise ConfigError("\n".join(errors))
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração usando notação de ponto.
        
        Args:
            key: Chave no formato "secao.subsecao.valor"
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou default
            
        Exemplo:
            config.get("audio.enabled")  # True
            config.get("models.transcription")  # "groq/whisper-large-v3"
        """
        keys = key.split(".")
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_path(self, key: str, default: str = "") -> Path:
        """
        Obtém caminho de configuração, resolvendo relativo ao projeto.
        
        Args:
            key: Chave da configuração
            default: Valor padrão
            
        Returns:
            Path absoluto
        """
        path_str = self.get(key, default)
        if not path_str:
            return Path(default)
        
        path = Path(path_str)
        if not path.is_absolute():
            path = self.root / path
        
        return path
    
    def is_enabled(self, module: str) -> bool:
        """
        Verifica se um módulo está habilitado.
        
        Args:
            module: Nome do módulo (audio, screen, email, google_drive)
            
        Returns:
            True se habilitado
        """
        return self.get(f"{module}.enabled", False)
    
    def get_prompt(self) -> str:
        """
        Carrega o prompt de resumo personalizado do arquivo.
        
        Returns:
            Conteúdo do prompt
        """
        prompt_file = self.get_path("prompt.file", "config/prompt.txt")
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        
        # Prompt padrão
        return """Analise o conteúdo do meu dia e faça um resumo executivo com:
1. Principais atividades
2. Decisões tomadas
3. Pendências identificadas"""
    
    def get_screen_analysis_prompt(self) -> str:
        """
        Carrega o prompt de análise de tela personalizado do arquivo.
        
        Returns:
            Conteúdo do prompt
        """
        prompt_file = self.get_path("prompt.screen_analysis_file", "config/screen_prompt.txt")
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        
        # Prompt padrão (fallback)
        return """Analise esta screenshot em detalhes:
1. Identifique o aplicativo ou site aberto.
2. Descreva as ações que parecem estar sendo realizadas.
3. Extraia textos, títulos ou informações importantes visíveis.
4. Identifique elementos de interface que chamam a atenção.
5. Seja detalhado e preciso na descrição."""

    def get_keyboard_analysis_prompt(self) -> str:
        """
        Carrega o prompt de análise de teclado personalizado do arquivo.
        
        Returns:
            Conteúdo do prompt
        """
        prompt_file = self.get_path("prompt.keyboard_analysis_file", "config/keyboard_prompt.txt")
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        
        # Prompt padrão (fallback)
        return """Analise o seguinte log de teclado:
1. Resuma as principais atividades e assuntos tratados.
2. Identifique intenções, tarefas mencionadas ou sites/aplicativos usados (pelo contexto).
3. Seja conciso e destaque pontos de produtividade."""
    
    def reload(self) -> None:
        """Recarrega configurações do arquivo."""
        self._load()
        self._validate()
        self.logger.info("Configuração recarregada")
    
    @property
    def audio_enabled(self) -> bool:
        return self.is_enabled("audio")
    
    @property
    def screen_enabled(self) -> bool:
        return self.is_enabled("screen")
    
    @property
    def email_enabled(self) -> bool:
        return self.is_enabled("email")
    
    @property
    def drive_enabled(self) -> bool:
        return self.is_enabled("google_drive")

    @property
    def keyboard_enabled(self) -> bool:
        return self.is_enabled("keyboard")


# Singleton para acesso global
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Obtém instância singleton do ConfigManager.
    
    Args:
        config_path: Caminho para config (apenas na primeira chamada)
        
    Returns:
        Instância do ConfigManager
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    
    return _config_instance
