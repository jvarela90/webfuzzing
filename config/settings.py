"""
Configuración del Security Fuzzing System
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

class Config:
    """Configuración centralizada del sistema"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.config_file = self.base_dir / config_file
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración desde archivo YAML"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                # Configuración por defecto si no existe el archivo
                return self._default_config()
        except Exception as e:
            print(f"⚠️ Error cargando config.yaml: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            'system': {
                'name': 'Security Fuzzing System',
                'version': '2.0.0',
                'environment': 'development',
                'debug': True,
                'log_level': 'INFO'
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/databases/fuzzing.db',
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'web': {
                'host': '0.0.0.0',
                'port': 5000,
                'secret_key': 'dev-secret-key-change-in-production'
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'enable_cors': True
            },
            'network': {
                'max_workers': 6,
                'timeout': 15,
                'verify_ssl': False
            },
            'tools': {
                'ffuf': {
                    'enabled': True,
                    'path': 'tools/ffuf/ffuf.exe'
                },
                'dirsearch': {
                    'enabled': True,
                    'path': 'tools/dirsearch/dirsearch.py'
                }
            }
        }
    
    def get(self, key: str, default=None):
        """Obtener valor de configuración usando notación punto"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value):
        """Establecer valor de configuración"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Guardar configuración actual al archivo"""
        try:
            # Crear directorio si no existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
            return False
    
    # Propiedades para acceso fácil a configuraciones comunes
    @property
    def DEBUG(self) -> bool:
        return self.get('system.debug', False)
    
    @property
    def LOG_LEVEL(self) -> str:
        return self.get('system.log_level', 'INFO')
    
    @property
    def DATABASE_PATH(self) -> str:
        db_path = self.get('database.path', 'data/databases/fuzzing.db')
        if not os.path.isabs(db_path):
            return str(self.base_dir / db_path)
        return db_path
    
    @property
    def WEB_HOST(self) -> str:
        return self.get('web.host', '0.0.0.0')
    
    @property
    def WEB_PORT(self) -> int:
        return self.get('web.port', 5000)
    
    @property
    def API_HOST(self) -> str:
        return self.get('api.host', '0.0.0.0')
    
    @property
    def API_PORT(self) -> int:
        return self.get('api.port', 8000)
    
    @property
    def SECRET_KEY(self) -> str:
        return self.get('web.secret_key', 'change-this-secret-key')
    
    @property
    def MAX_WORKERS(self) -> int:
        return self.get('network.max_workers', 6)
    
    @property
    def TIMEOUT(self) -> int:
        return self.get('network.timeout', 15)
    
    @property
    def VERIFY_SSL(self) -> bool:
        return self.get('network.verify_ssl', False)
    
    @property
    def FFUF_PATH(self) -> str:
        path = self.get('tools.ffuf.path', 'tools/ffuf/ffuf.exe')
        if not os.path.isabs(path):
            return str(self.base_dir / path)
        return path
    
    @property
    def DIRSEARCH_PATH(self) -> str:
        path = self.get('tools.dirsearch.path', 'tools/dirsearch/dirsearch.py')
        if not os.path.isabs(path):
            return str(self.base_dir / path)
        return path
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Verificar si una herramienta está habilitada"""
        return self.get(f'tools.{tool_name}.enabled', False)
    
    def get_wordlists(self) -> Dict[str, str]:
        """Obtener rutas de wordlists"""
        return self.get('wordlists', {})
    
    def get_notifications_config(self) -> Dict[str, Any]:
        """Obtener configuración de notificaciones"""
        return self.get('notifications', {})
    
    def __str__(self):
        return f"Config(file={self.config_file}, loaded={len(self._config)} keys)"
    
    def __repr__(self):
        return self.__str__()

# Instancia global de configuración
config = Config()

# Funciones de conveniencia
def get_config(key: str, default=None):
    """Función helper para obtener configuración"""
    return config.get(key, default)

def set_config(key: str, value):
    """Función helper para establecer configuración"""
    return config.set(key, value)

def save_config():
    """Función helper para guardar configuración"""
    return config.save()

if __name__ == "__main__":
    # Test de la configuración
    print("🧪 Testing Config Module...")
    print(f"Config file: {config.config_file}")
    print(f"Database path: {config.DATABASE_PATH}")
    print(f"Web server: {config.WEB_HOST}:{config.WEB_PORT}")
    print(f"API server: {config.API_HOST}:{config.API_PORT}")
    print(f"Debug mode: {config.DEBUG}")
    print(f"Max workers: {config.MAX_WORKERS}")
    print("✅ Config module working correctly!")