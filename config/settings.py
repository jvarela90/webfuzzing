# config/settings.py
import os
import json
from pathlib import Path
from typing import Dict, List, Any

class Config:
    """Configuración centralizada del sistema"""
    
    def __init__(self, config_file: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = config_file or str(self.base_dir / "config.json")
        self._load_config()
        
    def _load_config(self):
        """Cargar configuración desde archivo JSON"""
        default_config = {
            # Configuración general
            "system": {
                "name": "WebFuzzing Pro",
                "version": "2.0.0",
                "timezone": "America/Argentina/Buenos_Aires",
                "log_level": "INFO"
            },
            
            # Configuración de fuzzing
            "fuzzing": {
                "max_workers": 10,
                "timeout": 5,
                "user_agent": "Mozilla/5.0 (WebFuzzer Pro 2.0)",
                "retry_count": 3,
                "delay_between_requests": 0.1,
                "status_codes_of_interest": [200, 201, 202, 301, 302, 403, 500],
                "critical_paths": [".git", "admin", "config.php", "backup", "panel", "test", "dev"],
                "max_path_length": 12,
                "alphabet": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "numbers": "0123456789",
                "special_chars": "_-"
            },
            
            # Configuración de base de datos
            "database": {
                "type": "sqlite",
                "name": "webfuzzing.db",
                "backup_interval": 86400,  # 24 horas
                "cleanup_after_days": 30
            },
            
            # Configuración de notificaciones
            "notifications": {
                "telegram": {
                    "enabled": False,
                    "bot_token": "",
                    "chat_id": "",
                    "critical_only": True
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                }
            },
            
            # Configuración de horarios
            "schedules": {
                "general_scan": "0 8,13,18,23 * * *",  # 08:00, 13:00, 18:00, 23:00
                "deep_scan": "0 2 * * 0",              # Domingos a las 2:00
                "report_times": ["09:00", "14:00"],
                "working_hours": {
                    "start": "08:00",
                    "end": "16:00"
                }
            },
            
            # Configuración de integración con herramientas
            "tools": {
                "ffuf": {
                    "enabled": True,
                    "path": "ffuf",
                    "default_options": ["-mc", "200,403", "-t", "50"]
                },
                "dirsearch": {
                    "enabled": True,
                    "path": "python3 -m dirsearch",
                    "default_options": ["-t", "10", "--plain-text-report"]
                }
            },
            
            # Configuración de archivos
            "files": {
                "domains_file": "data/dominios.csv",
                "dictionaries_dir": "data/diccionarios",
                "results_dir": "data/resultados",
                "discovered_paths": "data/descubiertos.txt",
                "backup_dir": "backups"
            },
            
            # Configuración web
            "web": {
                "host": "127.0.0.1",
                "port": 5000,
                "debug": True,
                "secret_key": "your-secret-key-change-this",
                "session_timeout": 3600
            },
            
            # Configuración API
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "api_key": "your-api-key-change-this",
                "rate_limit": "100/hour"
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        else:
            # Crear archivo de configuración por defecto
            self.save_config(default_config)
            
        self.config = default_config
        
        # Crear directorios necesarios
        self._create_directories()
        
    def _create_directories(self):
        """Crear directorios necesarios"""
        dirs_to_create = [
            self.get('files.results_dir'),
            self.get('files.dictionaries_dir'),
            self.get('files.backup_dir'),
            'logs',
            'data'
        ]
        
        for dir_path in dirs_to_create:
            Path(self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default=None):
        """Obtener valor de configuración usando notación de punto"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any):
        """Establecer valor de configuración usando notación de punto"""
        keys = key.split('.')
        config_ref = self.config
        
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
            
        config_ref[keys[-1]] = value
    
    def save_config(self, config_dict: Dict = None):
        """Guardar configuración en archivo"""
        config_to_save = config_dict or self.config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2, ensure_ascii=False)
    
    def get_domains_file(self) -> Path:
        """Obtener ruta del archivo de dominios"""
        return self.base_dir / self.get('files.domains_file')
    
    def get_results_dir(self) -> Path:
        """Obtener directorio de resultados"""
        return self.base_dir / self.get('files.results_dir')
    
    def get_dictionaries_dir(self) -> Path:
        """Obtener directorio de diccionarios"""
        return self.base_dir / self.get('files.dictionaries_dir')
