#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Fuzzing Web Consolidado
Motor principal de fuzzing con compatibilidad multiplataforma

Funcionalidades:
- Fuzzing de rutas web por fuerza bruta
- Detección automatizada de vulnerabilidades
- Sistema de alertas críticas en tiempo real
- Base de datos SQLite robusta
- Compatibilidad Windows/Linux/macOS
- Generación automática de diccionarios
- Reportes detallados en JSON
- Sistema de cache inteligente
"""

import os
import sys
import csv
import json
import sqlite3
import requests
import time
import logging
import threading
import subprocess
import itertools
import string
import platform
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from pathlib import Path

# Configurar encoding para Windows
if platform.system() == "Windows":
    import locale
    try:
        # Forzar UTF-8 en Windows
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class FuzzingConfig:
    """Configuración consolidada del sistema de fuzzing"""
    
    def __init__(self):
        # Detectar sistema operativo
        self.is_windows = platform.system() == "Windows"
        self.system_info = {
            'os': platform.system(),
            'release': platform.release(),
            'python_version': platform.python_version()
        }
        
        # Configurar rutas base
        self.BASE_DIR = Path(__file__).parent.resolve()
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.RESULTS_DIR = self.BASE_DIR / "results"
        self.TOOLS_DIR = self.BASE_DIR / "tools"
        self.TEMPLATES_DIR = self.BASE_DIR / "templates"
        
        # Archivos de configuración
        self.DOMINIOS_FILE = self.DATA_DIR / "dominios.csv"
        self.DICCIONARIO_FILE = self.DATA_DIR / "diccionario.txt"
        self.DESCUBIERTOS_FILE = self.DATA_DIR / "descubiertos.txt"
        self.CONFIG_FILE = self.DATA_DIR / "config.json"
        self.DATABASE_FILE = self.DATA_DIR / "fuzzing.db"
        
        # Configuración de red optimizada por OS
        self.HEADERS = {
            "User-Agent": f"Mozilla/5.0 ({self.system_info['os']} {self.system_info['release']}) FuzzingBot/2.0"
        }
        
        # Parámetros ajustados por sistema operativo
        if self.is_windows:
            self.TIMEOUT = 15
            self.MAX_WORKERS = 6  # Conservador para Windows
            self.CHUNK_SIZE = 100
        else:
            self.TIMEOUT = 10
            self.MAX_WORKERS = 12
            self.CHUNK_SIZE = 200
        
        self.MAX_REDIRECTS = 3
        self.REQUEST_DELAY = 0.1  # Delay entre requests
        
        # Rutas críticas expandidas para alertas
        self.CRITICAL_PATHS = [
            # Configuración y admin
            '.git', '.env', 'admin', 'administrator', 'config.php', 'configuration.php',
            'config', 'settings', 'setup', 'install', 'installer',
            
            # Backups y archivos sensibles
            'backup', 'backups', 'dump', 'old', 'tmp', 'temp', 'test',
            'logs', 'log', 'private', 'secret', 'password', 'passwd',
            
            # Bases de datos
            'database', 'db', 'mysql', 'postgresql', 'oracle', 'sql',
            'phpmyadmin', 'adminer', 'sqlitemanager',
            
            # Paneles y CMS
            'panel', 'cpanel', 'wp-admin', 'wp-login', 'wp-config',
            'drupal', 'joomla', 'magento', 'prestashop',
            
            # Desarrollo y testing
            'dev', 'development', 'staging', 'beta', 'alpha',
            'phpinfo', 'info.php', 'test.php', 'debug',
            
            # APIs y servicios
            'api', 'rest', 'graphql', 'soap', 'wsdl', 'swagger',
            'status', 'health', 'metrics', 'monitoring'
        ]
        
        # Extensiones de archivos críticos
        self.CRITICAL_EXTENSIONS = [
            '.git', '.env', '.config', '.conf', '.ini', '.xml',
            '.json', '.yml', '.yaml', '.sql', '.db', '.sqlite',
            '.bak', '.backup', '.old', '.tmp', '.log'
        ]
        
        # Códigos HTTP de interés
        self.INTERESTING_CODES = [200, 201, 204, 301, 302, 307, 308, 401, 403, 405, 500, 502, 503]
        
        # Configuración de horarios
        self.SCAN_HOURS = [8, 13, 18, 23] if not self.is_windows else [9, 14, 18, 22]
        self.REPORT_HOURS = [9, 15] if not self.is_windows else [10, 16]
        
        # Configuración de cache
        self.CACHE_DURATION = 3600  # 1 hora
        self.CACHE_ENABLED = True
        
        self.create_directories()
        self.setup_logging()
        self.load_custom_config()
    
    def create_directories(self):
        """Crear directorios necesarios"""
        directories = [
            self.DATA_DIR, self.LOGS_DIR, self.RESULTS_DIR, 
            self.TOOLS_DIR, self.TEMPLATES_DIR
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error creando directorio {directory}: {e}")
    
    def setup_logging(self):
        """Configurar sistema de logging robusto"""
        try:
            log_file = self.LOGS_DIR / f"fuzzing_{datetime.now().strftime('%Y%m%d')}.log"
            
            # Configurar formato de logging
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
            # Configurar handlers
            handlers = [logging.StreamHandler(sys.stdout)]
            
            # Handler de archivo con encoding UTF-8
            if self.is_windows:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
            else:
                file_handler = logging.FileHandler(log_file)
            
            handlers.append(file_handler)
            
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                handlers=handlers
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Sistema iniciado en {self.system_info['os']}")
            
        except Exception as e:
            print(f"Error configurando logging: {e}")
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
    
    def load_custom_config(self):
        """Cargar configuración personalizada desde archivo JSON"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                    # Aplicar configuración personalizada
                    for key, value in config_data.items():
                        if hasattr(self, key.upper()):
                            setattr(self, key.upper(), value)
                            self.logger.info(f"Configuración personalizada aplicada: {key} = {value}")
                            
            except Exception as e:
                self.logger.error(f"Error cargando configuración personalizada: {e}")

class ConsolidatedDatabaseManager:
    """Gestor de base de datos SQLite consolidado"""
    
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos con esquema completo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Habilitar foreign keys
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("PRAGMA journal_mode = WAL")  # Mejor concurrencia
                
                # Tabla de dominios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dominios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dominio TEXT UNIQUE NOT NULL,
                        protocolo TEXT NOT NULL DEFAULT 'https',
                        puerto INTEGER DEFAULT 443,
                        activo BOOLEAN DEFAULT 1,
                        fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ultimo_escaneo DATETIME,
                        total_hallazgos INTEGER DEFAULT 0,
                        hallazgos_criticos INTEGER DEFAULT 0
                    )
                ''')
                
                # Tabla de hallazgos mejorada
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS hallazgos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dominio_id INTEGER,
                        url_completa TEXT NOT NULL,
                        ruta TEXT NOT NULL,
                        codigo_http INTEGER NOT NULL,
                        es_critico BOOLEAN DEFAULT 0,
                        fecha_descubierto DATETIME DEFAULT CURRENT_TIMESTAMP,
                        contenido_hash TEXT,
                        tamano_respuesta INTEGER DEFAULT 0,
                        tiempo_respuesta REAL DEFAULT 0.0,
                        herramienta TEXT DEFAULT 'fuzzing_engine',
                        headers_respuesta TEXT,
                        verificado BOOLEAN DEFAULT 0,
                        notas TEXT,
                        FOREIGN KEY (dominio_id) REFERENCES dominios (id)
                    )
                ''')
                
                # Tabla de alertas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alertas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hallazgo_id INTEGER,
                        tipo_alerta TEXT NOT NULL DEFAULT 'informativa',
                        nivel_severidad INTEGER DEFAULT 1,
                        mensaje TEXT NOT NULL,
                        estado TEXT DEFAULT 'pendiente',
                        analista TEXT,
                        comentarios TEXT,
                        fecha_creada DATETIME DEFAULT CURRENT_TIMESTAMP,
                        fecha_atendida DATETIME,
                        fecha_vencimiento DATETIME,
                        automatica BOOLEAN DEFAULT 1,
                        FOREIGN KEY (hallazgo_id) REFERENCES hallazgos (id)
                    )
                ''')
                
                # Tabla de subdominios descubiertos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS subdominios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dominio_padre TEXT NOT NULL,
                        subdominio TEXT NOT NULL,
                        activo BOOLEAN DEFAULT 1,
                        fecha_descubierto DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metodo_descubrimiento TEXT DEFAULT 'bruteforce',
                        codigo_respuesta INTEGER,
                        UNIQUE(dominio_padre, subdominio)
                    )
                ''')
                
                # Tabla de sesiones de escaneo
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sesiones_escaneo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                        fecha_fin DATETIME,
                        dominios_escaneados INTEGER DEFAULT 0,
                        rutas_probadas INTEGER DEFAULT 0,
                        hallazgos_encontrados INTEGER DEFAULT 0,
                        hallazgos_criticos INTEGER DEFAULT 0,
                        estado TEXT DEFAULT 'iniciado',
                        configuracion_usada TEXT,
                        notas TEXT
                    )
                ''')
                
                # Tabla de estadísticas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS estadisticas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha DATE DEFAULT (date('now')),
                        total_dominios INTEGER DEFAULT 0,
                        total_hallazgos INTEGER DEFAULT 0,
                        hallazgos_criticos INTEGER DEFAULT 0,
                        alertas_pendientes INTEGER DEFAULT 0,
                        tiempo_respuesta_promedio REAL DEFAULT 0.0,
                        UNIQUE(fecha)
                    )
                ''')
                
                # Crear índices para optimizar consultas
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_hallazgos_dominio ON hallazgos(dominio_id)",
                    "CREATE INDEX IF NOT EXISTS idx_hallazgos_critico ON hallazgos(es_critico)",
                    "CREATE INDEX IF NOT EXISTS idx_hallazgos_fecha ON hallazgos(fecha_descubierto)",
                    "CREATE INDEX IF NOT EXISTS idx_alertas_estado ON alertas(estado)",
                    "CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha_creada)",
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                self.logger.info("✅ Base de datos inicializada correctamente")
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def save_scan_session(self, session_data):
        """Guardar información de sesión de escaneo"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sesiones_escaneo 
                    (dominios_escaneados, rutas_probadas, hallazgos_encontrados, 
                     hallazgos_criticos, estado, configuracion_usada, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_data.get('dominios_escaneados', 0),
                    session_data.get('rutas_probadas', 0),
                    session_data.get('hallazgos_encontrados', 0),
                    session_data.get('hallazgos_criticos', 0),
                    session_data.get('estado', 'completado'),
                    json.dumps(session_data.get('configuracion', {})),
                    session_data.get('notas', '')
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error guardando sesión: {e}")
            return None
    
    def update_domain_stats(self, domain_id):
        """Actualizar estadísticas de un dominio"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE dominios SET 
                        total_hallazgos = (
                            SELECT COUNT(*) FROM hallazgos WHERE dominio_id = ?
                        ),
                        hallazgos_criticos = (
                            SELECT COUNT(*) FROM hallazgos WHERE dominio_id = ? AND es_critico = 1
                        ),
                        ultimo_escaneo = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (domain_id, domain_id, domain_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas de dominio: {e}")

class ConsolidatedDictionaryManager:
    """Gestor consolidado de diccionarios y generación de rutas"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.discovered_paths = set()
        self.base_paths = set()
        self.load_dictionaries()
    
    def load_dictionaries(self):
        """Cargar todos los diccionarios disponibles"""
        # Cargar diccionario base
        if self.config.DICCIONARIO_FILE.exists():
            try:
                with open(self.config.DICCIONARIO_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word and not word.startswith('#'):
                            self.base_paths.add(word)
            except Exception as e:
                self.logger.error(f"Error cargando diccionario base: {e}")
        else:
            self.create_default_wordlist()
        
        # Cargar rutas descubiertas
        if self.config.DESCUBIERTOS_FILE.exists():
            try:
                with open(self.config.DESCUBIERTOS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word:
                            self.discovered_paths.add(word)
            except Exception as e:
                self.logger.error(f"Error cargando rutas descubiertas: {e}")
        
        self.logger.info(f"Diccionarios cargados: {len(self.base_paths)} base + {len(self.discovered_paths)} descubiertas")
    
    def create_default_wordlist(self):
        """Crear wordlist por defecto con rutas comunes"""
        default_words = [
            # Archivos comunes
            'robots.txt', 'sitemap.xml', 'favicon.ico', 'crossdomain.xml',
            'humans.txt', 'security.txt', '.well-known/security.txt',
            
            # Directorios comunes
            'admin', 'administrator', 'login', 'signin', 'panel', 'dashboard',
            'api', 'rest', 'graphql', 'swagger', 'docs', 'documentation',
            'test', 'tests', 'testing', 'dev', 'development', 'staging',
            'backup', 'backups', 'old', 'tmp', 'temp', 'cache',
            'logs', 'log', 'debug', 'status', 'health', 'metrics',
            
            # Archivos de configuración
            'config', 'configuration', 'settings', 'env', '.env',
            'config.php', 'config.json', 'config.xml', 'config.ini',
            'web.config', 'app.config', 'database.yml', 'config.yml',
            
            # CMS y frameworks comunes
            'wp-admin', 'wp-login.php', 'wp-config.php', 'wp-content',
            'drupal', 'joomla', 'magento', 'prestashop', 'opencart',
            'laravel', 'symfony', 'zend', 'codeigniter', 'cakephp',
            
            # Bases de datos y herramientas
            'phpmyadmin', 'adminer', 'phpinfo.php', 'info.php',
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            
            # APIs y servicios
            'api/v1', 'api/v2', 'api/v3', 'rest/api', 'graphql/api',
            'webhooks', 'callbacks', 'notifications', 'uploads',
            
            # Archivos sensibles
            '.git', '.git/config', '.git/HEAD', '.git/logs/HEAD',
            '.svn', '.hg', '.bzr', 'CVS', '.DS_Store',
            'Thumbs.db', 'desktop.ini', 'error_log', 'access.log',
            
            # Extensiones comunes con nombres típicos
            'index.php', 'index.html', 'index.htm', 'default.php',
            'home.php', 'main.php', 'login.php', 'admin.php',
            'search.php', 'contact.php', 'about.php', 'profile.php'
        ]
        
        try:
            with open(self.config.DICCIONARIO_FILE, 'w', encoding='utf-8') as f:
                f.write("# Diccionario de rutas para fuzzing\n")
                f.write("# Agregue sus rutas personalizadas aquí\n\n")
                for word in sorted(default_words):
                    f.write(word + '\n')
            
            self.base_paths.update(default_words)
            self.logger.info("✅ Diccionario por defecto creado")
            
        except Exception as e:
            self.logger.error(f"Error creando diccionario por defecto: {e}")
    
    def generate_intelligent_paths(self):
        """Generar rutas inteligentes basadas en patrones comunes"""
        intelligent_paths = set()
        
        # Patrones de directorios comunes
        base_dirs = ['admin', 'api', 'app', 'assets', 'backup', 'bin', 'cache', 
                    'config', 'data', 'db', 'docs', 'files', 'images', 'inc',
                    'includes', 'js', 'lib', 'logs', 'media', 'modules', 'old',
                    'private', 'public', 'scripts', 'src', 'static', 'temp',
                    'test', 'tmp', 'tools', 'uploads', 'var', 'vendor']
        
        # Extensiones comunes
        extensions = ['.php', '.html', '.htm', '.asp', '.aspx', '.jsp', 
                     '.py', '.rb', '.pl', '.cgi', '.txt', '.xml', '.json',
                     '.log', '.bak', '.old', '.conf', '.ini']
        
        # Archivos comunes
        common_files = ['index', 'default', 'main', 'home', 'login', 'admin',
                       'test', 'config', 'setup', 'install', 'readme', 'info']
        
        # Generar combinaciones
        for base_dir in base_dirs:
            intelligent_paths.add(base_dir)
            intelligent_paths.add(base_dir + '/')
            
            for file_name in common_files:
                for ext in extensions:
                    intelligent_paths.add(f"{base_dir}/{file_name}{ext}")
        
        # Agregar archivos en raíz
        for file_name in common_files:
            for ext in extensions:
                intelligent_paths.add(f"{file_name}{ext}")
        
        return list(intelligent_paths)[:500]  # Limitar cantidad
    
    def generate_bruteforce_paths(self, max_length=4, min_length=2):
        """Generar rutas por fuerza bruta limitada"""
        paths = set()
        chars = string.ascii_lowercase
        
        # Solo generar para longitudes pequeñas para evitar sobrecarga
        for length in range(min_length, min(max_length + 1, 5)):
            count = 0
            for combo in itertools.product(chars, repeat=length):
                if count >= 200:  # Limitar cantidad por longitud
                    break
                    
                path = ''.join(combo)
                paths.add(path)
                paths.add(path + '/')
                paths.add(path + '.php')
                paths.add(path + '.html')
                count += 1
        
        return list(paths)
    
    def get_comprehensive_wordlist(self):
        """Obtener wordlist completa y optimizada"""
        all_paths = set()
        
        # Agregar rutas base
        all_paths.update(self.base_paths)
        
        # Agregar rutas descubiertas
        all_paths.update(self.discovered_paths)
        
        # Agregar rutas inteligentes
        intelligent_paths = self.generate_intelligent_paths()
        all_paths.update(intelligent_paths)
        
        # Agregar algunas rutas de fuerza bruta
        if len(all_paths) < 2000:  # Solo si no hay muchas rutas
            bruteforce_paths = self.generate_bruteforce_paths()
            all_paths.update(bruteforce_paths[:300])  # Limitar cantidad
        
        # Filtrar rutas vacías y duplicadas
        filtered_paths = [path for path in all_paths if path and path.strip()]
        
        self.logger.info(f"Wordlist completa generada: {len(filtered_paths)} rutas")
        return sorted(filtered_paths)
    
    def save_discovered_path(self, path):
        """Guardar nueva ruta descubierta"""
        if path and path not in self.discovered_paths:
            self.discovered_paths.add(path)
            try:
                with open(self.config.DESCUBIERTOS_FILE, 'a', encoding='utf-8') as f:
                    f.write(path + '\n')
            except Exception as e:
                self.logger.error(f"Error guardando ruta descubierta: {e}")

class ConsolidatedFuzzingEngine:
    """Motor de fuzzing consolidado y optimizado"""
    
    def __init__(self, config, db_manager, dict_manager):
        self.config = config
        self.db = db_manager
        self.dict_manager = dict_manager
        self.logger = logging.getLogger(__name__)
        
        # Configurar sesión HTTP optimizada
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        
        # Configurar adaptadores con retry
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Deshabilitar warnings SSL para testing
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Estadísticas de la sesión
        self.session_stats = {
            'requests_sent': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'critical_findings': 0,
            'start_time': None
        }
    
    def load_domains(self):
        """Cargar y validar dominios desde archivo"""
        domains = []
        
        if not self.config.DOMINIOS_FILE.exists():
            self.logger.warning("Archivo de dominios no encontrado, creando ejemplo...")
            self.create_sample_domains_file()
            return self.load_domains()
        
        try:
            with open(self.config.DOMINIOS_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        # Parsear diferentes formatos
                        if ':' in line and not line.startswith('http'):
                            if line.count(':') == 1:
                                host, port = line.split(':', 1)
                                protocol = 'https' if port == '443' else 'http'
                                domain = f"{protocol}://{host}:{port}"
                            else:
                                continue
                        elif not line.startswith('http'):
                            domain = f"https://{line}"
                        else:
                            domain = line
                        
                        # Validar formato básico
                        parsed = urlparse(domain)
                        if parsed.netloc:
                            domains.append(domain)
                            self.save_domain_to_db(domain)
                        
                    except Exception as e:
                        self.logger.warning(f"Error procesando línea {line_num}: {line} - {e}")
                        continue
            
        except Exception as e:
            self.logger.error(f"Error cargando dominios: {e}")
        
        self.logger.info(f"Dominios cargados: {len(domains)}")
        return domains
    
    def create_sample_domains_file(self):
        """Crear archivo de dominios de ejemplo"""
        sample_content = """# Configuración de dominios para fuzzing
# Formato soportado:
#   https://dominio.com
#   http://dominio.com:8080  
#   dominio.com:443
#   dominio.com (asume HTTPS)

# ⚠️  IMPORTANTE: Solo use dominios que le pertenezcan o tenga autorización
# ⚠️  El fuzzing no autorizado puede ser ilegal

# Dominios de prueba seguros (para PoC y testing)
https://httpbin.org
https://jsonplaceholder.typicode.com

# Ejemplos para sus dominios reales:
# https://miempresa.com
# https://app.miempresa.com
# https://api.miempresa.com
# miempresa.com:80
# test.miempresa.com:8080

# Subdominios comunes a probar:
# dev.miempresa.com
# staging.miempresa.com
# admin.miempresa.com
# panel.miempresa.com
"""
        try:
            with open(self.config.DOMINIOS_FILE, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            self.logger.info("✅ Archivo de dominios de ejemplo creado")
        except Exception as e:
            self.logger.error(f"Error creando archivo de dominios: {e}")
    
    def save_domain_to_db(self, domain):
        """Guardar dominio en base de datos"""
        try:
            parsed = urlparse(domain)
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO dominios (dominio, protocolo, puerto)
                    VALUES (?, ?, ?)
                ''', (parsed.netloc, parsed.scheme, parsed.port or (443 if parsed.scheme == 'https' else 80)))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error guardando dominio: {e}")
    
    def is_critical_finding(self, path, status_code, headers=None):
        """Determinar si un hallazgo es crítico con análisis mejorado"""
        path_lower = path.lower()
        
        # Verificar rutas críticas
        for critical_path in self.config.CRITICAL_PATHS:
            if critical_path in path_lower:
                return True
        
        # Verificar extensiones críticas
        for critical_ext in self.config.CRITICAL_EXTENSIONS:
            if path_lower.endswith(critical_ext):
                return True
        
        # Códigos de respuesta críticos
        critical_codes = [200, 403, 500]  # 200=acceso, 403=existe pero prohibido, 500=error
        if status_code in critical_codes:
            # Análisis más específico para código 200
            if status_code == 200:
                critical_keywords = ['admin', 'login', 'config', 'backup', 'password', 'secret']
                if any(keyword in path_lower for keyword in critical_keywords):
                    return True
        
        # Análisis de headers si están disponibles
        if headers:
            server = headers.get('server', '').lower()
            # Detección de tecnologías vulnerables
            vulnerable_servers = ['apache/2.2', 'nginx/1.0', 'iis/6.0']
            if any(vuln in server for vuln in vulnerable_servers):
                return True
        
        return False
    
    def fuzz_domain(self, domain, wordlist):
        """Realizar fuzzing completo en un dominio"""
        self.logger.info(f"🎯 Iniciando fuzzing en: {domain}")
        findings = []
        start_time = time.time()
        
        # Obtener ID del dominio
        domain_id = self.get_domain_id(domain)
        
        for i, path in enumerate(wordlist):
            if not path:
                continue
            
            # Construir URL
            if path.startswith('/'):
                url = domain.rstrip('/') + path
            else:
                url = urljoin(domain.rstrip('/') + '/', path.lstrip('/'))
            
            try:
                # Realizar request con timeout
                response_start = time.time()
                response = self.session.get(
                    url,
                    timeout=self.config.TIMEOUT,
                    allow_redirects=False,
                    verify=False
                )
                response_time = time.time() - response_start
                
                self.session_stats['requests_sent'] += 1
                
                # Verificar si el código es interesante
                if response.status_code in self.config.INTERESTING_CODES:
                    self.session_stats['successful_requests'] += 1
                    
                    # Crear hash del contenido
                    content_hash = hashlib.md5(response.content).hexdigest()
                    
                    # Determinar criticidad
                    is_critical = self.is_critical_finding(
                        path, 
                        response.status_code, 
                        response.headers
                    )
                    
                    if is_critical:
                        self.session_stats['critical_findings'] += 1
                    
                    finding = {
                        'domain_id': domain_id,
                        'url': url,
                        'path': path,
                        'status_code': response.status_code,
                        'content_length': len(response.content),
                        'response_time': response_time,
                        'content_hash': content_hash,
                        'headers': dict(response.headers),
                        'is_critical': is_critical,
                        'timestamp': datetime.now()
                    }
                    
                    findings.append(finding)
                    
                    # Log del hallazgo
                    status_icon = "🚨" if is_critical else "✅"
                    self.logger.info(f"  {status_icon} [{response.status_code}] {url} ({response_time:.2f}s)")
                    
                    # Guardar ruta descubierta para futuras ejecuciones
                    if response.status_code == 200:
                        self.dict_manager.save_discovered_path(path)
                
                # Delay entre requests para no sobrecargar
                if self.config.REQUEST_DELAY > 0:
                    time.sleep(self.config.REQUEST_DELAY)
                
                # Progreso cada 100 requests
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    self.logger.info(f"  Progreso: {i+1}/{len(wordlist)} rutas ({rate:.1f} req/s)")
                
            except requests.exceptions.Timeout:
                self.session_stats['failed_requests'] += 1
                continue
            except requests.exceptions.RequestException as e:
                self.session_stats['failed_requests'] += 1
                continue
            except Exception as e:
                self.logger.error(f"Error fuzzing {url}: {str(e)}")
                self.session_stats['failed_requests'] += 1
        
        # Guardar hallazgos en base de datos
        if findings:
            self.save_findings_to_db(findings)
            self.db.update_domain_stats(domain_id)
        
        elapsed = time.time() - start_time
        self.logger.info(f"✅ Fuzzing completado en {domain}: {len(findings)} hallazgos en {elapsed:.1f}s")
        
        return findings
    
    def get_domain_id(self, domain):
        """Obtener ID del dominio desde la base de datos"""
        try:
            parsed_domain = urlparse(domain).netloc
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM dominios WHERE dominio = ?", (parsed_domain,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error obteniendo ID de dominio: {e}")
            return None
    
    def save_findings_to_db(self, findings):
        """Guardar hallazgos en base de datos con transacción"""
        if not findings:
            return
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                for finding in findings:
                    # Insertar hallazgo
                    cursor.execute('''
                        INSERT INTO hallazgos 
                        (dominio_id, url_completa, ruta, codigo_http, es_critico, 
                         tamano_respuesta, tiempo_respuesta, contenido_hash, 
                         headers_respuesta, herramienta)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        finding['domain_id'],
                        finding['url'],
                        finding['path'],
                        finding['status_code'],
                        finding['is_critical'],
                        finding['content_length'],
                        finding['response_time'],
                        finding['content_hash'],
                        json.dumps(finding['headers']),
                        'fuzzing_engine_v2'
                    ))
                    
                    # Crear alerta automática si es crítico
                    if finding['is_critical']:
                        hallazgo_id = cursor.lastrowid
                        
                        # Determinar nivel de severidad
                        severity = self.calculate_severity(finding)
                        
                        cursor.execute('''
                            INSERT INTO alertas 
                            (hallazgo_id, tipo_alerta, nivel_severidad, mensaje, automatica)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            hallazgo_id,
                            'critica',
                            severity,
                            f"🚨 Hallazgo crítico: {finding['path']} (HTTP {finding['status_code']}) en {urlparse(finding['url']).netloc}",
                            True
                        ))
                
                conn.commit()
                self.logger.info(f"💾 Guardados {len(findings)} hallazgos en base de datos")
                
        except Exception as e:
            self.logger.error(f"Error guardando hallazgos: {e}")
    
    def calculate_severity(self, finding):
        """Calcular nivel de severidad de 1-5"""
        severity = 1
        
        # Incrementar por código de respuesta
        if finding['status_code'] == 200:
            severity += 2
        elif finding['status_code'] in [403, 500]:
            severity += 1
        
        # Incrementar por tipo de ruta
        critical_keywords = ['admin', 'login', 'config', 'backup', '.git', 'password']
        path_lower = finding['path'].lower()
        
        for keyword in critical_keywords:
            if keyword in path_lower:
                severity += 1
                break
        
        # Máximo nivel 5
        return min(severity, 5)
    
    def run_comprehensive_scan(self):
        """Ejecutar escaneo completo y consolidado"""
        self.logger.info("🚀 INICIANDO ESCANEO COMPLETO CONSOLIDADO")
        self.logger.info("=" * 60)
        
        self.session_stats['start_time'] = datetime.now()
        
        # Cargar configuración
        domains = self.load_domains()
        wordlist = self.dict_manager.get_comprehensive_wordlist()
        
        if not domains:
            self.logger.error("❌ No hay dominios configurados para escanear")
            return []
        
        if not wordlist:
            self.logger.error("❌ No hay wordlist disponible")
            return []
        
        self.logger.info(f"📊 Configuración del escaneo:")
        self.logger.info(f"   • Dominios a escanear: {len(domains)}")
        self.logger.info(f"   • Rutas a probar: {len(wordlist)}")
        self.logger.info(f"   • Workers concurrentes: {self.config.MAX_WORKERS}")
        self.logger.info(f"   • Timeout por request: {self.config.TIMEOUT}s")
        self.logger.info(f"   • Sistema operativo: {self.config.system_info['os']}")
        self.logger.info("")
        
        # Guardar información de sesión inicial
        session_data = {
            'dominios_escaneados': len(domains),
            'rutas_probadas': len(wordlist),
            'estado': 'iniciado',
            'configuracion': {
                'max_workers': self.config.MAX_WORKERS,
                'timeout': self.config.TIMEOUT,
                'total_rutas': len(wordlist)
            }
        }
        session_id = self.db.save_scan_session(session_data)
        
        all_findings = []
        
        # Ejecutar fuzzing con ThreadPoolExecutor
        try:
            with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                future_to_domain = {
                    executor.submit(self.fuzz_domain, domain, wordlist): domain 
                    for domain in domains
                }
                
                for future in as_completed(future_to_domain):
                    domain = future_to_domain[future]
                    try:
                        findings = future.result()
                        all_findings.extend(findings)
                        
                        critical_count = len([f for f in findings if f['is_critical']])
                        self.logger.info(f"✅ Completado {domain}: {len(findings)} hallazgos ({critical_count} críticos)")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error escaneando {domain}: {str(e)}")
        
        except KeyboardInterrupt:
            self.logger.warning("🛑 Escaneo interrumpido por el usuario")
        except Exception as e:
            self.logger.error(f"❌ Error durante el escaneo: {e}")
        
        # Finalizar sesión
        end_time = datetime.now()
        duration = end_time - self.session_stats['start_time']
        
        # Actualizar estadísticas de sesión
        session_data.update({
            'hallazgos_encontrados': len(all_findings),
            'hallazgos_criticos': self.session_stats['critical_findings'],
            'estado': 'completado',
            'notas': f"Duración: {duration}, Requests: {self.session_stats['requests_sent']}"
        })
        
        # Generar reporte completo
        self.generate_comprehensive_report(all_findings, duration)
        
        return all_findings
    
    def generate_comprehensive_report(self, findings, duration):
        """Generar reporte completo y detallado"""
        end_time = datetime.now()
        
        # Análisis detallado de resultados
        critical_findings = [f for f in findings if f['is_critical']]
        status_codes = {}
        domains_affected = set()
        
        for finding in findings:
            code = finding['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
            domains_affected.add(urlparse(finding['url']).netloc)
        
        # Estadísticas de rendimiento
        total_requests = self.session_stats['requests_sent']
        success_rate = (self.session_stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        requests_per_second = total_requests / duration.total_seconds() if duration.total_seconds() > 0 else 0
        
        # Crear reporte completo
        report = {
            'metadata': {
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'duration_formatted': str(duration),
                'fuzzing_engine_version': '2.0',
                'system_info': self.config.system_info
            },
            'configuration': {
                'max_workers': self.config.MAX_WORKERS,
                'timeout': self.config.TIMEOUT,
                'request_delay': self.config.REQUEST_DELAY,
                'critical_paths_count': len(self.config.CRITICAL_PATHS)
            },
            'statistics': {
                'total_findings': len(findings),
                'critical_findings': len(critical_findings),
                'domains_affected': len(domains_affected),
                'unique_status_codes': len(status_codes),
                'total_requests_sent': total_requests,
                'successful_requests': self.session_stats['successful_requests'],
                'failed_requests': self.session_stats['failed_requests'],
                'success_rate_percent': round(success_rate, 2),
                'requests_per_second': round(requests_per_second, 2)
            },
            'analysis': {
                'status_codes_distribution': status_codes,
                'domains_list': list(domains_affected),
                'critical_paths_found': [f['path'] for f in critical_findings],
                'top_response_codes': sorted(status_codes.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'findings': {
                'critical_sample': critical_findings[:10],  # Muestra de críticos
                'all_findings_sample': findings[:20]        # Muestra general
            }
        }
        
        # Guardar reporte JSON
        try:
            report_file = self.config.RESULTS_DIR / f"comprehensive_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str, ensure_ascii=False)
            
            self.logger.info(f"📄 Reporte guardado en: {report_file}")
        except Exception as e:
            self.logger.error(f"Error guardando reporte: {e}")
        
        # Mostrar resumen en consola
        self.print_final_summary(report)
    
    def print_final_summary(self, report):
        """Mostrar resumen final en consola"""
        stats = report['statistics']
        analysis = report['analysis']
        
        print("")
        print("🎉 ESCANEO COMPLETADO - RESUMEN EJECUTIVO")
        print("=" * 60)
        print(f"⏱️  Duración total: {report['metadata']['duration_formatted']}")
        print(f"📊 Estadísticas de fuzzing:")
        print(f"   • Total de hallazgos: {stats['total_findings']}")
        print(f"   • Hallazgos críticos: {stats['critical_findings']}")
        print(f"   • Dominios afectados: {stats['domains_affected']}")
        print(f"   • Requests enviados: {stats['total_requests_sent']}")
        print(f"   • Tasa de éxito: {stats['success_rate_percent']}%")
        print(f"   • Velocidad: {stats['requests_per_second']} req/s")
        
        if analysis['status_codes_distribution']:
            print(f"\n📈 Distribución de códigos HTTP:")
            for code, count in analysis['top_response_codes']:
                print(f"   • {code}: {count} respuestas")
        
        if stats['critical_findings'] > 0:
            print(f"\n🚨 ATENCIÓN: {stats['critical_findings']} HALLAZGOS CRÍTICOS ENCONTRADOS!")
            print("   Rutas críticas detectadas:")
            for path in analysis['critical_paths_found'][:5]:
                print(f"     • {path}")
            if len(analysis['critical_paths_found']) > 5:
                print(f"     ... y {len(analysis['critical_paths_found']) - 5} más")
            print("\n   🔍 Revisar inmediatamente en el dashboard web")
            print("   💻 Comando: python app.py")
        else:
            print("\n✅ No se encontraron hallazgos críticos")
        
        print(f"\n📁 Archivos generados:")
        print(f"   • Base de datos: {self.config.DATABASE_FILE}")
        print(f"   • Logs: {self.config.LOGS_DIR}")
        print(f"   • Reportes: {self.config.RESULTS_DIR}")

# Funciones principales de entrada

def run_fuzzing_scan():
    """Función principal para ejecutar escaneo de fuzzing"""
    try:
        config = FuzzingConfig()
        db_manager = ConsolidatedDatabaseManager(config.DATABASE_FILE)
        dict_manager = ConsolidatedDictionaryManager(config)
        fuzzing_engine = ConsolidatedFuzzingEngine(config, db_manager, dict_manager)
        
        findings = fuzzing_engine.run_comprehensive_scan()
        
        return findings
        
    except KeyboardInterrupt:
        print("\n🛑 Escaneo interrumpido por el usuario")
        return []
    except Exception as e:
        print(f"❌ Error ejecutando escaneo: {e}")
        import traceback
        traceback.print_exc()
        return []

def setup_fuzzing_environment():
    """Configurar entorno inicial del sistema de fuzzing"""
    try:
        config = FuzzingConfig()
        db_manager = ConsolidatedDatabaseManager(config.DATABASE_FILE)
        dict_manager = ConsolidatedDictionaryManager(config)
        
        print("✅ Sistema de fuzzing configurado correctamente")
        print(f"📁 Directorio base: {config.BASE_DIR}")
        print(f"💾 Base de datos: {config.DATABASE_FILE}")
        print(f"📋 Logs: {config.LOGS_DIR}")
        print(f"📚 Diccionarios: {config.DICCIONARIO_FILE}")
        print(f"🌐 Sistema: {config.system_info['os']} {config.system_info['release']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando entorno: {e}")
        return False

def run_quick_test():
    """Ejecutar prueba rápida del sistema"""
    print("🧪 Ejecutando prueba rápida del sistema...")
    
    try:
        config = FuzzingConfig()
        
        # Verificar que httpbin.org esté disponible
        test_url = "https://httpbin.org/status/200"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Conectividad verificada")
            
            # Crear dominios de prueba si no existen
            if not config.DOMINIOS_FILE.exists():
                test_domains = "https://httpbin.org\nhttps://jsonplaceholder.typicode.com\n"
                with open(config.DOMINIOS_FILE, 'w', encoding='utf-8') as f:
                    f.write(test_domains)
                print("✅ Dominios de prueba creados")
            
            # Ejecutar escaneo limitado
            db_manager = ConsolidatedDatabaseManager(config.DATABASE_FILE)
            dict_manager = ConsolidatedDictionaryManager(config)
            fuzzing_engine = ConsolidatedFuzzingEngine(config, db_manager, dict_manager)
            
            # Test con wordlist reducida
            test_wordlist = ['status/200', 'json', 'headers', 'user-agent', 'admin', 'test']
            test_domain = "https://httpbin.org"
            
            findings = fuzzing_engine.fuzz_domain(test_domain, test_wordlist)
            
            print(f"✅ Prueba completada: {len(findings)} hallazgos encontrados")
            return True
        else:
            print("❌ Error de conectividad")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba rápida: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(
        description='Sistema de Fuzzing Web Consolidado v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python fuzzing_engine.py --scan          # Escaneo completo
  python fuzzing_engine.py --setup         # Configurar entorno
  python fuzzing_engine.py --test          # Prueba rápida
  python fuzzing_engine.py --info          # Información del sistema
        """
    )
    
    parser.add_argument('--scan', action='store_true', 
                       help='Ejecutar escaneo completo de fuzzing')
    parser.add_argument('--setup', action='store_true', 
                       help='Configurar entorno inicial del sistema')
    parser.add_argument('--test', action='store_true', 
                       help='Ejecutar prueba rápida de funcionalidad')
    parser.add_argument('--info', action='store_true', 
                       help='Mostrar información del sistema')
    
    args = parser.parse_args()
    
    # Banner del sistema
    print("🔍 Sistema de Fuzzing Web Consolidado v2.0")
    print("=" * 50)
    
    if args.setup:
        setup_fuzzing_environment()
    elif args.scan:
        findings = run_fuzzing_scan()
        print(f"\n📊 Resumen: {len(findings)} hallazgos encontrados")
    elif args.test:
        success = run_quick_test()
        if success:
            print("✅ Todas las pruebas pasaron correctamente")
        else:
            print("❌ Algunas pruebas fallaron")
    elif args.info:
        config = FuzzingConfig()
        print(f"Sistema operativo: {config.system_info['os']} {config.system_info['release']}")
        print(f"Python: {config.system_info['python_version']}")
        print(f"Directorio base: {config.BASE_DIR}")
        print(f"Workers configurados: {config.MAX_WORKERS}")
        print(f"Timeout: {config.TIMEOUT}s")
    else:
        parser.print_help()
        print("\n💡 Recomendación: Comience con --setup para configurar el entorno")