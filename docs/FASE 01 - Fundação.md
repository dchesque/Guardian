# FASE 01 - Fundação

## Objetivo
Criar a estrutura base do projeto, sistema de configuração e logging.

## Duração Estimada
2 horas

## Pré-requisitos
- Python 3.11+ instalado
- pip disponível

---

## Entregas

### 1. Estrutura de Diretórios

Criar a seguinte estrutura:

```
voice-screen-assistant/
├── config/
│   ├── settings.yaml
│   ├── prompt.txt
│   └── credentials/
│       └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config_manager.py
│   ├── api/
│   │   └── __init__.py
│   ├── audio/
│   │   └── __init__.py
│   ├── screen/
│   │   └── __init__.py
│   ├── summary/
│   │   └── __init__.py
│   ├── storage/
│   │   └── __init__.py
│   ├── delivery/
│   │   └── __init__.py
│   ├── system/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
├── data/
│   ├── temp_audio/
│   │   └── .gitkeep
│   ├── temp_screenshots/
│   │   └── .gitkeep
│   ├── transcriptions/
│   │   └── .gitkeep
│   └── screen_analysis/
│       └── .gitkeep
├── logs/
│   └── .gitkeep
├── requirements.txt
├── install.bat
├── start.bat
├── stop.bat
└── README.md
```

---

### 2. requirements.txt

```
# API
requests==2.31.0
httpx==0.27.0

# Áudio
sounddevice==0.4.6
scipy==1.11.4
numpy==1.26.2
pydub==0.25.1

# Captura de tela
mss==9.0.1
Pillow==10.1.0

# Google Drive
google-api-python-client==2.111.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0

# Configuração
pyyaml==6.0.1
python-dotenv==1.0.0

# Agendamento
schedule==1.2.1

# Windows
pywin32==306

# Utilidades
python-dateutil==2.8.2
```

---

### 3. config/settings.yaml

```yaml
# ============================================================
# VOICE & SCREEN ASSISTANT - CONFIGURAÇÕES
# ============================================================

# ===== API OPENROUTER =====
openrouter:
  api_key: "YOUR_OPENROUTER_API_KEY"

# ===== MODELOS LLM =====
models:
  transcription: "groq/whisper-large-v3"
  screen_analysis: "google/gemini-2.0-flash-lite-001"
  summary: "openai/gpt-4o-mini"

# ===== MÓDULO DE ÁUDIO =====
audio:
  enabled: true
  input_device: null
  chunk_duration_minutes: 10
  format: "mp3"
  quality: "low"

# ===== MÓDULO DE TELA =====
screen:
  enabled: true
  capture_interval_seconds: 30
  monitor: 0
  format: "jpg"
  quality: 70

# ===== AGENDAMENTO =====
schedule:
  summary_time: "22:00"
  timezone: "America/Sao_Paulo"

# ===== GOOGLE DRIVE =====
google_drive:
  enabled: true
  credentials_file: "config/credentials/google_drive.json"
  token_file: "config/credentials/token.json"
  folder_name: "Assistente IA"
  backup:
    audio: true
    screenshots: false
    transcriptions: true
    screen_analysis: true
    summaries: true
  cleanup:
    enabled: true
    audio_retention_days: 30
    screenshots_retention_days: 7

# ===== EMAIL =====
email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  sender_email: "your_email@gmail.com"
  sender_password: "your_app_password"
  recipient_email: "your_email@gmail.com"
  send_daily_summary: true
  send_on_error: true

# ===== PROMPT =====
prompt:
  file: "config/prompt.txt"

# ===== SISTEMA =====
system:
  start_with_windows: true
  start_minimized: true
  log_level: "INFO"
  log_retention_days: 7

# ===== PRIVACIDADE =====
privacy:
  pause_on_lock: true
  excluded_apps: []
  excluded_windows: []
```

---

### 4. config/prompt.txt

```
Analise as transcrições de áudio e análises de tela do meu dia e me entregue:

## 1. Resumo Executivo
- O que aconteceu hoje em 3-5 frases

## 2. Decisões Tomadas
- Liste todas as decisões que mencionei ou tomei

## 3. Compromissos e Prazos
- Qualquer coisa que prometi fazer ou data que mencionei

## 4. Ideias e Insights
- Ideias que tive durante o dia (negócios, projetos, melhorias)

## 5. Tarefas Pendentes
- O que preciso fazer amanhã ou nos próximos dias

## 6. Alertas
- Algo que parece urgente ou que não posso esquecer

Seja objetivo e direto. Use bullet points.
```

---

### 5. src/utils/logger.py

```python
"""
Sistema de logging centralizado.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "assistant",
    log_level: str = "INFO",
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        name: Nome do logger
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        log_dir: Diretório para salvar logs
        
    Returns:
        Logger configurado
    """
    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo de log com data
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar handlers duplicados
    if logger.handlers:
        return logger
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console (apenas em modo debug)
    if log_level.upper() == "DEBUG":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def cleanup_old_logs(log_dir: str = "logs", retention_days: int = 7) -> int:
    """
    Remove logs mais antigos que retention_days.
    
    Args:
        log_dir: Diretório de logs
        retention_days: Dias para manter logs
        
    Returns:
        Número de arquivos removidos
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return 0
    
    cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
    removed = 0
    
    for log_file in log_path.glob("*.log"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            removed += 1
    
    return removed
```

---

### 6. src/utils/helpers.py

```python
"""
Funções auxiliares usadas em todo o projeto.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib


def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).parent.parent.parent


def get_today_folder() -> str:
    """Retorna o nome da pasta do dia atual (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")


def get_month_folder() -> str:
    """Retorna o nome da pasta do mês atual (YYYY-MM)."""
    return datetime.now().strftime("%Y-%m")


def get_timestamp() -> str:
    """Retorna timestamp atual formatado (HHhMM)."""
    return datetime.now().strftime("%Hh%M")


def get_datetime_stamp() -> str:
    """Retorna datetime stamp completo (YYYY-MM-DD_HHhMMmSSs)."""
    return datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")


def ensure_dir(path: str | Path) -> Path:
    """
    Garante que um diretório existe, criando se necessário.
    
    Args:
        path: Caminho do diretório
        
    Returns:
        Path do diretório
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(filename: str) -> str:
    """
    Remove caracteres inválidos de um nome de arquivo.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome do arquivo sanitizado
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def file_hash(filepath: str | Path) -> str:
    """
    Calcula hash MD5 de um arquivo.
    
    Args:
        filepath: Caminho do arquivo
        
    Returns:
        Hash MD5 em hexadecimal
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para string legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "1h 30m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_size(bytes_size: int) -> str:
    """
    Formata tamanho em bytes para string legível.
    
    Args:
        bytes_size: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"
```

---

### 7. src/config_manager.py

```python
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
        Carrega o prompt personalizado do arquivo.
        
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
```

---

### 8. src/main.py (Esqueleto)

```python
"""
Voice & Screen Assistant - Ponto de entrada principal.
"""

import sys
import signal
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import get_config, ConfigError
from src.utils.logger import setup_logger, cleanup_old_logs


class Assistant:
    """Classe principal do assistente."""
    
    def __init__(self):
        """Inicializa o assistente."""
        self.running = False
        self.config = None
        self.logger = None
    
    def setup(self) -> bool:
        """
        Configura o assistente.
        
        Returns:
            True se setup bem-sucedido
        """
        try:
            # Carregar configuração
            self.config = get_config()
            
            # Setup logger
            log_level = self.config.get("system.log_level", "INFO")
            self.logger = setup_logger("assistant", log_level)
            
            # Limpar logs antigos
            retention = self.config.get("system.log_retention_days", 7)
            removed = cleanup_old_logs(retention_days=retention)
            if removed > 0:
                self.logger.info(f"Removidos {removed} arquivos de log antigos")
            
            self.logger.info("=" * 50)
            self.logger.info("Voice & Screen Assistant iniciando...")
            self.logger.info("=" * 50)
            
            # Log das configurações ativas
            self.logger.info(f"Módulo de áudio: {'ATIVO' if self.config.audio_enabled else 'INATIVO'}")
            self.logger.info(f"Módulo de tela: {'ATIVO' if self.config.screen_enabled else 'INATIVO'}")
            self.logger.info(f"Google Drive: {'ATIVO' if self.config.drive_enabled else 'INATIVO'}")
            self.logger.info(f"Email: {'ATIVO' if self.config.email_enabled else 'INATIVO'}")
            
            return True
            
        except ConfigError as e:
            print(f"ERRO DE CONFIGURAÇÃO: {e}")
            return False
        except Exception as e:
            print(f"ERRO NO SETUP: {e}")
            return False
    
    def start(self) -> None:
        """Inicia o assistente."""
        if not self.setup():
            sys.exit(1)
        
        self.running = True
        self.logger.info("Assistente iniciado com sucesso!")
        
        # TODO: Iniciar módulos (implementar nas próximas fases)
        # - Audio recorder
        # - Screen capture
        # - Scheduler
        # - Power monitor
        
        self.logger.info("Pressione Ctrl+C para encerrar")
        
        try:
            # Loop principal (será substituído pelo scheduler)
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Para o assistente."""
        self.running = False
        if self.logger:
            self.logger.info("Encerrando assistente...")
            self.logger.info("=" * 50)
    
    def handle_signal(self, signum, frame) -> None:
        """Handler para sinais do sistema."""
        self.stop()


def main():
    """Função principal."""
    assistant = Assistant()
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, assistant.handle_signal)
    signal.signal(signal.SIGTERM, assistant.handle_signal)
    
    assistant.start()


if __name__ == "__main__":
    main()
```

---

### 9. Scripts Batch

#### install.bat
```batch
@echo off
echo ========================================
echo Voice Screen Assistant - Instalacao
echo ========================================
echo.

echo Verificando Python...
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.11+ de https://python.org
    pause
    exit /b 1
)

echo.
echo Instalando dependencias...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Instalacao concluida!
echo ========================================
echo.
echo Proximos passos:
echo 1. Edite config/settings.yaml com suas credenciais
echo 2. Configure o Google Drive (veja README.md)
echo 3. Execute start.bat para iniciar
echo.
pause
```

#### start.bat
```batch
@echo off
echo Iniciando Voice Screen Assistant...
pythonw src/main.py
```

#### stop.bat
```batch
@echo off
echo Parando Voice Screen Assistant...
taskkill /f /im pythonw.exe 2>nul
echo Assistente encerrado.
pause
```

---

### 10. README.md

```markdown
# Voice & Screen Assistant

Assistente que captura áudio e tela, transcreve, analisa e gera resumos diários.

## Instalação

1. Instale Python 3.11+ de https://python.org
2. Execute `install.bat`
3. Configure `config/settings.yaml` com sua API key do OpenRouter
4. Configure o Google Drive (veja abaixo)

## Configuração do Google Drive

1. Acesse https://console.cloud.google.com
2. Crie um novo projeto
3. Ative a "Google Drive API"
4. Crie credenciais OAuth 2.0 (tipo "App para computador")
5. Baixe o JSON e salve como `config/credentials/google_drive.json`

## Uso

- Iniciar: `start.bat`
- Parar: `stop.bat`

## Configuração

Edite `config/settings.yaml` para personalizar:

- Modelos de IA utilizados
- Intervalo de captura de tela
- Duração dos chunks de áudio
- Horário do resumo diário
- Email de destino
- E mais...

## Estrutura de Pastas no Google Drive

```
Assistente IA/
└── 2025-01-15/
    ├── audio/
    │   └── *.mp3
    ├── transcricao.txt
    ├── analise_tela.txt
    └── resumo.md
```

## Custos Estimados

- Só áudio: ~R$40/mês
- Só tela: ~R$110/mês
- Completo: ~R$150/mês
```

---

## Critérios de Aceite da Fase 1

- [ ] Estrutura de diretórios criada
- [ ] requirements.txt funcional (pip install sem erros)
- [ ] settings.yaml com todas as configurações documentadas
- [ ] prompt.txt com prompt padrão
- [ ] Logger funcionando (cria arquivos em logs/)
- [ ] ConfigManager carrega e valida configurações
- [ ] main.py executa sem erros (apenas setup, sem funcionalidade real)
- [ ] Scripts batch funcionando (install.bat, start.bat, stop.bat)
- [ ] README.md com instruções básicas

---

## Testes

```bash
# Testar instalação
pip install -r requirements.txt

# Testar configuração (deve dar erro por falta de API key)
python -c "from src.config_manager import get_config; get_config()"

# Após configurar API key, testar novamente
python -c "from src.config_manager import get_config; c = get_config(); print('OK')"

# Testar main (Ctrl+C para sair)
python src/main.py
```

---

## Próxima Fase

Após completar esta fase, prossiga para **FASE-02-API-CLIENT.md**.