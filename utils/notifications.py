# utils/notifications.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from utils.logger import get_logger
from integrations.telegram_bot import TelegramBot

class NotificationManager:
    """Gestor central de notificaciones"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Inicializar Telegram
        self.telegram = TelegramBot(config)
        
        # Configuración de email
        self.email_enabled = config.get('notifications.email.enabled', False)
        self.smtp_server = config.get('notifications.email.smtp_server')
        self.smtp_port = config.get('notifications.email.smtp_port', 587)
        self.email_username = config.get('notifications.email.username')
        self.email_password = config.get('notifications.email.password')
        self.recipients = config.get('notifications.email.recipients', [])
    
    def send_email(self, subject: str, body: str, recipients: List[str] = None) -> bool:
        """Enviar email"""
        if not self.email_enabled:
            return False
        
        recipients = recipients or self.recipients
        if not recipients:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_username, recipients, text)
            server.quit()
            
            self.logger.info(f"Email enviado a {len(recipients)} destinatarios")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando email: {e}")
            return False
    
    def notify_critical_finding(self, finding: Dict) -> bool:
        """Notificar hallazgo crítico"""
        success = True
        
        # Telegram
        if self.telegram.enabled:
            success &= self.telegram.send_critical_alert(finding)
        
        # Email
        if self.email_enabled:
            subject = f"🚨 Alerta Crítica: {finding['path']}"
            body = f"""
            <h2>Alerta Crítica de Seguridad</h2>
            <p><strong>URL:</strong> {finding['url']}</p>
            <p><strong>Código de estado:</strong> {finding['status_code']}</p>
            <p><strong>Ruta:</strong> {finding['path']}</p>
            <p><strong>Tamaño de contenido:</strong> {finding.get('content_length', 'N/A')} bytes</p>
            <p><strong>Tipo de contenido:</strong> {finding.get('content_type', 'N/A')}</p>
            <p><em>Esta ruta puede contener información sensible que requiere atención inmediata.</em></p>
            """
            success &= self.send_email(subject, body)
        
        return success
    
    def send_scan_report(self, stats: Dict, findings: List[Dict] = None) -> bool:
        """Enviar reporte de escaneo"""
        success = True
        
        # Telegram - solo resumen
        if self.telegram.enabled:
            success &= self.telegram.send_scan_summary(stats)
        
        # Email - reporte detallado
        if self.email_enabled and findings:
            subject = f"Reporte de Escaneo Web - {stats.get('total_domains', 0)} dominios"
            
            # Crear reporte HTML
            critical_findings = [f for f in findings if f.get('is_critical', False)]
            normal_findings = [f for f in findings if not f.get('is_critical', False)]
            
            body = f"""
            <h2>Reporte de Escaneo Web</h2>
            
            <h3>Resumen</h3>
            <ul>
                <li><strong>Dominios escaneados:</strong> {stats.get('total_domains', 0)}</li>
                <li><strong>Rutas encontradas:</strong> {stats.get('paths_found', 0)}</li>
                <li><strong>Rutas críticas:</strong> {stats.get('critical_found', 0)}</li>
                <li><strong>Duración:</strong> {stats.get('scan_duration', 0):.1f} segundos</li>
            </ul>
            """
            
            if critical_findings:
                body += "<h3>🚨 Hallazgos Críticos</h3><ul>"
                for finding in critical_findings[:10]:  # Limitar a 10
                    body += f"<li><strong>{finding['url']}</strong> [{finding['status_code']}]</li>"
                body += "</ul>"
            
            if normal_findings:
                body += f"<h3>📁 Otros Hallazgos ({len(normal_findings)})</h3>"
                body += "<p>Ver reporte completo en el dashboard web.</p>"
            
            success &= self.send_email(subject, body)
        
        return success