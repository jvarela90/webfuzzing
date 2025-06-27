# utils/logger.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name: str = None, log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """Configurar logger del sistema"""
    
    # Crear directorio de logs
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Nombre del logger
    logger_name = name or 'webfuzzing'
    logger = logging.getLogger(logger_name)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Nivel de logging
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación
    log_file = log_file or f'logs/{logger_name}_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Obtener logger configurado"""
    return logging.getLogger(name or 'webfuzzing')