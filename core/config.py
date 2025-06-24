#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Configuración Unificado
Gestiona toda la configuración del sistema desde un punto central
"""

import os
import yaml
import platform
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    path: str = "data/databases/fuzzing.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_connections: int = 10


@dataclass
class NetworkConfig:
    """Configuración de red"""
    timeout: int = 15
    max_workers: int = 6
    max_redirects: int = 3
    user_agent: str = "SecurityScanner/2.0"
    verify_ssl: bool = False
    rate_limit_delay: float = 0.1


@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    jwt_secret_key: str = ""
    session_timeout_hours: int = 8
    max_login_attempts: int = 5
    password_min_length: int = 12
    require_2fa_admin: bool = True


@dataclass
class AlertConfig:
    """Configuración de alertas"""
    critical_paths: list = field(default_factory=lambda: [
        '.git', 'admin', 'config.php', 'backup', 'panel',
        'phpmyadmin', 'wp-admin', 'test', 'dev', 'old',
        'tmp', 'logs', 'private', 'secret', 'password',
        'database', 'db', 'mysql', 'oracle', 'sql'
    ])
    ml_enabled: bool = True
    auto_response: bool = False


@dataclass
class NotificationConfig:
    """Configuración de notificaciones"""
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_ids: list = field(default_factory=list)
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: list = field(default_factory=list)


@dataclass
class AutomationConfig:
    """Configuración de automatización"""
    enabled: bool = True
    scan_hours: list = field(default_factory=lambda: [9, 14, 18, 22])
    report_hours: list = field(default_factory=lambda: [10, 15])
    continuous_scan: bool = True
    intelligent_scheduling: bool = True


@dataclass
class ToolsConfig:
    """Configuración de herramientas externas"""
    ffuf_enabled: bool = True
    ffuf_path: str = "tools/ffuf/ffuf"
    dirsearch_enabled: bool = True
    dirsearch_path: str = "tools/dirsearch/dirsearch.py"
    nuclei_enabled: bool = False
    nuclei_path: str = "tools/nuclei/nuclei"


class ConfigManager:
    """Gestor centralizado de configuración"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = config_file or (self.base_dir / "config.yaml")
        self.platform = platform.system().lower()
        self.logger = logging.getLogger(__name__)
        
        # Configuraciones por sección
        self.database = DatabaseConfig()
        self.network = NetworkConfig()
        self.security = SecurityConfig()
        self.alerts = AlertConfig()
        self.notifications = NotificationConfig()
        self.automation = AutomationConfig()
        self.tools = ToolsConfig()
        
        # Cargar configuración
        self.load_config()
        self.apply_platform_optimizations()
    
    def load_config(self):
        """Cargar configuración desde archivo YAML"""
        if not self.config_file.exists():
            self.create_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Aplicar configuraciones
            self._apply_config_section('database', config_data.get('database', {}))
            self._apply_config_section('network', config_data.get('network', {}))
            self._apply_config_section('security', config_data.get('security', {}))
            self._apply_config_section('alerts', config_data.get('alerts', {}))
            self._apply_config_section('notifications', config_data.get('notifications', {}))
            self._apply_config_section('automation', config_data.get('automation', {}))
            self._apply_config_section('tools', config_data.get('tools', {}))
            
            self.logger.info(f"Configuración cargada desde {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self.logger.info("Usando configuración por defecto")
    
    def _apply_config_section(self, section_name: str, section_data: Dict[str, Any]):
        """Aplicar configuración a una sección específica"""
        section_obj = getattr(self, section_name)
        
        for key, value in section_data.items():
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
    
    def apply_platform_optimizations(self):
        """Aplicar optimizaciones específicas de plataforma"""
        if self.platform == "windows":
            self.network.max_workers = max(4, self.network.max_workers // 2)
            self.network.timeout = max(self.network.timeout, 20)
            
            # Rutas de herramientas para Windows
            if self.tools.ffuf_enabled:
                self.tools.ffuf_path = "tools/ffuf/ffuf.exe"
        
        elif self.platform == "linux":
            # Optimizaciones para Linux
            self.network.max_workers = min(self.network.max_workers * 2, 20)
        
        elif self.platform == "darwin":  # macOS
            self.network.max_workers = min(self.network.max_workers, 10)
    
    def create_default_config(self):
        """Crear archivo de configuración por defecto"""
        default_config = {
            'database': {
                'path': 'data/databases/fuzzing.db',
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'network': {
                'timeout': 15,
                'max_workers': 6,
                'max_redirects': 3,
                'verify_ssl': False,
                'rate_limit_delay': 0.1
            },
            'security': {
                'jwt_secret_key': 'CHANGE_THIS_SECRET_KEY',
                'session_timeout_hours': 8,
                'max_login_attempts': 5,
                'password_min_length': 12,
                'require_2fa_admin': True
            },
            'alerts': {
                'critical_paths': [
                    '.git', 'admin', 'config.php', 'backup', 'panel',
                    'phpmyadmin', 'wp-admin', 'test', 'dev', 'old'
                ],
                'ml_enabled': True,
                'auto_response': False
            },
            'notifications': {
                'telegram_enabled': False,
                'telegram_bot_token': 'YOUR_BOT_TOKEN_HERE',
                'telegram_chat_ids': ['YOUR_CHAT_ID_HERE'],
                'email_enabled': False,
                'email_smtp_server': 'smtp.gmail.com',
                'email_smtp_port': 587,
                'email_recipients': ['security@company.com']
            },
            'automation': {
                'enabled': True,
                'scan_hours': [9, 14, 18, 22],
                'report_hours': [10, 15],
                'continuous_scan': True,
                'intelligent_scheduling': True
            },
            'tools': {
                'ffuf_enabled': True,
                'ffuf_path': 'tools/ffuf/ffuf',
                'dirsearch_enabled': True,
                'dirsearch_path': 'tools/dirsearch/dirsearch.py',
                'nuclei_enabled': False,
                'nuclei_path': 'tools/nuclei/nuclei'
            }
        }
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuración por defecto creada en {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error creando configuración por defecto: {e}")
    
    def save_config(self):
        """Guardar configuración actual al archivo"""
        config_data = {
            'database': self._dataclass_to_dict(self.database),
            'network': self._dataclass_to_dict(self.network),
            'security': self._dataclass_to_dict(self.security),
            'alerts': self._dataclass_to_dict(self.alerts),
            'notifications': self._dataclass_to_dict(self.notifications),
            'automation': self._dataclass_to_dict(self.automation),
            'tools': self._dataclass_to_dict(self.tools)
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuración guardada en {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convertir dataclass a diccionario"""
        if hasattr(obj, '__dataclass_fields__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return obj.__dict__
    
    def get_db_path(self) -> Path:
        """Obtener ruta absoluta de la base de datos"""
        db_path = Path(self.database.path)
        if not db_path.is_absolute():
            db_path = self.base_dir / db_path
        return db_path
    
    def get_logs_dir(self) -> Path:
        """Obtener directorio de logs"""
        return self.base_dir / "logs"
    
    def get_reports_dir(self) -> Path:
        """Obtener directorio de reportes"""
        return self.base_dir / "reports"
    
    def get_wordlists_dir(self) -> Path:
        """Obtener directorio de wordlists"""
        return self.base_dir / "data" / "wordlists"
    
    def get_tools_dir(self) -> Path:
        """Obtener directorio de herramientas"""
        return self.base_dir / "tools"
    
    def is_development_mode(self) -> bool:
        """Verificar si está en modo desarrollo"""
        return os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG') == 'True'
    
    def get_network_headers(self) -> Dict[str, str]:
        """Obtener headers HTTP por defecto"""
        if self.platform == "windows":
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        elif self.platform == "darwin":
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        else:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
    
    def validate_config(self) -> bool:
        """Validar configuración actual"""
        errors = []
        
        # Validar rutas críticas
        if not self.database.path:
            errors.append("Database path not configured")
        
        if self.notifications.telegram_enabled and not self.notifications.telegram_bot_token:
            errors.append("Telegram enabled but no bot token configured")
        
        if self.notifications.email_enabled and not self.notifications.email_username:
            errors.append("Email enabled but no username configured")
        
        if self.security.jwt_secret_key == "CHANGE_THIS_SECRET_KEY":
            errors.append("JWT secret key not changed from default")
        
        if errors:
            for error in errors:
                self.logger.error(f"Config validation error: {error}")
            return False
        
        return True


# Instancia global de configuración
config = ConfigManager()


def get_config() -> ConfigManager:
    """Obtener instancia global de configuración"""
    return config


def reload_config():
    """Recargar configuración desde archivo"""
    global config
    config.load_config()
    config.apply_platform_optimizations()