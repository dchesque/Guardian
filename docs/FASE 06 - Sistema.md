# FASE 06 - Sistema

## Objetivo
Implementar agendador, monitoramento de energia, inicialização com Windows e integração final.

## Duração Estimada
2 horas

## Pré-requisitos
- Fases 01-05 completas

---

## Entregas

### 1. src/system/scheduler.py

```python
"""
Agendador de tarefas.
"""

import schedule
import threading
import time
from datetime import datetime
from typing import Callable, Optional

from src.config_manager import get_config
from src.utils.logger import setup_logger


class TaskScheduler:
    """Agendador de tarefas periódicas."""
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("scheduler", config.get("system.log_level", "INFO"))
        
        self.summary_time = config.get("schedule.summary_time", "22:00")
        self.timezone = config.get("schedule.timezone", "America/Sao_Paulo")
        
        self._is_running = False
        self._thread = None
        self._callbacks = {}
    
    def register_callback(self, name: str, callback: Callable):
        """Registra callback para eventos."""
        self._callbacks[name] = callback
        self.logger.debug(f"Callback registrado: {name}")
    
    def _run_scheduler(self):
        """Loop do agendador."""
        self.logger.info("Scheduler iniciado")
        
        while self._is_running:
            schedule.run_pending()
            time.sleep(1)
        
        self.logger.info("Scheduler parado")
    
    def _trigger_daily_summary(self):
        """Dispara geração de resumo diário."""
        self.logger.info("Disparando resumo diário...")
        
        if 'on_summary_time' in self._callbacks:
            try:
                self._callbacks['on_summary_time']()
            except Exception as e:
                self.logger.error(f"Erro no resumo diário: {e}")
    
    def _trigger_cleanup(self):
        """Dispara limpeza de arquivos antigos."""
        self.logger.info("Disparando limpeza...")
        
        if 'on_cleanup' in self._callbacks:
            try:
                self._callbacks['on_cleanup']()
            except Exception as e:
                self.logger.error(f"Erro na limpeza: {e}")
    
    def start(self):
        """Inicia o agendador."""
        if self._is_running:
            return
        
        # Agendar resumo diário
        schedule.every().day.at(self.summary_time).do(self._trigger_daily_summary)
        self.logger.info(f"Resumo agendado para {self.summary_time}")
        
        # Agendar limpeza (1x por dia, meia-noite)
        schedule.every().day.at("00:30").do(self._trigger_cleanup)
        self.logger.info("Limpeza agendada para 00:30")
        
        self._is_running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Para o agendador."""
        self._is_running = False
        schedule.clear()
        
        if self._thread:
            self._thread.join(timeout=5)
    
    def run_now(self, task: str):
        """Executa tarefa imediatamente."""
        if task == 'summary':
            self._trigger_daily_summary()
        elif task == 'cleanup':
            self._trigger_cleanup()
```

---

### 2. src/system/power_monitor.py

```python
"""
Monitor de eventos de energia do Windows.
Detecta sleep, wake, lock, unlock.
"""

import threading
import ctypes
from ctypes import wintypes
from typing import Callable, Optional

from src.config_manager import get_config
from src.utils.logger import setup_logger


# Constantes Windows
WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012

WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8


class PowerMonitor:
    """Monitora eventos de energia e sessão do Windows."""
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("power_monitor", config.get("system.log_level", "INFO"))
        
        self.pause_on_lock = config.get("privacy.pause_on_lock", True)
        
        self._callbacks = {}
        self._is_running = False
        self._hwnd = None
    
    def register_callback(self, event: str, callback: Callable):
        """
        Registra callback para evento.
        
        Eventos:
        - 'on_sleep': Quando PC entra em sleep
        - 'on_wake': Quando PC acorda
        - 'on_lock': Quando tela é bloqueada
        - 'on_unlock': Quando tela é desbloqueada
        """
        self._callbacks[event] = callback
    
    def _window_proc(self, hwnd, msg, wparam, lparam):
        """Processa mensagens do Windows."""
        try:
            if msg == WM_POWERBROADCAST:
                if wparam == PBT_APMSUSPEND:
                    self.logger.info("Sistema entrando em sleep")
                    self._trigger('on_sleep')
                elif wparam in (PBT_APMRESUMESUSPEND, PBT_APMRESUMEAUTOMATIC):
                    self.logger.info("Sistema acordando")
                    self._trigger('on_wake')
            
            elif msg == WM_WTSSESSION_CHANGE:
                if wparam == WTS_SESSION_LOCK:
                    self.logger.info("Tela bloqueada")
                    if self.pause_on_lock:
                        self._trigger('on_lock')
                elif wparam == WTS_SESSION_UNLOCK:
                    self.logger.info("Tela desbloqueada")
                    if self.pause_on_lock:
                        self._trigger('on_unlock')
        except Exception as e:
            self.logger.error(f"Erro no power monitor: {e}")
        
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)
    
    def _trigger(self, event: str):
        """Dispara callback de evento."""
        if event in self._callbacks:
            try:
                self._callbacks[event]()
            except Exception as e:
                self.logger.error(f"Erro no callback {event}: {e}")
    
    def _message_loop(self):
        """Loop de mensagens do Windows."""
        try:
            # Criar janela invisível para receber mensagens
            WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)
            
            wc = ctypes.windll.user32.WNDCLASSW()
            wc.lpfnWndProc = WNDPROC(self._window_proc)
            wc.lpszClassName = "PowerMonitorClass"
            
            ctypes.windll.user32.RegisterClassW(ctypes.byref(wc))
            
            self._hwnd = ctypes.windll.user32.CreateWindowExW(
                0, wc.lpszClassName, "PowerMonitor",
                0, 0, 0, 0, 0, None, None, None, None
            )
            
            # Registrar para notificações de sessão
            ctypes.windll.wtsapi32.WTSRegisterSessionNotification(self._hwnd, 0)
            
            self.logger.info("Power monitor iniciado")
            
            # Loop de mensagens
            msg = wintypes.MSG()
            while self._is_running:
                if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
                    
        except Exception as e:
            self.logger.error(f"Erro no message loop: {e}")
    
    def start(self):
        """Inicia monitoramento."""
        if self._is_running:
            return
        
        self._is_running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Para monitoramento."""
        self._is_running = False
        
        if self._hwnd:
            try:
                ctypes.windll.wtsapi32.WTSUnRegisterSessionNotification(self._hwnd)
                ctypes.windll.user32.DestroyWindow(self._hwnd)
            except:
                pass
```

---

### 3. src/system/startup.py

```python
"""
Configuração de inicialização com Windows.
"""

import os
import sys
from pathlib import Path

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import get_project_root


class StartupManager:
    """Gerencia inicialização automática com Windows."""
    
    TASK_NAME = "VoiceScreenAssistant"
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("startup", config.get("system.log_level", "INFO"))
        self.root = get_project_root()
    
    def enable(self) -> bool:
        """Habilita inicialização com Windows usando Agendador de Tarefas."""
        try:
            import subprocess
            
            # Caminho do script
            script_path = self.root / "src" / "main.py"
            pythonw_path = Path(sys.executable).parent / "pythonw.exe"
            
            # Criar tarefa agendada
            cmd = f'''schtasks /create /tn "{self.TASK_NAME}" /tr "\\"{pythonw_path}\\" \\"{script_path}\\"" /sc onlogon /rl highest /f'''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Inicialização automática habilitada")
                return True
            else:
                self.logger.error(f"Erro ao criar tarefa: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao habilitar startup: {e}")
            return False
    
    def disable(self) -> bool:
        """Desabilita inicialização com Windows."""
        try:
            import subprocess
            
            cmd = f'schtasks /delete /tn "{self.TASK_NAME}" /f'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Inicialização automática desabilitada")
                return True
            else:
                self.logger.error(f"Erro ao remover tarefa: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao desabilitar startup: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Verifica se inicialização está habilitada."""
        try:
            import subprocess
            
            cmd = f'schtasks /query /tn "{self.TASK_NAME}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except:
            return False
```

---

### 4. src/system/__init__.py

```python
from src.system.scheduler import TaskScheduler
from src.system.power_monitor import PowerMonitor
from src.system.startup import StartupManager

__all__ = ["TaskScheduler", "PowerMonitor", "StartupManager"]
```

---

### 5. src/main.py (Versão Final)

```python
"""
Voice & Screen Assistant - Versão Final
"""

import sys
import signal
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import get_config, ConfigError
from src.utils.logger import setup_logger, cleanup_old_logs
from src.audio import AudioRecorder, AudioTranscriber
from src.screen import ScreenCapture, ScreenAnalyzer
from src.storage import DriveManager
from src.delivery import EmailSender
from src.summary import SummaryGenerator
from src.system import TaskScheduler, PowerMonitor, StartupManager


class Assistant:
    """Classe principal do assistente."""
    
    def __init__(self):
        self.running = False
        self.config = None
        self.logger = None
        
        # Módulos
        self.audio_recorder = None
        self.audio_transcriber = None
        self.screen_capture = None
        self.screen_analyzer = None
        self.drive_manager = None
        self.email_sender = None
        self.summary_generator = None
        self.scheduler = None
        self.power_monitor = None
    
    def setup(self) -> bool:
        """Configura o assistente."""
        try:
            self.config = get_config()
            
            log_level = self.config.get("system.log_level", "INFO")
            self.logger = setup_logger("assistant", log_level)
            
            # Limpar logs antigos
            retention = self.config.get("system.log_retention_days", 7)
            cleanup_old_logs(retention_days=retention)
            
            self.logger.info("=" * 50)
            self.logger.info("Voice & Screen Assistant v1.0")
            self.logger.info("=" * 50)
            
            # Setup módulos
            if self.config.audio_enabled:
                self._setup_audio()
            
            if self.config.screen_enabled:
                self._setup_screen()
            
            if self.config.drive_enabled:
                self._setup_drive()
            
            if self.config.email_enabled:
                self._setup_email()
            
            self._setup_summary()
            self._setup_scheduler()
            self._setup_power_monitor()
            
            # Configurar startup se habilitado
            if self.config.get("system.start_with_windows", False):
                startup = StartupManager()
                if not startup.is_enabled():
                    startup.enable()
            
            self._log_status()
            return True
            
        except ConfigError as e:
            print(f"ERRO DE CONFIGURAÇÃO: {e}")
            return False
        except Exception as e:
            print(f"ERRO NO SETUP: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _setup_audio(self):
        self.logger.info("Configurando módulo de áudio...")
        chunk_duration = self.config.get("audio.chunk_duration_minutes", 10)
        
        self.audio_transcriber = AudioTranscriber()
        self.audio_recorder = AudioRecorder(
            chunk_duration_minutes=chunk_duration,
            on_chunk_ready=self._on_audio_chunk_ready
        )
    
    def _setup_screen(self):
        self.logger.info("Configurando módulo de tela...")
        interval = self.config.get("screen.capture_interval_seconds", 30)
        
        self.screen_analyzer = ScreenAnalyzer()
        self.screen_capture = ScreenCapture(
            interval_seconds=interval,
            on_capture_ready=self._on_screenshot_ready
        )
    
    def _setup_drive(self):
        self.logger.info("Configurando Google Drive...")
        self.drive_manager = DriveManager()
    
    def _setup_email(self):
        self.logger.info("Configurando email...")
        self.email_sender = EmailSender()
    
    def _setup_summary(self):
        self.logger.info("Configurando gerador de resumo...")
        self.summary_generator = SummaryGenerator()
    
    def _setup_scheduler(self):
        self.logger.info("Configurando agendador...")
        self.scheduler = TaskScheduler()
        self.scheduler.register_callback('on_summary_time', self._generate_daily_summary)
        self.scheduler.register_callback('on_cleanup', self._cleanup_old_files)
    
    def _setup_power_monitor(self):
        self.logger.info("Configurando monitor de energia...")
        self.power_monitor = PowerMonitor()
        self.power_monitor.register_callback('on_sleep', self._on_sleep)
        self.power_monitor.register_callback('on_wake', self._on_wake)
        self.power_monitor.register_callback('on_lock', self._on_lock)
        self.power_monitor.register_callback('on_unlock', self._on_unlock)
    
    def _log_status(self):
        self.logger.info("-" * 50)
        self.logger.info(f"Áudio: {'✓' if self.config.audio_enabled else '✗'}")
        self.logger.info(f"Tela: {'✓' if self.config.screen_enabled else '✗'}")
        self.logger.info(f"Drive: {'✓' if self.config.drive_enabled else '✗'}")
        self.logger.info(f"Email: {'✓' if self.config.email_enabled else '✗'}")
        self.logger.info("-" * 50)
    
    # Callbacks de áudio
    def _on_audio_chunk_ready(self, audio_path: Path):
        self.logger.info(f"Chunk de áudio: {audio_path.name}")
        
        if self.audio_transcriber:
            self.audio_transcriber.add_to_queue(audio_path)
        
        if self.drive_manager:
            self.drive_manager.upload_audio(audio_path)
    
    # Callbacks de tela
    def _on_screenshot_ready(self, screenshot_path: Path):
        self.logger.debug(f"Screenshot: {screenshot_path.name}")
        
        if self.screen_analyzer:
            self.screen_analyzer.add_to_queue(screenshot_path)
    
    # Callbacks de energia
    def _on_sleep(self):
        self.logger.info("Pausando para sleep...")
        if self.audio_recorder:
            self.audio_recorder.pause()
        if self.screen_capture:
            self.screen_capture.pause()
    
    def _on_wake(self):
        self.logger.info("Retomando após wake...")
        if self.audio_recorder:
            self.audio_recorder.resume()
        if self.screen_capture:
            self.screen_capture.resume()
    
    def _on_lock(self):
        self.logger.info("Pausando (tela bloqueada)...")
        if self.audio_recorder:
            self.audio_recorder.pause()
        if self.screen_capture:
            self.screen_capture.pause()
    
    def _on_unlock(self):
        self.logger.info("Retomando (tela desbloqueada)...")
        if self.audio_recorder:
            self.audio_recorder.resume()
        if self.screen_capture:
            self.screen_capture.resume()
    
    # Callbacks do scheduler
    def _generate_daily_summary(self):
        self.logger.info("Gerando resumo diário...")
        
        try:
            summary = self.summary_generator.generate()
            
            if self.email_sender:
                self.email_sender.send_daily_summary(summary)
            
            if self.drive_manager:
                from src.utils.helpers import get_today_folder, get_project_root
                summary_path = get_project_root() / "data" / "summaries" / get_today_folder() / "resumo.md"
                if summary_path.exists():
                    self.drive_manager.upload_summary(summary_path)
            
        except Exception as e:
            self.logger.error(f"Erro no resumo diário: {e}")
            if self.email_sender:
                self.email_sender.send_error_alert(str(e))
    
    def _cleanup_old_files(self):
        self.logger.info("Limpando arquivos antigos...")
        
        if self.drive_manager:
            self.drive_manager.cleanup_old_files()
    
    def start(self):
        """Inicia o assistente."""
        if not self.setup():
            sys.exit(1)
        
        self.running = True
        self.logger.info("Iniciando assistente...")
        
        # Iniciar módulos
        if self.audio_transcriber:
            self.audio_transcriber.start()
        if self.audio_recorder:
            self.audio_recorder.start()
        if self.screen_analyzer:
            self.screen_analyzer.start()
        if self.screen_capture:
            self.screen_capture.start()
        if self.scheduler:
            self.scheduler.start()
        if self.power_monitor:
            self.power_monitor.start()
        
        self.logger.info("=" * 50)
        self.logger.info("Assistente rodando!")
        self.logger.info("=" * 50)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Para o assistente."""
        self.running = False
        self.logger.info("Encerrando assistente...")
        
        # Parar módulos na ordem inversa
        if self.power_monitor:
            self.power_monitor.stop()
        if self.scheduler:
            self.scheduler.stop()
        if self.screen_capture:
            self.screen_capture.stop()
        if self.screen_analyzer:
            self.screen_analyzer.stop()
        if self.audio_recorder:
            self.audio_recorder.stop()
        if self.audio_transcriber:
            self.audio_transcriber.stop()
        
        self.logger.info("Assistente encerrado.")
    
    def handle_signal(self, signum, frame):
        self.stop()


def main():
    assistant = Assistant()
    
    signal.signal(signal.SIGINT, assistant.handle_signal)
    signal.signal(signal.SIGTERM, assistant.handle_signal)
    
    assistant.start()


if __name__ == "__main__":
    main()
```

---

## Critérios de Aceite

- [ ] Scheduler executa resumo no horário configurado
- [ ] Scheduler executa limpeza diária
- [ ] PowerMonitor detecta sleep/wake
- [ ] PowerMonitor detecta lock/unlock
- [ ] StartupManager cria tarefa agendada no Windows
- [ ] main.py integra todos os módulos
- [ ] App inicia e roda em background
- [ ] Ctrl+C encerra corretamente

---

## Testes Finais

```bash
# Teste completo (deixar rodando por 5 minutos)
python src/main.py

# Testar startup
python -c "
from src.system import StartupManager
sm = StartupManager()
print('Habilitado:', sm.is_enabled())
sm.enable()
print('Após enable:', sm.is_enabled())
"

# Forçar resumo imediato
python -c "
from src.system import TaskScheduler
from src.summary import SummaryGenerator

sg = SummaryGenerator()
summary = sg.generate()
print(summary)
"
```

---

## Conclusão

Com esta fase completa, o app está 100% funcional:

✅ Grava áudio em background
✅ Captura e analisa tela
✅ Transcreve usando IA
✅ Gera resumo diário
✅ Envia por email
✅ Faz backup no Drive
✅ Limpa arquivos antigos
✅ Inicia com Windows
✅ Detecta sleep/wake/lock
✅ Zero interação necessária