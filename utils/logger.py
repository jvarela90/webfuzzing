# utils/logger.py
"""
Sistema de logging para WebFuzzing Pro
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any
import json

class WebFuzzingFormatter(logging.Formatter):
    """Formateador personalizado para logs"""
    
    def __init__(self, include_colors: bool = False):
        """
        Inicializar formateador
        
        Args:
            include_colors: Incluir códigos de color ANSI
        """
        self.include_colors = include_colors
        
        # Formato base
        self.base_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Colores ANSI
        self.colors = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Verde
            'WARNING': '\033[33m',   # Amarillo
            'ERROR': '\033[31m',     # Rojo
            'CRITICAL': '\033[35m',  # Magenta
            'RESET': '\033[0m'       # Reset
        }
        
        super().__init__(self.base_format)
    
    def format(self, record):
        """Formatear registro de log"""
        # Formatear mensaje base
        formatted = super().format(record)
        
        # Agregar colores si está habilitado y es terminal
        if self.include_colors and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            level_color = self.colors.get(record.levelname, '')
            reset_color = self.colors['RESET']
            formatted = f"{level_color}{formatted}{reset_color}"
        
        return formatted

class JSONFormatter(logging.Formatter):
    """Formateador JSON para logs estructurados"""
    
    def format(self, record):
        """Formatear registro como JSON"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Agregar campos personalizados si existen
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Configurar sistema de logging
    
    Args:
        config: Configuración de logging
        
    Returns:
        Logger principal configurado
    """
    if config is None:
        config = {
            'level': 'INFO',
            'file': 'logs/webfuzzing.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5,
            'format': 'standard',
            'console': True,
            'json_format': False
        }
    
    # Obtener nivel de logging
    log_level = getattr(logging, config.get('level', 'INFO').upper())
    
    # Configurar logger principal
    logger = logging.getLogger('webfuzzing')
    logger.setLevel(log_level)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Crear directorio de logs si no existe
    log_file = config.get('file', 'logs/webfuzzing.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Handler para archivo con rotación
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.get('max_size', 10485760),
            backupCount=config.get('backup_count', 5),
            encoding='utf-8'
        )
        
        # Seleccionar formateador
        if config.get('json_format', False):
            file_formatter = JSONFormatter()
        else:
            file_formatter = WebFuzzingFormatter(include_colors=False)
        
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Error configurando handler de archivo: {e}")
    
    # Handler para consola si está habilitado
    if config.get('console', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = WebFuzzingFormatter(include_colors=True)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    
    # Handler separado para errores críticos
    try:
        error_file = log_file.replace('.log', '_errors.log')
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=config.get('max_size', 10485760),
            backupCount=config.get('backup_count', 5),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(WebFuzzingFormatter(include_colors=False))
        logger.addHandler(error_handler)
        
    except Exception as e:
        print(f"Error configurando handler de errores: {e}")
    
    # Configurar loggers de librerías externas
    _configure_external_loggers(log_level)
    
    logger.info("Sistema de logging configurado correctamente")
    return logger

def _configure_external_loggers(level: int) -> None:
    """Configurar loggers de librerías externas"""
    
    # Reducir verbosidad de requests
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Configurar otros loggers comunes
    external_loggers = [
        'werkzeug',
        'flask',
        'socketio',
        'engineio'
    ]
    
    for logger_name in external_loggers:
        ext_logger = logging.getLogger(logger_name)
        ext_logger.setLevel(max(level, logging.WARNING))

def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger hijo del sistema principal
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(f'webfuzzing.{name}')

class LogContext:
    """Context manager para agregar información extra a logs"""
    
    def __init__(self, logger: logging.Logger, **extra_fields):
        """
        Inicializar contexto de log
        
        Args:
            logger: Logger a usar
            **extra_fields: Campos adicionales
        """
        self.logger = logger
        self.extra_fields = extra_fields
        self.old_factory = None
    
    def __enter__(self):
        """Entrar al contexto"""
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_fields = self.extra_fields
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salir del contexto"""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)

def log_function_call(func):
    """Decorador para logging automático de llamadas a funciones"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log de entrada
        logger.debug(f"Llamando {func.__name__} con args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completado exitosamente")
            return result
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {e}")
            raise
    
    return wrapper

def log_performance(func):
    """Decorador para medir y logging rendimiento"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} ejecutado en {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} falló después de {execution_time:.3f}s: {e}")
            raise
    
    return wrapper

class ScanLogger:
    """Logger especializado para operaciones de escaneo"""
    
    def __init__(self, scan_id: str, domain: str):
        """
        Inicializar logger de escaneo
        
        Args:
            scan_id: ID del escaneo
            domain: Dominio objetivo
        """
        self.scan_id = scan_id
        self.domain = domain
        self.logger = get_logger('scan')
        self.start_time = datetime.now()
    
    def log_start(self, scan_type: str, **kwargs):
        """Log de inicio de escaneo"""
        self.logger.info(f"[{self.scan_id}] Iniciando escaneo {scan_type} en {self.domain}")
        
        with LogContext(self.logger, scan_id=self.scan_id, domain=self.domain):
            self.logger.info(f"Parámetros: {kwargs}")
    
    def log_finding(self, path: str, status_code: int, is_critical: bool = False):
        """Log de hallazgo"""
        level = logging.WARNING if is_critical else logging.INFO
        
        with LogContext(self.logger, scan_id=self.scan_id, domain=self.domain):
            self.logger.log(level, f"Hallazgo: {path} ({status_code}) - {'CRÍTICO' if is_critical else 'Normal'}")
    
    def log_completion(self, paths_found: int, critical_found: int):
        """Log de finalización de escaneo"""
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        with LogContext(self.logger, scan_id=self.scan_id, domain=self.domain):
            self.logger.info(f"Escaneo completado: {paths_found} rutas, {critical_found} críticas, {execution_time:.2f}s")
    
    def log_error(self, error: str):
        """Log de error en escaneo"""
        with LogContext(self.logger, scan_id=self.scan_id, domain=self.domain):
            self.logger.error(f"Error en escaneo: {error}")

# Configuración global por defecto
_default_config = {
    'level': 'INFO',
    'file': 'logs/webfuzzing.log',
    'max_size': 10485760,
    'backup_count': 5,
    'console': True,
    'json_format': False
}

# Inicializar logging por defecto si se importa el módulo
if not logging.getLogger('webfuzzing').handlers:
    setup_logging(_default_config)