# config/database.py
"""
Configuración de base de datos para WebFuzzing Pro
ARREGLO: Importar Config correctamente
"""

import sqlite3
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Importar Config de settings
try:
    from config.settings import Config
except ImportError:
    # Fallback si no existe config.settings
    from typing import Dict as Config

class DatabaseManager:
    """Gestor de configuración de base de datos"""
    
    def __init__(self, config: Optional[Config] = None):
        """Inicializar gestor de base de datos"""
        self.logger = logging.getLogger(__name__)
        
        # Si config es un dict o None, manejarlo apropiadamente
        if isinstance(config, dict):
            self.config = config
        elif hasattr(config, 'get'):
            self.config = config
        else:
            # Configuración por defecto
            self.config = {
                'database': {
                    'path': 'webfuzzing.db',
                    'timeout': 30.0,
                    'check_same_thread': False
                }
            }
        
        # Obtener configuración de base de datos
        self.db_path = self._get_config_value('database.path', 'webfuzzing.db')
        self.timeout = self._get_config_value('database.timeout', 30.0)
        self.check_same_thread = self._get_config_value('database.check_same_thread', False)
        
        # Crear directorio si no existe
        self._ensure_db_directory()
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración de forma segura"""
        try:
            if hasattr(self.config, 'get') and callable(self.config.get):
                return self.config.get(key, default)
            elif isinstance(self.config, dict):
                # Navegar por claves anidadas (ej: 'database.path')
                keys = key.split('.')
                value = self.config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                return value
            else:
                return default
        except Exception as e:
            self.logger.warning(f"Error obteniendo configuración {key}: {e}")
            return default
    
    def _ensure_db_directory(self) -> None:
        """Asegurar que el directorio de la base de datos existe"""
        try:
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                self.logger.info(f"Directorio de BD creado: {db_dir}")
        except Exception as e:
            self.logger.error(f"Error creando directorio de BD: {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtener conexión a la base de datos"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=self.check_same_thread
            )
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys = ON')
            return conn
        except Exception as e:
            self.logger.error(f"Error conectando a la base de datos: {e}")
            raise
    
    def get_database_path(self) -> str:
        """Obtener ruta de la base de datos"""
        return self.db_path
    
    def database_exists(self) -> bool:
        """Verificar si la base de datos existe"""
        return os.path.exists(self.db_path)
    
    def get_database_size(self) -> int:
        """Obtener tamaño de la base de datos en bytes"""
        try:
            if self.database_exists():
                return os.path.getsize(self.db_path)
            return 0
        except Exception as e:
            self.logger.error(f"Error obteniendo tamaño de BD: {e}")
            return 0