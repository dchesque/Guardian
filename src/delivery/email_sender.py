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
