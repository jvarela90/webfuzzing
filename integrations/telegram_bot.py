# integrations/telegram_bot.py
"""
Bot de Telegram para notificaciones de WebFuzzing Pro
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime
import threading
import queue

class TelegramBot:
    """Bot de Telegram para notificaciones"""
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializar bot de Telegram"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuración del bot
        self.bot_token = self.config.get('telegram.bot_token', '')
        self.chat_ids = self.config.get('telegram.chat_ids', [])
        self.enabled = self.config.get('telegram.enabled', False)
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Queue para mensajes
        self.message_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        
        # Verificar configuración
        if self.enabled and self.bot_token:
            self.is_available = self._verify_bot_token()
        else:
            self.is_available = False
    
    def _verify_bot_token(self) -> bool:
        """Verificar que el token del bot sea válido"""
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    self.logger.info(f"Bot de Telegram verificado: {bot_info.get('username', 'Unknown')}")
                    return True
                else:
                    self.logger.error(f"Error verificando bot: {data.get('description', 'Unknown error')}")
                    return False
            else:
                self.logger.error(f"Error HTTP verificando bot: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verificando bot de Telegram: {e}")
            return False
    
    def start(self) -> None:
        """Iniciar el procesador de mensajes"""
        if not self.is_available:
            self.logger.warning("Bot de Telegram no disponible, no se puede iniciar")
            return
        
        if self.is_running:
            self.logger.warning("Bot de Telegram ya está ejecutándose")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._message_worker, daemon=True)
        self.worker_thread.start()
        self.logger.info("Bot de Telegram iniciado")
    
    def stop(self) -> None:
        """Detener el procesador de mensajes"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("Bot de Telegram detenido")
    
    def _message_worker(self) -> None:
        """Worker thread para procesar mensajes"""
        while self.is_running:
            try:
                # Obtener mensaje de la queue con timeout
                message_data = self.message_queue.get(timeout=1)
                
                # Enviar mensaje
                self._send_message_sync(
                    message_data['text'],
                    message_data.get('chat_id'),
                    message_data.get('parse_mode', 'HTML'),
                    message_data.get('disable_web_page_preview', True)
                )
                
                # Marcar tarea como completada
                self.message_queue.task_done()
                
                # Pequeña pausa para evitar rate limiting
                time.sleep(0.1)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error en worker de mensajes: {e}")
                continue
    
    def send_notification(self, title: str, message: str, severity: str = 'info', 
                         url: Optional[str] = None, **kwargs) -> bool:
        """
        Enviar notificación por Telegram
        
        Args:
            title: Título de la notificación
            message: Mensaje principal
            severity: Severidad (info, warning, critical)
            url: URL relacionada (opcional)
            **kwargs: Parámetros adicionales
        
        Returns:
            bool: True si se encoló correctamente
        """
        if not self.is_available:
            self.logger.warning("Bot de Telegram no disponible")
            return False
        
        # Formatear mensaje
        formatted_message = self._format_notification(title, message, severity, url, **kwargs)
        
        # Encolar mensaje
        try:
            message_data = {
                'text': formatted_message,
                'chat_id': kwargs.get('chat_id'),
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            self.message_queue.put(message_data, timeout=5)
            return True
            
        except queue.Full:
            self.logger.error("Cola de mensajes de Telegram llena")
            return False
        except Exception as e:
            self.logger.error(f"Error encolando mensaje: {e}")
            return False
    
    def _format_notification(self, title: str, message: str, severity: str, 
                           url: Optional[str] = None, **kwargs) -> str:
        """Formatear notificación para Telegram"""
        
        # Emojis por severidad
        severity_emojis = {
            'info': '🔍',
            'warning': '⚠️',
            'critical': '🚨',
            'success': '✅',
            'error': '❌'
        }
        
        emoji = severity_emojis.get(severity, '📢')
        
        # Construir mensaje
        formatted = f"{emoji} <b>{title}</b>\n\n"
        formatted += f"{message}\n"
        
        # Agregar información adicional
        if url:
            formatted += f"\n🔗 <a href='{url}'>Ver detalles</a>"
        
        # Agregar timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted += f"\n\n⏰ {timestamp}"
        
        # Agregar información del dominio si está disponible
        domain = kwargs.get('domain')
        if domain:
            formatted += f"\n🌐 Dominio: <code>{domain}</code>"
        
        # Agregar información del escaneo si está disponible
        scan_type = kwargs.get('scan_type')
        if scan_type:
            formatted += f"\n🔎 Tipo: {scan_type}"
        
        return formatted
    
    def _send_message_sync(self, text: str, chat_id: Optional[str] = None, 
                          parse_mode: str = 'HTML', disable_web_page_preview: bool = True) -> bool:
        """Enviar mensaje de forma síncrona"""
        
        # Usar chat_ids por defecto si no se especifica uno
        target_chats = [chat_id] if chat_id else self.chat_ids
        
        if not target_chats:
            self.logger.warning("No hay chat_ids configurados para Telegram")
            return False
        
        success = True
        
        for chat_id in target_chats:
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': disable_web_page_preview
                }
                
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        self.logger.debug(f"Mensaje enviado a {chat_id}")
                    else:
                        self.logger.error(f"Error enviando mensaje a {chat_id}: {data.get('description')}")
                        success = False
                else:
                    self.logger.error(f"Error HTTP enviando mensaje a {chat_id}: {response.status_code}")
                    success = False
                    
            except Exception as e:
                self.logger.error(f"Error enviando mensaje a {chat_id}: {e}")
                success = False
        
        return success
    
    def send_critical_finding(self, domain: str, path: str, status_code: int, 
                             full_url: str, **kwargs) -> bool:
        """Enviar notificación de hallazgo crítico"""
        title = f"🚨 Hallazgo Crítico Detectado"
        
        message = f"Se ha encontrado una ruta crítica en el dominio <b>{domain}</b>\n\n"
        message += f"📍 Ruta: <code>{path}</code>\n"
        message += f"📊 Código: <b>{status_code}</b>\n"
        message += f"🌐 URL: <code>{full_url}</code>"
        
        return self.send_notification(
            title, message, 'critical', full_url,
            domain=domain, **kwargs
        )
    
    def send_scan_started(self, domain: str, scan_type: str = 'full', **kwargs) -> bool:
        """Enviar notificación de inicio de escaneo"""
        title = f"🔍 Escaneo Iniciado"
        
        message = f"Se ha iniciado un escaneo en el dominio <b>{domain}</b>\n\n"
        message += f"🔎 Tipo de escaneo: <b>{scan_type}</b>"
        
        return self.send_notification(
            title, message, 'info',
            domain=domain, scan_type=scan_type, **kwargs
        )
    
    def send_scan_completed(self, domain: str, paths_found: int, critical_found: int, 
                           execution_time: float, **kwargs) -> bool:
        """Enviar notificación de escaneo completado"""
        title = f"✅ Escaneo Completado"
        
        message = f"El escaneo del dominio <b>{domain}</b> ha finalizado\n\n"
        message += f"📊 Rutas encontradas: <b>{paths_found}</b>\n"
        message += f"🚨 Hallazgos críticos: <b>{critical_found}</b>\n"
        message += f"⏱️ Tiempo de ejecución: <b>{execution_time:.2f}s</b>"
        
        severity = 'critical' if critical_found > 0 else 'success'
        
        return self.send_notification(
            title, message, severity,
            domain=domain, **kwargs
        )
    
    def send_scan_error(self, domain: str, error_message: str, **kwargs) -> bool:
        """Enviar notificación de error en escaneo"""
        title = f"❌ Error en Escaneo"
        
        message = f"Ha ocurrido un error durante el escaneo de <b>{domain}</b>\n\n"
        message += f"💥 Error: <code>{error_message}</code>"
        
        return self.send_notification(
            title, message, 'error',
            domain=domain, **kwargs
        )
    
    def send_alert(self, alert_type: str, severity: str, alert_title: str, 
                  alert_message: str, **kwargs) -> bool:
        """Enviar alerta personalizada"""
        title = f"📢 {alert_title}"
        
        message = f"<b>Tipo:</b> {alert_type}\n"
        message += f"<b>Severidad:</b> {severity}\n\n"
        message += alert_message
        
        return self.send_notification(
            title, message, severity, **kwargs
        )
    
    def send_system_status(self, status: Dict[str, Any]) -> bool:
        """Enviar estado del sistema"""
        title = f"📊 Estado del Sistema"
        
        message = f"<b>WebFuzzing Pro - Estado Actual</b>\n\n"
        message += f"🌐 Dominios activos: <b>{status.get('total_domains', 0)}</b>\n"
        message += f"🔍 Hallazgos recientes: <b>{status.get('recent_findings', 0)}</b>\n"
        message += f"🚨 Hallazgos críticos: <b>{status.get('critical_findings', 0)}</b>\n"
        message += f"⚠️ Alertas nuevas: <b>{status.get('new_alerts', 0)}</b>\n"
        message += f"⚡ Escaneos activos: <b>{status.get('active_scans', 0)}</b>"
        
        return self.send_notification(title, message, 'info')
    
    def test_connection(self, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """Probar conexión con Telegram"""
        if not self.is_available:
            return {
                'success': False,
                'error': 'Bot no disponible'
            }
        
        test_message = "🧪 <b>Test de conexión</b>\n\nSi recibes este mensaje, las notificaciones de WebFuzzing Pro están funcionando correctamente."
        
        success = self._send_message_sync(test_message, chat_id)
        
        return {
            'success': success,
            'message': 'Mensaje de prueba enviado' if success else 'Error enviando mensaje de prueba'
        }
    
    def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Obtener información de un chat"""
        try:
            response = requests.get(
                f"{self.api_url}/getChat",
                params={'chat_id': chat_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return {
                        'success': True,
                        'info': data.get('result', {})
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('description', 'Error desconocido')
                    }
            else:
                return {
                    'success': False,
                    'error': f'Error HTTP: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del bot"""
        status = {
            'name': 'Telegram Bot',
            'enabled': self.enabled,
            'available': self.is_available,
            'chat_ids_count': len(self.chat_ids),
            'queue_size': self.message_queue.qsize(),
            'is_running': self.is_running
        }
        
        if self.is_available:
            try:
                response = requests.get(f"{self.api_url}/getMe", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        status.update({
                            'bot_username': bot_info.get('username'),
                            'bot_name': bot_info.get('first_name'),
                            'bot_id': bot_info.get('id')
                        })
            except:
                pass
        
        return status
    
    def configure(self, bot_token: str = None, chat_ids: List[str] = None, 
                 enabled: bool = None) -> Dict[str, Any]:
        """Configurar bot dinámicamente"""
        changes = {}
        
        if bot_token is not None:
            self.bot_token = bot_token
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
            changes['bot_token'] = 'actualizado'
        
        if chat_ids is not None:
            self.chat_ids = chat_ids
            changes['chat_ids'] = f'{len(chat_ids)} configurados'
        
        if enabled is not None:
            self.enabled = enabled
            changes['enabled'] = enabled
        
        # Re-verificar disponibilidad si hay cambios importantes
        if bot_token is not None:
            self.is_available = self._verify_bot_token() if self.enabled else False
            changes['availability'] = self.is_available
        
        return {
            'success': True,
            'changes': changes,
            'status': self.get_status()
        }