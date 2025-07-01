# integrations/__init__.py
"""
Módulo de integraciones para WebFuzzing Pro
Contiene integraciones con herramientas externas y servicios
"""

import logging
from typing import Dict, Any, Optional, List
from integrations.dirsearch_integration import DirsearchIntegration
from integrations.ffuf_integration import FFUFIntegration
from integrations.telegram_bot import TelegramBot

__version__ = "1.0.0"
__author__ = "WebFuzzing Pro Team"

# Logger para el módulo
logger = logging.getLogger(__name__)

class IntegrationManager:
    """Gestor central de todas las integraciones"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializar gestor de integraciones
        
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Inicializar integraciones
        self.integrations = {}
        self._initialize_integrations()
    
    def _initialize_integrations(self) -> None:
        """Inicializar todas las integraciones disponibles"""
        
        # Integración con Dirsearch
        try:
            self.integrations['dirsearch'] = DirsearchIntegration(self.config)
            self.logger.info("Integración Dirsearch inicializada")
        except Exception as e:
            self.logger.error(f"Error inicializando Dirsearch: {e}")
            self.integrations['dirsearch'] = None
        
        # Integración con FFUF
        try:
            self.integrations['ffuf'] = FFUFIntegration(self.config)
            self.logger.info("Integración FFUF inicializada")
        except Exception as e:
            self.logger.error(f"Error inicializando FFUF: {e}")
            self.integrations['ffuf'] = None
        
        # Bot de Telegram
        try:
            self.integrations['telegram'] = TelegramBot(self.config)
            if self.integrations['telegram'].enabled:
                self.integrations['telegram'].start()
            self.logger.info("Bot de Telegram inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando Telegram: {e}")
            self.integrations['telegram'] = None
    
    def get_integration(self, name: str) -> Optional[Any]:
        """
        Obtener integración por nombre
        
        Args:
            name: Nombre de la integración
            
        Returns:
            Instancia de la integración o None
        """
        return self.integrations.get(name)
    
    def get_available_integrations(self) -> List[str]:
        """
        Obtener lista de integraciones disponibles
        
        Returns:
            Lista de nombres de integraciones disponibles
        """
        available = []
        for name, integration in self.integrations.items():
            if integration and getattr(integration, 'is_available', False):
                available.append(name)
        return available
    
    def get_integration_status(self, name: str = None) -> Dict[str, Any]:
        """
        Obtener estado de integraciones
        
        Args:
            name: Nombre específico de integración (opcional)
            
        Returns:
            Dict con estado de integraciones
        """
        if name:
            integration = self.integrations.get(name)
            if integration and hasattr(integration, 'get_status'):
                return integration.get_status()
            else:
                return {'name': name, 'available': False, 'error': 'Integration not found'}
        
        # Obtener estado de todas las integraciones
        status = {}
        for name, integration in self.integrations.items():
            if integration and hasattr(integration, 'get_status'):
                status[name] = integration.get_status()
            else:
                status[name] = {'name': name, 'available': False}
        
        return status
    
    def test_integration(self, name: str) -> Dict[str, Any]:
        """
        Probar integración específica
        
        Args:
            name: Nombre de la integración
            
        Returns:
            Resultado del test
        """
        integration = self.integrations.get(name)
        if not integration:
            return {
                'success': False,
                'error': f'Integración {name} no encontrada'
            }
        
        try:
            if name == 'telegram':
                # Test específico para Telegram
                return integration.test_connection()
            elif name in ['dirsearch', 'ffuf']:
                # Test de disponibilidad para herramientas de fuzzing
                return {
                    'success': integration.is_available,
                    'message': f'{name} {"disponible" if integration.is_available else "no disponible"}'
                }
            else:
                return {
                    'success': True,
                    'message': f'Integración {name} operativa'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_notification(self, title: str, message: str, severity: str = 'info', **kwargs) -> Dict[str, Any]:
        """
        Enviar notificación a través de integraciones habilitadas
        
        Args:
            title: Título de la notificación
            message: Mensaje
            severity: Severidad (info, warning, critical)
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultado del envío
        """
        results = {}
        
        # Enviar por Telegram si está disponible
        telegram = self.integrations.get('telegram')
        if telegram and telegram.is_available:
            try:
                success = telegram.send_notification(title, message, severity, **kwargs)
                results['telegram'] = {
                    'success': success,
                    'message': 'Notificación enviada' if success else 'Error enviando notificación'
                }
            except Exception as e:
                results['telegram'] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Aquí se pueden agregar otras integraciones de notificación (email, webhook, etc.)
        
        return results
    
    def run_scan(self, url: str, scan_type: str = 'directory', tool: str = 'auto', **kwargs) -> Dict[str, Any]:
        """
        Ejecutar escaneo usando la integración apropiada
        
        Args:
            url: URL objetivo
            scan_type: Tipo de escaneo (directory, file, subdomain, etc.)
            tool: Herramienta a usar (auto, dirsearch, ffuf)
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultados del escaneo
        """
        # Selección automática de herramienta
        if tool == 'auto':
            # Preferir FFUF si está disponible, sino Dirsearch
            if self.integrations.get('ffuf') and self.integrations['ffuf'].is_available:
                tool = 'ffuf'
            elif self.integrations.get('dirsearch') and self.integrations['dirsearch'].is_available:
                tool = 'dirsearch'
            else:
                return {
                    'success': False,
                    'error': 'No hay herramientas de fuzzing disponibles'
                }
        
        # Ejecutar escaneo según la herramienta
        try:
            if tool == 'ffuf':
                ffuf = self.integrations.get('ffuf')
                if not ffuf or not ffuf.is_available:
                    return {'success': False, 'error': 'FFUF no disponible'}
                
                if scan_type == 'directory':
                    return ffuf.fuzz_directories(url, **kwargs)
                elif scan_type == 'file':
                    return ffuf.fuzz_files(url, **kwargs)
                elif scan_type == 'subdomain':
                    # Extraer dominio de la URL
                    domain = url.replace('http://', '').replace('https://', '').split('/')[0]
                    return ffuf.fuzz_subdomains(domain, **kwargs)
                else:
                    return {'success': False, 'error': f'Tipo de escaneo {scan_type} no soportado por FFUF'}
            
            elif tool == 'dirsearch':
                dirsearch = self.integrations.get('dirsearch')
                if not dirsearch or not dirsearch.is_available:
                    return {'success': False, 'error': 'Dirsearch no disponible'}
                
                if scan_type in ['directory', 'file']:
                    return dirsearch.scan_directory(url, **kwargs)
                else:
                    return {'success': False, 'error': f'Tipo de escaneo {scan_type} no soportado por Dirsearch'}
            
            else:
                return {'success': False, 'error': f'Herramienta {tool} no reconocida'}
                
        except Exception as e:
            self.logger.error(f"Error ejecutando escaneo con {tool}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def shutdown(self) -> None:
        """Apagar todas las integraciones"""
        try:
            # Detener bot de Telegram
            telegram = self.integrations.get('telegram')
            if telegram and hasattr(telegram, 'stop'):
                telegram.stop()
            
            self.logger.info("Integraciones cerradas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error cerrando integraciones: {e}")

# Funciones de conveniencia para acceso rápido
def get_integration_manager(config: Dict[str, Any]) -> IntegrationManager:
    """Crear gestor de integraciones"""
    return IntegrationManager(config)

def test_all_integrations(config: Dict[str, Any]) -> Dict[str, Any]:
    """Probar todas las integraciones"""
    manager = IntegrationManager(config)
    results = {}
    
    for name in manager.integrations.keys():
        results[name] = manager.test_integration(name)
    
    return results

# Exportar clases principales
__all__ = [
    'IntegrationManager',
    'DirsearchIntegration', 
    'FFUFIntegration',
    'TelegramBot',
    'get_integration_manager',
    'test_all_integrations'
]