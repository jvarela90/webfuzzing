# integrations/telegram_bot.py
import requests
import json
from typing import Dict, List
from utils.logger import get_logger

class TelegramBot:
    """Bot de Telegram para notificaciones"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.bot_token = config.get('notifications.telegram.bot_token')
        self.chat_id = config.get('notifications.telegram.chat_id')
        self.enabled = config.get('notifications.telegram.enabled', False)
        self.critical_only = config.get('notifications.telegram.critical_only', True)
        
        if self.enabled and self.bot_token:
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Enviar mensaje a Telegram"""
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Mensaje enviado a Telegram exitosamente")
                return True
            else:
                self.logger.error(f"Error enviando mensaje a Telegram: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a Telegram: {e}")
            return False
    
    def send_critical_alert(self, finding: Dict) -> bool:
        """Enviar alerta crítica"""
        message = f"""
🚨 <b>ALERTA CRÍTICA DE SEGURIDAD</b>

<b>URL:</b> {finding['url']}
<b>Código:</b> {finding['status_code']}
<b>Ruta:</b> {finding['path']}
<b>Tamaño:</b> {finding.get('content_length', 'N/A')} bytes

⚠️ <i>Esta ruta puede contener información sensible</i>

<b>Tiempo:</b> {finding.get('discovered_at', 'Ahora')}
        """
        
        return self.send_message(message.strip())
    
    def send_scan_summary(self, stats: Dict) -> bool:
        """Enviar resumen de escaneo"""
        critical_emoji = "🔥" if stats.get('critical_found', 0) > 0 else "✅"
        
        message = f"""
{critical_emoji} <b>Resumen de Escaneo Web</b>

<b>Dominios escaneados:</b> {stats.get('total_domains', 0)}
<b>Rutas encontradas:</b> {stats.get('paths_found', 0)}
<b>Rutas críticas:</b> {stats.get('critical_found', 0)}
<b>Duración:</b> {stats.get('scan_duration', 0):.1f}s

<b>Tiempo:</b> {stats.get('timestamp', 'Ahora')}
        """
        
        return self.send_message(message.strip())
