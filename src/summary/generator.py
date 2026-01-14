"""
Gerador de resumo diário.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

from src.api import get_openrouter_client
from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder, get_project_root


class SummaryGenerator:
    """Gera resumo diário combinando transcrições e análises."""
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("summary", config.get("system.log_level", "INFO"))
        
        self.model = config.get("models.summary")
        self.prompt = config.get_prompt()
        
        root = get_project_root()
        self.transcriptions_dir = root / "data" / "transcriptions"
        self.screen_analysis_dir = root / "data" / "screen_analysis"
        self.keyboard_analysis_dir = root / "data" / "keyboard_analysis"
        self.output_dir = root / "data" / "summaries"
        
        ensure_dir(self.output_dir)
    
    def _get_transcriptions(self, date: Optional[str] = None) -> str:
        """Obtém transcrições do dia."""
        date = date or get_today_folder()
        file_path = self.transcriptions_dir / date / "transcricao.txt"
        
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""
    
    def _get_screen_analysis(self, date: Optional[str] = None) -> str:
        """Obtém análises de tela do dia."""
        date = date or get_today_folder()
        file_path = self.screen_analysis_dir / date / "analise_tela.txt"
        
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""
    
    def _get_keyboard_analysis(self, date: Optional[str] = None) -> str:
        """Obtém análises de teclado do dia."""
        date = date or get_today_folder()
        file_path = self.keyboard_analysis_dir / date / "analise_teclado.txt"
        
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""
    
    def generate(self, date: Optional[str] = None) -> str:
        """
        Gera resumo do dia.
        
        Args:
            date: Data no formato YYYY-MM-DD (default: hoje)
            
        Returns:
            Resumo gerado
        """
        date = date or get_today_folder()
        self.logger.info(f"Gerando resumo para {date}")
        
        # Coletar conteúdo
        transcriptions = self._get_transcriptions(date)
        screen_analysis = self._get_screen_analysis(date)
        keyboard_analysis = self._get_keyboard_analysis(date)
        
        if not transcriptions and not screen_analysis and not keyboard_analysis:
            self.logger.warning("Nenhum conteúdo para resumir")
            return "Nenhum conteúdo foi capturado hoje."
        
        # Montar conteúdo
        content_parts = []
        
        if transcriptions:
            content_parts.append("### TRANSCRIÇÕES DE ÁUDIO ###")
            content_parts.append(transcriptions)
        
        if screen_analysis:
            content_parts.append("\n### ANÁLISES DE TELA ###")
            content_parts.append(screen_analysis)
        
        if keyboard_analysis:
            content_parts.append("\n### ANÁLISES DE TECLADO ###")
            content_parts.append(keyboard_analysis)
        
        content = "\n".join(content_parts)
        
        # Gerar resumo via API
        client = get_openrouter_client()
        summary = client.generate_summary(content, custom_prompt=self.prompt, model=self.model)
        
        # Salvar
        self._save_summary(summary, date)
        
        self.logger.info(f"Resumo gerado: {len(summary)} caracteres")
        return summary
    
    def _save_summary(self, summary: str, date: str):
        """Salva resumo em arquivo."""
        output_path = ensure_dir(self.output_dir / date)
        summary_file = output_path / "resumo.md"
        
        header = f"""# Resumo do dia {date}
*Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}*

---

"""
        summary_file.write_text(header + summary, encoding="utf-8")
        self.logger.info(f"Resumo salvo: {summary_file}")
    
    def get_summary(self, date: Optional[str] = None) -> str:
        """Obtém resumo salvo do dia."""
        date = date or get_today_folder()
        summary_file = self.output_dir / date / "resumo.md"
        
        if summary_file.exists():
            return summary_file.read_text(encoding="utf-8")
        return ""
