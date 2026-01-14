"""
Analisador de screenshots usando IA com visão.
"""

from pathlib import Path
from typing import Optional
import threading
import queue

from src.api import get_openrouter_client, OpenRouterError
from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class ScreenAnalyzer:
    """Analisa screenshots usando modelo de visão."""
    
    DEFAULT_PROMPT = """Analise esta screenshot e descreva brevemente:
1. Qual aplicativo/site está aberto
2. O que o usuário está fazendo
3. Qualquer texto importante visível

Seja conciso (máximo 3 linhas)."""
    
    def __init__(
        self,
        output_dir: str = "data/screen_analysis",
        model: Optional[str] = None,
        analysis_prompt: Optional[str] = None
    ):
        config = get_config()
        self.logger = setup_logger("screen_analyzer", config.get("system.log_level", "INFO"))
        
        self.output_dir = Path(output_dir)
        self.model = model or config.get("models.screen_analysis")
        self.prompt = analysis_prompt or config.get_screen_analysis_prompt()
        
        self._queue = queue.Queue()
        self._is_running = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"ScreenAnalyzer: modelo={self.model}")
    
    def _worker(self):
        """Worker que processa fila de análise."""
        client = get_openrouter_client()
        
        while self._is_running or not self._queue.empty():
            try:
                screenshot_path = self._queue.get(timeout=1.0)
                self.logger.info(f"Analisando: {screenshot_path.name}")
                
                analysis = client.analyze_image(
                    screenshot_path,
                    prompt=self.prompt,
                    model=self.model
                )
                
                self._save_analysis(screenshot_path, analysis)
                
                # Deletar screenshot após análise (economizar espaço)
                self._delete_screenshot(screenshot_path)
                
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro na análise: {e}")
    
    def _save_analysis(self, screenshot_path: Path, analysis: str):
        """Salva análise em arquivo do dia."""
        try:
            output_path = ensure_dir(self.output_dir / get_today_folder())
            analysis_file = output_path / "analise_tela.txt"
            
            timestamp = screenshot_path.stem  # Ex: "14h30m45s"
            
            with open(analysis_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}]\n{analysis}\n")
            
            self.logger.debug("Análise salva")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar análise: {e}")
    
    def _delete_screenshot(self, screenshot_path: Path):
        """Deleta screenshot após análise (se não for fazer backup)."""
        config = get_config()
        if not config.get("google_drive.backup.screenshots", False):
            try:
                screenshot_path.unlink()
                self.logger.debug(f"Screenshot deletado: {screenshot_path.name}")
            except:
                pass
    
    def start(self):
        """Inicia worker de análise."""
        if self._is_running:
            return
        
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._worker)
        self._worker_thread.start()
        self.logger.info("Analisador iniciado")
    
    def stop(self):
        """Para worker de análise."""
        self._is_running = False
        if hasattr(self, '_worker_thread'):
            self._worker_thread.join(timeout=60)
        self.logger.info("Analisador parado")
    
    def add_to_queue(self, screenshot_path: Path):
        """Adiciona screenshot à fila de análise."""
        self._queue.put(screenshot_path)
        self.logger.debug(f"Screenshot na fila: {screenshot_path.name}")
    
    def analyze_file(self, screenshot_path: Path) -> str:
        """Analisa screenshot diretamente (síncrono)."""
        client = get_openrouter_client()
        return client.analyze_image(screenshot_path, prompt=self.prompt, model=self.model)
    
    def get_queue_size(self) -> int:
        """Retorna tamanho da fila."""
        return self._queue.qsize()
    
    def get_today_analysis(self) -> str:
        """Obtém todas as análises do dia."""
        analysis_file = self.output_dir / get_today_folder() / "analise_tela.txt"
        return analysis_file.read_text(encoding="utf-8") if analysis_file.exists() else ""
