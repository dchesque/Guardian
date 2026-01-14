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
