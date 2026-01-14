"""
Gerenciador do Google Drive.
Upload, download e limpeza de arquivos.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import get_project_root, get_today_folder, get_month_folder


SCOPES = ['https://www.googleapis.com/auth/drive.file']


class DriveManager:
    """Gerencia uploads e organização no Google Drive."""
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("drive_manager", config.get("system.log_level", "INFO"))
        
        self.enabled = config.get("google_drive.enabled", False)
        self.folder_name = config.get("google_drive.folder_name", "Assistente IA")
        
        # Caminhos das credenciais
        root = get_project_root()
        self.credentials_file = root / config.get("google_drive.credentials_file", "config/credentials/google_drive.json")
        self.token_file = root / config.get("google_drive.token_file", "config/credentials/token.json")
        
        # Configurações de backup
        self.backup_config = {
            'audio': config.get("google_drive.backup.audio", True),
            'screenshots': config.get("google_drive.backup.screenshots", False),
            'transcriptions': config.get("google_drive.backup.transcriptions", True),
            'screen_analysis': config.get("google_drive.backup.screen_analysis", True),
            'summaries': config.get("google_drive.backup.summaries", True),
        }
        
        # Retenção
        self.audio_retention = config.get("google_drive.cleanup.audio_retention_days", 30)
        self.screenshots_retention = config.get("google_drive.cleanup.screenshots_retention_days", 7)
        
        self.service = None
        self._folder_cache = {}
        
        if self.enabled:
            self._authenticate()
    
    def _authenticate(self):
        """Autentica com Google Drive API."""
        creds = None
        
        # Carregar token existente
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                try:
                    creds = pickle.load(token)
                except Exception:
                    self.logger.warning("Token inválido ou corrompido")
        
        # Renovar ou criar credenciais
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Erro ao renovar token: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_file.exists():
                    self.logger.error(f"Arquivo de credenciais não encontrado: {self.credentials_file}")
                    self.enabled = False
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.logger.error(f"Erro na autenticação: {e}")
                    self.enabled = False
                    return
            
            # Salvar token
            try:
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                self.logger.error(f"Erro ao salvar token: {e}")
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            self.logger.info("Autenticado no Google Drive")
        except Exception as e:
            self.logger.error(f"Erro ao criar serviço Drive: {e}")
            self.enabled = False
    
    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Obtém ou cria pasta no Drive."""
        cache_key = f"{parent_id}/{folder_name}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        
        # Buscar pasta existente
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
        else:
            # Criar pasta
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(body=metadata, fields='id').execute()
            folder_id = folder['id']
            self.logger.info(f"Pasta criada: {folder_name}")
        
        self._folder_cache[cache_key] = folder_id
        return folder_id
    
    def _get_day_folder(self, date: Optional[str] = None) -> str:
        """Obtém pasta do dia (cria estrutura se necessário)."""
        date = date or get_today_folder()
        month = date[:7]  # YYYY-MM
        
        root_id = self._get_or_create_folder(self.folder_name)
        month_id = self._get_or_create_folder(month, root_id)
        day_id = self._get_or_create_folder(date, month_id)
        
        return day_id
    
    def upload_file(
        self,
        local_path: Path,
        subfolder: Optional[str] = None,
        date: Optional[str] = None
    ) -> Optional[str]:
        """
        Faz upload de arquivo para o Drive.
        
        Args:
            local_path: Caminho local do arquivo
            subfolder: Subpasta dentro do dia (ex: "audio")
            date: Data da pasta (default: hoje)
            
        Returns:
            ID do arquivo no Drive ou None se falha
        """
        if not self.enabled or not self.service:
            return None
        
        if not local_path.exists():
            self.logger.error(f"Arquivo não existe: {local_path}")
            return None
        
        try:
            # Obter pasta de destino
            day_folder = self._get_day_folder(date)
            
            if subfolder:
                parent_id = self._get_or_create_folder(subfolder, day_folder)
            else:
                parent_id = day_folder
            
            # Determinar MIME type
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.jpg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
            }
            mime_type = mime_types.get(local_path.suffix.lower(), 'application/octet-stream')
            
            # Upload
            metadata = {
                'name': local_path.name,
                'parents': [parent_id]
            }
            
            media = MediaFileUpload(str(local_path), mimetype=mime_type)
            file = self.service.files().create(
                body=metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            self.logger.info(f"Upload: {local_path.name}")
            return file['id']
            
        except Exception as e:
            self.logger.error(f"Erro no upload: {e}")
            return None
    
    def upload_audio(self, audio_path: Path) -> Optional[str]:
        """Upload de arquivo de áudio."""
        if not self.backup_config['audio']:
            return None
        return self.upload_file(audio_path, subfolder="audio")
    
    def upload_transcription(self, transcription_path: Path) -> Optional[str]:
        """Upload de transcrição."""
        if not self.backup_config['transcriptions']:
            return None
        return self.upload_file(transcription_path)
    
    def upload_screen_analysis(self, analysis_path: Path) -> Optional[str]:
        """Upload de análise de tela."""
        if not self.backup_config['screen_analysis']:
            return None
        return self.upload_file(analysis_path)
    
    def upload_summary(self, summary_path: Path) -> Optional[str]:
        """Upload de resumo."""
        if not self.backup_config['summaries']:
            return None
        return self.upload_file(summary_path)
    
    def cleanup_old_files(self):
        """Remove arquivos antigos do Drive."""
        if not self.enabled or not self.service:
            return
        
        self.logger.info("Iniciando limpeza de arquivos antigos...")
        
        # Limpar áudios antigos
        if self.backup_config['audio']:
            self._cleanup_folder_type("audio", self.audio_retention)
        
        # Limpar screenshots antigos
        if self.backup_config['screenshots']:
            self._cleanup_folder_type("screenshots", self.screenshots_retention)
    
    def _cleanup_folder_type(self, folder_type: str, retention_days: int):
        """Limpa arquivos de um tipo específico mais antigos que retention_days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            # Buscar pasta raiz
            root_id = self._get_or_create_folder(self.folder_name)
            
            # Listar pastas de mês
            query = f"'{root_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            
            deleted_count = 0
            for month_folder in results.get('files', []):
                # Listar pastas de dia
                query = f"'{month_folder['id']}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
                days = self.service.files().list(q=query, fields="files(id, name)").execute()
                
                for day_folder in days.get('files', []):
                    if day_folder['name'] < cutoff_str:
                        # Buscar subpasta do tipo
                        query = f"'{day_folder['id']}' in parents and name='{folder_type}' and trashed=false"
                        subfolders = self.service.files().list(q=query, fields="files(id)").execute()
                        
                        for subfolder in subfolders.get('files', []):
                            # Deletar conteúdo
                            self.service.files().delete(fileId=subfolder['id']).execute()
                            deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(f"Limpeza: {deleted_count} pastas de {folder_type} removidas")
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")
