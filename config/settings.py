import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base del proyecto"""
    
    # Directorios
    BASE_DIR = Path(__file__).parent.parent
    STATIC_DIR = BASE_DIR / "web" / "static"
    TEMPLATES_DIR = BASE_DIR / "web" / "templates"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///urlcontrol.db")
    
    # Configuración de Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-aqui")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configuración del Fuzzer
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "50"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
    USER_AGENT = os.getenv("USER_AGENT", "URLControl-Fuzzer/1.0")
    
    # Configuración de alertas
    ENABLE_ALERTS = os.getenv("ENABLE_ALERTS", "True").lower() == "true"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    # Configuración de logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "{time} | {level} | {message}"
    
    # Configuración de la API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "5000"))
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "5001"))

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    MAX_CONCURRENT_REQUESTS = 100

# Seleccionar configuración según el entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}