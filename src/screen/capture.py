"""
Captura de screenshots da tela.
"""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List

import mss
from PIL import Image

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class ScreenCapture:
    """Captura screenshots em intervalos configuráveis."""
    
    def __init__(
        self,
        interval_seconds: int = 30,
        output_dir: str = "data/temp_screenshots",
        on_capture_ready: Optional[Callable[[Path], None]] = None
    ):
        config = get_config()
        self.logger = setup_logger("screen_capture", config.get("system.log_level", "INFO"))
        
        self.interval = interval_seconds
        self.output_dir = Path(output_dir)
        self.on_capture_ready = on_capture_ready
        
        self.monitor_index = config.get("screen.monitor", 0)
        self.format = config.get("screen.format", "jpg")
        self.quality = config.get("screen.quality", 70)
        
        # Privacidade
        self.excluded_apps = config.get("privacy.excluded_apps", [])
        self.excluded_windows = config.get("privacy.excluded_windows", [])
        
        self.is_running = False
        self.is_paused = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"ScreenCapture: intervalo={interval_seconds}s, monitor={self.monitor_index}")
    
    def _get_active_window_title(self) -> str:
        """Obtém título da janela ativa (Windows)."""
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except:
            return ""
    
    def _should_skip_capture(self) -> bool:
        """Verifica se deve pular captura (app/janela excluída)."""
        title = self._get_active_window_title().lower()
        
        for app in self.excluded_apps:
            if app.lower() in title:
                self.logger.debug(f"Pulando captura: app excluído ({app})")
                return True
        
        for window in self.excluded_windows:
            if window.lower() in title:
                self.logger.debug(f"Pulando captura: janela excluída ({window})")
                return True
        
        return False
    
    def _capture_loop(self):
        """Loop principal de captura."""
        self.logger.info("Loop de captura iniciado")
        
        with mss.mss() as sct:
            monitors = sct.monitors
            
            # Selecionar monitor (0 = todos, 1+ = específico)
            if self.monitor_index < len(monitors):
                monitor = monitors[self.monitor_index]
            else:
                monitor = monitors[1]  # Monitor principal
            
            while self.is_running:
                try:
                    if self.is_paused or self._should_skip_capture():
                        time.sleep(self.interval)
                        continue
                    
                    # Capturar
                    screenshot = sct.grab(monitor)
                    
                    # Converter para PIL Image
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    
                    # Salvar
                    filepath = self._save_screenshot(img)
                    
                    if filepath and self.on_capture_ready:
                        self.on_capture_ready(filepath)
                    
                    time.sleep(self.interval)
                    
                except Exception as e:
                    self.logger.error(f"Erro na captura: {e}")
                    time.sleep(self.interval)
        
        self.logger.info("Loop de captura encerrado")
    
    def _save_screenshot(self, img: Image.Image) -> Optional[Path]:
        """Salva screenshot em arquivo."""
        try:
            today_dir = ensure_dir(self.output_dir / get_today_folder())
            timestamp = datetime.now().strftime("%Hh%Mm%Ss")
            
            if self.format == "jpg":
                filepath = today_dir / f"{timestamp}.jpg"
                img.save(filepath, "JPEG", quality=self.quality)
            else:
                filepath = today_dir / f"{timestamp}.png"
                img.save(filepath, "PNG")
            
            self.logger.debug(f"Screenshot salvo: {filepath.name}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {e}")
            return None
    
    def start(self) -> bool:
        """Inicia captura de tela."""
        if self.is_running:
            return False
        
        self.is_running = True
        self.is_paused = False
        
        self._capture_thread = threading.Thread(target=self._capture_loop)
        self._capture_thread.start()
        
        self.logger.info("Captura de tela iniciada")
        return True
    
    def stop(self):
        """Para captura de tela."""
        if not self.is_running:
            return
        
        self.is_running = False
        if hasattr(self, '_capture_thread'):
            self._capture_thread.join(timeout=10)
        
        self.logger.info("Captura de tela parada")
    
    def pause(self):
        """Pausa captura."""
        self.is_paused = True
        self.logger.info("Captura pausada")
    
    def resume(self):
        """Retoma captura."""
        self.is_paused = False
        self.logger.info("Captura retomada")
    
    def capture_once(self) -> Optional[Path]:
        """Captura uma única screenshot."""
        with mss.mss() as sct:
            monitors = sct.monitors
            monitor = monitors[min(self.monitor_index, len(monitors) - 1)]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return self._save_screenshot(img)
    
    def get_monitors(self) -> List[dict]:
        """Lista monitores disponíveis."""
        with mss.mss() as sct:
            return [{'id': i, 'size': f"{m['width']}x{m['height']}"} for i, m in enumerate(sct.monitors)]
