"""
Funções auxiliares usadas em todo o projeto.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib


def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).parent.parent.parent


def get_today_folder() -> str:
    """Retorna o nome da pasta do dia atual (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")


def get_month_folder() -> str:
    """Retorna o nome da pasta do mês atual (YYYY-MM)."""
    return datetime.now().strftime("%Y-%m")


def get_timestamp() -> str:
    """Retorna timestamp atual formatado (HHhMM)."""
    return datetime.now().strftime("%Hh%M")


def get_datetime_stamp() -> str:
    """Retorna datetime stamp completo (YYYY-MM-DD_HHhMMmSSs)."""
    return datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")


def ensure_dir(path: str | Path) -> Path:
    """
    Garante que um diretório existe, criando se necessário.
    
    Args:
        path: Caminho do diretório
        
    Returns:
        Path do diretório
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(filename: str) -> str:
    """
    Remove caracteres inválidos de um nome de arquivo.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome do arquivo sanitizado
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def file_hash(filepath: str | Path) -> str:
    """
    Calcula hash MD5 de um arquivo.
    
    Args:
        filepath: Caminho do arquivo
        
    Returns:
        Hash MD5 em hexadecimal
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para string legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "1h 30m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_size(bytes_size: int) -> str:
    """
    Formata tamanho em bytes para string legível.
    
    Args:
        bytes_size: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"
