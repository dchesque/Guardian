# FASE 05 - Storage e Delivery

## Objetivo
Implementar integração com Google Drive, envio de email e geração de resumo diário.

## Duração Estimada
3 horas

## Pré-requisitos
- Fases 01-04 completas
- Credenciais do Google Drive configuradas
- Senha de app do Gmail configurada

---

## Entregas

### 1. src/storage/drive_manager.py

```python
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
                creds = pickle.load(token)
        
        # Renovar ou criar credenciais
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file.exists():
                    self.logger.error(f"Arquivo de credenciais não encontrado: {self.credentials_file}")
                    self.enabled = False
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Salvar token
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        self.logger.info("Autenticado no Google Drive")
    
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
```

---

### 2. src/delivery/email_sender.py

```python
"""
Envio de emails com resumo diário.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import get_today_folder


class EmailSender:
    """Envia emails via SMTP."""
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("email_sender", config.get("system.log_level", "INFO"))
        
        self.enabled = config.get("email.enabled", False)
        self.smtp_server = config.get("email.smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("email.smtp_port", 587)
        self.use_tls = config.get("email.use_tls", True)
        self.sender_email = config.get("email.sender_email")
        self.sender_password = config.get("email.sender_password")
        self.recipient_email = config.get("email.recipient_email")
        
        self.send_on_error = config.get("email.send_on_error", True)
    
    def send(
        self,
        subject: str,
        body: str,
        is_html: bool = False,
        recipient: Optional[str] = None
    ) -> bool:
        """
        Envia email.
        
        Args:
            subject: Assunto
            body: Corpo do email
            is_html: Se True, corpo é HTML
            recipient: Destinatário (default: config)
            
        Returns:
            True se enviado com sucesso
        """
        if not self.enabled:
            self.logger.debug("Email desativado")
            return False
        
        recipient = recipient or self.recipient_email
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            self.logger.info(f"Email enviado: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def send_daily_summary(self, summary: str) -> bool:
        """Envia resumo diário."""
        today = get_today_folder()
        subject = f"📋 Resumo do dia {today}"
        
        # Converter markdown para HTML básico
        html_body = self._markdown_to_html(summary)
        
        return self.send(subject, html_body, is_html=True)
    
    def send_error_alert(self, error_message: str) -> bool:
        """Envia alerta de erro."""
        if not self.send_on_error:
            return False
        
        subject = "⚠️ Erro no Voice Screen Assistant"
        body = f"Ocorreu um erro no assistente:\n\n{error_message}"
        
        return self.send(subject, body)
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Converte markdown básico para HTML."""
        html = markdown
        
        # Headers
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('## '):
                lines[i] = f"<h2>{line[3:]}</h2>"
            elif line.startswith('# '):
                lines[i] = f"<h1>{line[2:]}</h1>"
        html = '\n'.join(lines)
        
        # Bold
        import re
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Line breaks
        html = html.replace('\n', '<br>\n')
        
        # Wrap in basic HTML
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        {html}
        </body>
        </html>
        """
    
    def test_connection(self) -> bool:
        """Testa conexão SMTP."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
            self.logger.info("Conexão SMTP OK")
            return True
        except Exception as e:
            self.logger.error(f"Erro na conexão SMTP: {e}")
            return False
```

---

### 3. src/summary/generator.py

```python
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
        
        if not transcriptions and not screen_analysis:
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
```

---

### 4. src/storage/__init__.py e src/delivery/__init__.py e src/summary/__init__.py

```python
# src/storage/__init__.py
from src.storage.drive_manager import DriveManager
__all__ = ["DriveManager"]

# src/delivery/__init__.py
from src.delivery.email_sender import EmailSender
__all__ = ["EmailSender"]

# src/summary/__init__.py
from src.summary.generator import SummaryGenerator
__all__ = ["SummaryGenerator"]
```

---

## Critérios de Aceite

- [ ] DriveManager autentica com Google Drive
- [ ] Upload de arquivos funciona
- [ ] Estrutura de pastas por data criada corretamente
- [ ] Limpeza de arquivos antigos funciona
- [ ] EmailSender envia emails via SMTP
- [ ] Resumo diário enviado por email
- [ ] SummaryGenerator combina transcrições e análises
- [ ] Resumo usa prompt personalizado
- [ ] Arquivos salvos localmente e no Drive

---

## Configuração do Gmail

Para usar Gmail como SMTP:

1. Ative verificação em 2 etapas na conta Google
2. Acesse: https://myaccount.google.com/apppasswords
3. Gere uma "Senha de app" para "Outro"
4. Use essa senha em `email.sender_password`

---

## Testes

```bash
# Testar conexão com Drive
python -c "
from src.storage import DriveManager
dm = DriveManager()
print('Drive conectado!' if dm.service else 'Falha')
"

# Testar envio de email
python -c "
from src.delivery import EmailSender
es = EmailSender()
es.send('Teste', 'Email de teste do assistente')
"

# Testar geração de resumo (precisa ter dados do dia)
python -c "
from src.summary import SummaryGenerator
sg = SummaryGenerator()
summary = sg.generate()
print(summary)
"
```

---

## Próxima Fase
Prossiga para **FASE-06-SISTEMA.md**.