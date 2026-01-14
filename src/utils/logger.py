"""
Sistema de logging centralizado.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "assistant",
    log_level: str = "INFO",
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        name: Nome do logger
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        log_dir: Diretório para salvar logs
        
    Returns:
        Logger configurado
    """
    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo de log com data
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar handlers duplicados
    if logger.handlers:
        return logger
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console (apenas em modo debug)
    if log_level.upper() == "DEBUG":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def cleanup_old_logs(log_dir: str = "logs", retention_days: int = 7) -> int:
    """
    Remove logs mais antigos que retention_days.
    
    Args:
        log_dir: Diretório de logs
        retention_days: Dias para manter logs
        
    Returns:
        Número de arquivos removidos
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return 0
    
    cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
    removed = 0
    
    for log_file in log_path.glob("*.log"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            removed += 1
    
    return removed
