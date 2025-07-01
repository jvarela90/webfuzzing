# config/settings.py
"""
Configuración principal del sistema WebFuzzing Pro
"""

import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import yaml

class Config:
    """Gestor de configuración del sistema"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializar configuración
        
        Args:
            config_file: Archivo de configuración (JSON o YAML)
        """
        self.logger = logging.getLogger(__name__)
        
        # Archivos de configuración por defecto
        self.config_files = [
            config_file,
            'config.json',
            'config.yaml',
            'config.yml',
            'settings.json',
            'settings.yaml'
        ]
        
        # Configuración por defecto
        self.default_config = {
            'api': {
                'api_key': 'demo-key-change-this',
                'host': '127.0.0.1',
                'port': 8000,
                'debug': False
            },
            'web': {
                'host': '127.0.0.1',
                'port': 5000,
                'debug': False,
                'secret_key': 'change-this-secret-key'
            },
            'database': {
                'path': 'webfuzzing.db',
                'timeout': 30.0,
                'check_same_thread': False,
                'backup_interval': 3600  # 1 hora
            },
            'scan': {
                'default_wordlist': 'data/wordlists/common.txt',
                'max_concurrent': 10,
                'timeout': 30,
                'user_agent': 'WebFuzzing-Pro/1.0',
                'threads': 10,
                'delay': 0,
                'rate_limit': 0
            },
            'fuzzing': {
                'max_depth': 3,
                'follow_redirects': True,
                'verify_ssl': True,
                'custom_headers': {},
                'proxy': None
            },
            'notifications': {
                'telegram': {
                    'enabled': False,
                    'bot_token': '',
                    'chat_ids': []
                },
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_email': '',
                    'to_emails': []
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'secret': ''
                }
            },
            'integrations': {
                'dirsearch': {
                    'path': 'dirsearch',
                    'wordlist': 'data/wordlists/common.txt',
                    'extensions': ['php', 'html', 'js', 'txt', 'asp', 'aspx'],
                    'threads': 30,
                    'timeout': 30
                },
                'ffuf': {
                    'path': 'ffuf',
                    'wordlist': 'data/wordlists/common.txt',
                    'threads': 40,
                    'timeout': 10,
                    'delay': 0,
                    'rate': 0
                }
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/webfuzzing.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'security': {
                'max_login_attempts': 5,
                'session_timeout': 3600,
                'require_https': False,
                'allowed_hosts': ['localhost', '127.0.0.1']
            },
            'system': {
                'debug': False,
                'version': '1.0.0',
                'environment': 'production',
                'max_workers': 4,
                'cleanup_interval': 86400  # 24 horas
            }
        }
        
        # Cargar configuración
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración desde archivo"""
        config = self.default_config.copy()
        
        # Intentar cargar desde archivos de configuración
        for config_file in self.config_files:
            if config_file and os.path.exists(config_file):
                try:
                    loaded_config = self._load_config_file(config_file)
                    if loaded_config:
                        config = self._merge_configs(config, loaded_config)
                        self.logger.info(f"Configuración cargada desde: {config_file}")
                        break
                except Exception as e:
                    self.logger.warning(f"Error cargando configuración desde {config_file}: {e}")
                    continue
        
        # Cargar variables de entorno
        config = self._load_env_overrides(config)
        
        return config
    
    def _load_config_file(self, config_file: str) -> Optional[Dict[str, Any]]:
        """Cargar archivo de configuración"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.endswith(('.yaml', '.yml')):
                    try:
                        import yaml
                        return yaml.safe_load(f)
                    except ImportError:
                        self.logger.error("PyYAML no está instalado, no se puede cargar archivo YAML")
                        return None
                else:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error leyendo archivo de configuración {config_file}: {e}")
            return None
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionar configuraciones recursivamente"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Cargar overrides desde variables de entorno"""
        env_mappings = {
            'WEBFUZZING_API_KEY': ('api', 'api_key'),
            'WEBFUZZING_API_HOST': ('api', 'host'),
            'WEBFUZZING_API_PORT': ('api', 'port'),
            'WEBFUZZING_WEB_HOST': ('web', 'host'),
            'WEBFUZZING_WEB_PORT': ('web', 'port'),
            'WEBFUZZING_DB_PATH': ('database', 'path'),
            'WEBFUZZING_DEBUG': ('system', 'debug'),
            'WEBFUZZING_LOG_LEVEL': ('logging', 'level'),
            'WEBFUZZING_TELEGRAM_TOKEN': ('notifications', 'telegram', 'bot_token'),
            'WEBFUZZING_TELEGRAM_CHAT_IDS': ('notifications', 'telegram', 'chat_ids'),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                try:
                    # Navegar al nivel correcto de la configuración
                    current = config
                    for key in config_path[:-1]:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                    
                    # Convertir tipos apropiados
                    final_key = config_path[-1]
                    if env_var.endswith('_PORT'):
                        current[final_key] = int(env_value)
                    elif env_var.endswith('_DEBUG'):
                        current[final_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif env_var.endswith('_CHAT_IDS'):
                        current[final_key] = env_value.split(',')
                    else:
                        current[final_key] = env_value
                        
                    self.logger.info(f"Override de configuración desde {env_var}")
                    
                except Exception as e:
                    self.logger.warning(f"Error procesando variable de entorno {env_var}: {e}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración
        
        Args:
            key: Clave de configuración (puede usar notación punto: 'api.port')
            default: Valor por defecto
            
        Returns:
            Valor de configuración o default
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Error obteniendo configuración {key}: {e}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Establecer valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        try:
            keys = key.split('.')
            current = self.config
            
            # Navegar hasta el penúltimo nivel
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Establecer el valor final
            current[keys[-1]] = value
            
        except Exception as e:
            self.logger.error(f"Error estableciendo configuración {key}: {e}")
    
    def save(self, config_file: str = None) -> bool:
        """
        Guardar configuración actual en archivo
        
        Args:
            config_file: Archivo donde guardar (por defecto config.json)
            
        Returns:
            bool: True si se guardó exitosamente
        """
        if not config_file:
            config_file = 'config.json'
        
        try:
            # Crear directorio si no existe
            config_dir = os.path.dirname(os.path.abspath(config_file))
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Guardar configuración
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_file.endswith(('.yaml', '.yml')):
                    try:
                        import yaml
                        yaml.safe_dump(self.config, f, default_flow_style=False, indent=2)
                    except ImportError:
                        self.logger.error("PyYAML no está instalado, guardando como JSON")
                        config_file = config_file.replace('.yaml', '.json').replace('.yml', '.json')
                        with open(config_file, 'w', encoding='utf-8') as json_f:
                            json.dump(self.config, json_f, indent=2)
                else:
                    json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuración guardada en: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
            return False
    
    def reload(self) -> bool:
        """
        Recargar configuración desde archivos
        
        Returns:
            bool: True si se recargó exitosamente
        """
        try:
            self.config = self._load_config()
            self.logger.info("Configuración recargada")
            return True
        except Exception as e:
            self.logger.error(f"Error recargando configuración: {e}")
            return False
    
    def validate(self) -> Dict[str, Any]:
        """
        Validar configuración actual
        
        Returns:
            Dict con resultados de validación
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validar configuración de API
            api_key = self.get('api.api_key')
            if not api_key or api_key == 'demo-key-change-this':
                results['warnings'].append('API key por defecto detectada, cambiar por seguridad')
            
            # Validar configuración de base de datos
            db_path = self.get('database.path')
            if not db_path:
                results['errors'].append('Ruta de base de datos no especificada')
                results['valid'] = False
            
            # Validar puertos
            api_port = self.get('api.port')
            web_port = self.get('web.port')
            
            if not isinstance(api_port, int) or not (1 <= api_port <= 65535):
                results['errors'].append('Puerto de API inválido')
                results['valid'] = False
            
            if not isinstance(web_port, int) or not (1 <= web_port <= 65535):
                results['errors'].append('Puerto web inválido')
                results['valid'] = False
            
            if api_port == web_port:
                results['errors'].append('Puerto de API y web no pueden ser iguales')
                results['valid'] = False
            
            # Validar configuración de Telegram si está habilitada
            if self.get('notifications.telegram.enabled'):
                telegram_token = self.get('notifications.telegram.bot_token')
                telegram_chats = self.get('notifications.telegram.chat_ids')
                
                if not telegram_token:
                    results['errors'].append('Token de Telegram requerido cuando está habilitado')
                    results['valid'] = False
                
                if not telegram_chats:
                    results['warnings'].append('No hay chat IDs configurados para Telegram')
            
            # Validar wordlists
            default_wordlist = self.get('scan.default_wordlist')
            if default_wordlist and not os.path.exists(default_wordlist):
                results['warnings'].append(f'Wordlist por defecto no encontrada: {default_wordlist}')
            
        except Exception as e:
            results['errors'].append(f'Error durante validación: {e}')
            results['valid'] = False
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de configuración"""
        return {
            'api_port': self.get('api.port'),
            'web_port': self.get('web.port'),
            'database_path': self.get('database.path'),
            'debug_mode': self.get('system.debug'),
            'telegram_enabled': self.get('notifications.telegram.enabled'),
            'email_enabled': self.get('notifications.email.enabled'),
            'default_wordlist': self.get('scan.default_wordlist'),
            'log_level': self.get('logging.level'),
            'version': self.get('system.version')
        }
    
    def export_template(self, output_file: str = 'config_template.json') -> bool:
        """
        Exportar plantilla de configuración
        
        Args:
            output_file: Archivo de salida
            
        Returns:
            bool: True si se exportó exitosamente
        """
        try:
            template = self.default_config.copy()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2)
            
            self.logger.info(f"Plantilla de configuración exportada: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando plantilla: {e}")
            return False

# Instancia global de configuración
_config_instance = None

def get_config(config_file: Optional[str] = None) -> Config:
    """Obtener instancia global de configuración"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_file)
    
    return _config_instance

def reload_config() -> bool:
    """Recargar configuración global"""
    global _config_instance
    
    if _config_instance:
        return _config_instance.reload()
    else:
        _config_instance = Config()
        return True