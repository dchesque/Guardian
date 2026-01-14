"""
Transcritor de áudio usando OpenRouter API.
"""

from pathlib import Path
from typing import Optional
import threading
import queue

from src.api import get_openrouter_client, OpenRouterError
from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class AudioTranscriber:
    """Transcritor de áudio com fila de processamento."""
    
    def __init__(self, output_dir: str = "data/transcriptions", model: Optional[str] = None):
        config = get_config()
        self.logger = setup_logger("transcriber", config.get("system.log_level", "INFO"))
        
        self.output_dir = Path(output_dir)
        self.model = model or config.get("models.transcription")
        
        self._queue = queue.Queue()
        self._is_running = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"Transcritor: modelo={self.model}")
    
    def _worker(self):
        client = get_openrouter_client()
        
        while self._is_running or not self._queue.empty():
            try:
                audio_path = self._queue.get(timeout=1.0)
                self.logger.info(f"Transcrevendo: {audio_path.name}")
                
                transcription = client.transcribe_audio(audio_path, model=self.model, language="pt")
                self._save_transcription(audio_path, transcription)
                
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro: {e}")
    
    def _save_transcription(self, audio_path: Path, transcription: str):
        try:
            output_path = ensure_dir(self.output_dir / get_today_folder())
            transcript_file = output_path / "transcricao.txt"
            
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{audio_path.stem}]\n{transcription}\n")
            
            self.logger.info(f"Transcrição salva")
        except Exception as e:
            self.logger.error(f"Erro ao salvar: {e}")
    
    def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._worker)
        self._worker_thread.start()
    
    def stop(self):
        self._is_running = False
        if hasattr(self, '_worker_thread'):
            self._worker_thread.join(timeout=30)
    
    def add_to_queue(self, audio_path: Path):
        self._queue.put(audio_path)
    
    def transcribe_file(self, audio_path: Path) -> str:
        return get_openrouter_client().transcribe_audio(audio_path, model=self.model)
    
    def get_today_transcription(self) -> str:
        transcript_file = self.output_dir / get_today_folder() / "transcricao.txt"
        return transcript_file.read_text(encoding="utf-8") if transcript_file.exists() else ""
