#!/usr/bin/env python3
"""
Sistema de Notificaciones Telegram para Fuzzing
Notifica alertas críticas y reportes automáticos
"""

import os
import json
import sqlite3
import requests
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path

class TelegramNotifier:
    """Gestor de notificaciones de Telegram"""
    
    def __init__(self, bot_token, chat_ids):
        self.bot_token = bot_token
        self.chat_ids = chat_ids if isinstance(chat_ids, list) else [chat_ids]
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, message, parse_mode='HTML', priority='normal'):
        """Enviar mensaje a todos los chats configurados"""
        success = True
        
        for chat_id in self.chat_ids:
            try:
                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': True
                }
                
                response = requests.post(f"{self.api_url}/sendMessage", data=data, timeout=10)
                
                if response.status_code == 200:
                    self.logger.info(f"Mensaje enviado a chat {chat_id}")
                else:
                    self.logger.error(f"Error enviando mensaje a chat {chat_id}: {response.text}")
                    success = False
                    
            except Exception as e:
                self.logger.error(f"Excepción enviando mensaje a {chat_id}: {str(e)}")
                success = False
        
        return success
    
    def send_critical_alert(self, finding):
        """Enviar alerta crítica"""
        emoji = "🚨" if finding.get('is_critical') else "⚠️"
        
        message = f"""
{emoji} <b>ALERTA DE SEGURIDAD</b> {emoji}

🌐 <b>Dominio:</b> {finding.get('domain', 'N/A')}
🔗 <b>URL:</b> <code>{finding.get('url', 'N/A')}</code>
📁 <b>Ruta:</b> <code>{finding.get('path', 'N/A')}</code>
📊 <b>Código HTTP:</b> {finding.get('status_code', 'N/A')}
⏰ <b>Detectado:</b> {finding.get('timestamp', datetime.now()).strftime('%d/%m/%Y %H:%M:%S')}

{f"🔴 <b>CRÍTICO:</b> Requiere atención inmediata" if finding.get('is_critical') else "🟡 <b>ADVERTENCIA:</b> Revisar cuando sea posible"}

🔗 <a href="http://localhost:5000/findings">Ver en Dashboard</a>
        """.strip()
        
        return self.send_message(message, priority='high')
    
    def send_summary_report(self, stats):
        """Enviar reporte resumen"""
        message = f"""
📊 <b>REPORTE DE SEGURIDAD</b>
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

📈 <b>Estadísticas:</b>
• Alertas pendientes: {stats.get('pending_alerts', 0)}
• Hallazgos críticos (24h): {stats.get('critical_24h', 0)}
• Dominios activos: {stats.get('active_domains', 0)}

🔗 <a href="http://localhost:5000">Ver Dashboard Completo</a>
        """.strip()
        
        return self.send_message(message)
    
    def send_no_findings_report(self):
        """Enviar reporte de 'sin novedades'"""
        message = f"""
✅ <b>REPORTE SIN NOVEDADES</b>
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

No se han detectado nuevas alertas críticas en las últimas horas.
Sistema funcionando correctamente.

🔗 <a href="http://localhost:5000">Ver Dashboard</a>
        """.strip()
        
        return self.send_message(message)

class EmailNotifier:
    """Gestor de notificaciones por email"""
    
    def __init__(self, smtp_server, smtp_port, username, password, recipients):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients if isinstance(recipients, list) else [recipients]
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, subject, body, is_html=False):
        """Enviar email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html' if is_html else 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email enviado: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando email: {str(e)}")
            return False
    
    def send_critical_alert_email(self, finding):
        """Enviar alerta crítica por email"""
        subject = f"🚨 ALERTA CRÍTICA DE SEGURIDAD - {finding.get('domain', 'N/A')}"
        
        body = f"""
        <html>
        <body>
            <h2 style="color: red;">ALERTA CRÍTICA DE SEGURIDAD</h2>
            
            <table border="1" cellpadding="10">
                <tr><td><strong>Dominio:</strong></td><td>{finding.get('domain', 'N/A')}</td></tr>
                <tr><td><strong>URL:</strong></td><td>{finding.get('url', 'N/A')}</td></tr>
                <tr><td><strong>Ruta:</strong></td><td>{finding.get('path', 'N/A')}</td></tr>
                <tr><td><strong>Código HTTP:</strong></td><td>{finding.get('status_code', 'N/A')}</td></tr>
                <tr><td><strong>Detectado:</strong></td><td>{finding.get('timestamp', datetime.now()).strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
            </table>
            
            <p><strong>Esta alerta requiere atención inmediata.</strong></p>
            
            <p><a href="http://localhost:5000/findings">Ver en Dashboard</a></p>
        </body>
        </html>
        """
        
        return self.send_email(subject, body, is_html=True)

class NotificationManager:
    """Gestor principal de notificaciones"""
    
    def __init__(self, config_file="data/notifications_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_notifiers()
        self.logger = logging.getLogger(__name__)
        self.db_path = "data/fuzzing.db"
    
    def load_config(self):
        """Cargar configuración de notificaciones"""
        default_config = {
            "telegram": {
                "enabled": True,
                "bot_token": "YOUR_BOT_TOKEN_HERE",
                "chat_ids": ["YOUR_CHAT_ID_HERE"]
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your_email@gmail.com",
                "password": "your_app_password",
                "recipients": ["security@company.com"]
            },
            "thresholds": {
                "critical_immediate": True,
                "batch_summary_hours": [9, 14],
                "no_findings_hours": [9, 14]
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_config.items():
                        if key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                self.logger.error(f"Error cargando config: {str(e)}")
        
        # Crear archivo de config si no existe
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def setup_notifiers(self):
        """Configurar notificadores"""
        self.telegram_notifier = None
        self.email_notifier = None
        
        # Configurar Telegram
        if self.config['telegram']['enabled']:
            try:
                self.telegram_notifier = TelegramNotifier(
                    self.config['telegram']['bot_token'],
                    self.config['telegram']['chat_ids']
                )
            except Exception as e:
                self.logger.error(f"Error configurando Telegram: {str(e)}")
        
        # Configurar Email
        if self.config['email']['enabled']:
            try:
                self.email_notifier = EmailNotifier(
                    self.config['email']['smtp_server'],
                    self.config['email']['smtp_port'],
                    self.config['email']['username'],
                    self.config['email']['password'],
                    self.config['email']['recipients']
                )
            except Exception as e:
                self.logger.error(f"Error configurando Email: {str(e)}")
    
    def get_stats_from_db(self):
        """Obtener estadísticas de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Alertas pendientes
                cursor.execute("SELECT COUNT(*) FROM alertas WHERE estado = 'pendiente'")
                pending_alerts = cursor.fetchone()[0]
                
                # Hallazgos críticos últimas 24h
                cursor.execute('''
                    SELECT COUNT(*) FROM hallazgos 
                    WHERE es_critico = 1 AND fecha_descubierto > datetime('now', '-1 day')
                ''')
                critical_24h = cursor.fetchone()[0]
                
                # Total de dominios activos
                cursor.execute("SELECT COUNT(*) FROM dominios WHERE activo = 1")
                active_domains = cursor.fetchone()[0]
                
                return {
                    'pending_alerts': pending_alerts,
                    'critical_24h': critical_24h,
                    'active_domains': active_domains
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo stats: {str(e)}")
            return {'pending_alerts': 0, 'critical_24h': 0, 'active_domains': 0}
    
    def notify_critical_finding(self, finding):
        """Notificar hallazgo crítico inmediatamente"""
        if not self.config['thresholds']['critical_immediate']:
            return
        
        success = True
        
        # Telegram
        if self.telegram_notifier:
            if not self.telegram_notifier.send_critical_alert(finding):
                success = False
        
        # Email
        if self.email_notifier:
            if not self.email_notifier.send_critical_alert_email(finding):
                success = False
        
        return success
    
    def send_summary_report(self):
        """Enviar reporte resumen"""
        stats = self.get_stats_from_db()
        
        success = True
        
        # Telegram
        if self.telegram_notifier:
            if not self.telegram_notifier.send_summary_report(stats):
                success = False
        
        return success
    
    def send_no_findings_report(self):
        """Enviar reporte de sin novedades"""
        stats = self.get_stats_from_db()
        
        # Solo enviar si realmente no hay alertas pendientes
        if stats['pending_alerts'] == 0 and stats['critical_24h'] == 0:
            if self.telegram_notifier:
                return self.telegram_notifier.send_no_findings_report()
        
        return True
    
    def should_send_scheduled_report(self):
        """Verificar si debe enviar reporte programado"""
        current_hour = datetime.now().hour
        return current_hour in self.config['thresholds']['batch_summary_hours']

# Script para ejecutar desde cron
def main():
    """Función principal para ejecutar notificaciones"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Notificaciones')
    parser.add_argument('--type', choices=['critical', 'summary', 'no-findings', 'test'], 
                       required=True, help='Tipo de notificación')
    parser.add_argument('--finding', help='JSON del hallazgo para alertas críticas')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    notifier = NotificationManager()
    
    if args.type == 'critical' and args.finding:
        finding = json.loads(args.finding)
        notifier.notify_critical_finding(finding)
    
    elif args.type == 'summary':
        notifier.send_summary_report()
    
    elif args.type == 'no-findings':
        notifier.send_no_findings_report()
    
    elif args.type == 'test':
        test_finding = {
            'domain': 'example.com',
            'url': 'https://example.com/admin/',
            'path': 'admin/',
            'status_code': 200,
            'is_critical': True,
            'timestamp': datetime.now()
        }
        notifier.notify_critical_finding(test_finding)

if __name__ == "__main__":
    main()