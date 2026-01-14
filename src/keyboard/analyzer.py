"""
Analisador de logs de teclado usando IA.
"""

from pathlib import Path
from typing import Optional
import threading
import queue

from src.api import get_openrouter_client
from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder

class KeyboardAnalyzer:
    """Resume logs de teclado usando modelos de texto."""
    
    def __init__(
        self,
        output_dir: str = "data/keyboard_analysis",
        model: Optional[str] = None,
        analysis_prompt: Optional[str] = None
    ):
        config = get_config()
        self.logger = setup_logger("keyboard_analyzer", config.get("system.log_level", "INFO"))
        
        self.output_dir = Path(output_dir)
        self.model = model or config.get("models.summary") # Usar o modelo de resumo por padrão
        self.prompt = analysis_prompt or config.get_keyboard_analysis_prompt()
        
        self._queue = queue.Queue()
        self._is_running = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"KeyboardAnalyzer: modelo={self.model}")
        
    def _worker(self):
        """Worker que processa fila de análise."""
        client = get_openrouter_client()
        
        while self._is_running or not self._queue.empty():
            try:
                log_path = self._queue.get(timeout=1.0)
                self.logger.info(f"Analisando log de teclado: {log_path.name}")
                
                # Ler o conteúdo do log
                content = log_path.read_text(encoding="utf-8")
                
                if not content.strip():
                    self._queue.task_done()
                    continue
                
                # Chamar a API para resumir
                analysis = client.generate_summary(
                    content,
                    custom_prompt=self.prompt,
                    model=self.model
                )
                
                self._save_analysis(analysis)
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro na análise de teclado: {e}")
                
    def _save_analysis(self, analysis: str):
        """Salva análise em arquivo do dia."""
        try:
            output_path = ensure_dir(self.output_dir / get_today_folder())
            analysis_file = output_path / "analise_teclado.txt"
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Hh%Mm%Ss")
            
            with open(analysis_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}]\n{analysis}\n")
            
            self.logger.debug("Análise de teclado salva")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar análise de teclado: {e}")
            
    def start(self):
        """Inicia worker de análise."""
        if self._is_running:
            return
            
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        self.logger.info("Analisador de teclado iniciado")
        
    def stop(self):
        """Para worker de análise."""
        self._is_running = False
        if hasattr(self, '_worker_thread'):
            self._worker_thread.join(timeout=30)
        self.logger.info("Analisador de teclado parado")
        
    def add_to_queue(self, log_path: Path):
        """Adiciona log à fila de análise."""
        self._queue.put(log_path)
        self.logger.debug(f"Log de teclado na fila: {log_path.name}")
        
    def get_today_analysis(self) -> str:
        """Obtém todas as análises do dia."""
        analysis_file = self.output_dir / get_today_folder() / "analise_teclado.txt"
        return analysis_file.read_text(encoding="utf-8") if analysis_file.exists() else ""
