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
from src.keyboard import KeyboardRecorder, KeyboardAnalyzer
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
        self.keyboard_recorder = None
        self.keyboard_analyzer = None
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
            self.logger.info("Guardian v1.0")
            self.logger.info("=" * 50)
            
            # Setup módulos
            if self.config.audio_enabled:
                self._setup_audio()
            
            if self.config.screen_enabled:
                self._setup_screen()
            
            if self.config.keyboard_enabled:
                self._setup_keyboard()
            
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
    
    def _setup_keyboard(self):
        self.logger.info("Configurando módulo de teclado...")
        interval = self.config.get("keyboard.save_interval_minutes", 5)
        
        self.keyboard_analyzer = KeyboardAnalyzer()
        self.keyboard_recorder = KeyboardRecorder(
            save_interval_minutes=interval,
            on_log_ready=self._on_keyboard_log_ready
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
        self.logger.info(f"Teclado: {'✓' if self.config.keyboard_enabled else '✗'}")
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
            
    # Callbacks de teclado
    def _on_keyboard_log_ready(self, log_path: Path):
        self.logger.debug(f"Log de teclado pronto: {log_path.name}")
        
        if self.keyboard_analyzer:
            self.keyboard_analyzer.add_to_queue(log_path)
    
    # Callbacks de energia
    def _on_sleep(self):
        self.logger.info("Pausando para sleep...")
        if self.audio_recorder:
            self.audio_recorder.pause()
        if self.screen_capture:
            self.screen_capture.pause()
        if self.keyboard_recorder:
            self.keyboard_recorder.pause()
    
    def _on_wake(self):
        self.logger.info("Retomando após wake...")
        if self.audio_recorder:
            self.audio_recorder.resume()
        if self.screen_capture:
            self.screen_capture.resume()
        if self.keyboard_recorder:
            self.keyboard_recorder.resume()
    
    def _on_lock(self):
        self.logger.info("Pausando (tela bloqueada)...")
        if self.audio_recorder:
            self.audio_recorder.pause()
        if self.screen_capture:
            self.screen_capture.pause()
        if self.keyboard_recorder:
            self.keyboard_recorder.pause()
    
    def _on_unlock(self):
        self.logger.info("Retomando (tela desbloqueada)...")
        if self.audio_recorder:
            self.audio_recorder.resume()
        if self.screen_capture:
            self.screen_capture.resume()
        if self.keyboard_recorder:
            self.keyboard_recorder.resume()
    
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
        if self.keyboard_analyzer:
            self.keyboard_analyzer.start()
        if self.keyboard_recorder:
            self.keyboard_recorder.start()
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
        if self.keyboard_recorder:
            self.keyboard_recorder.stop()
        if self.keyboard_analyzer:
            self.keyboard_analyzer.stop()
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
