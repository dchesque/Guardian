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
    
    TASK_NAME = "GuardianAssistant"
    
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
