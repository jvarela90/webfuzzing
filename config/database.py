# config/database.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import threading
from config.settings import Config 

class DatabaseManager:
    """Gestor de base de datos SQLite"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.base_dir / config.get('database.name')
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos con tablas necesarias"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Tabla de dominios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    port INTEGER DEFAULT 443,
                    protocol TEXT DEFAULT 'https',
                    status TEXT DEFAULT 'active',
                    last_scan TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de subdominios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subdomains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER NOT NULL,
                    subdomain TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (domain_id) REFERENCES domains (id),
                    UNIQUE(domain_id, subdomain)
                )
            ''')
            
            # Tabla de rutas descubiertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discovered_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER NOT NULL,
                    subdomain_id INTEGER,
                    path TEXT NOT NULL,
                    full_url TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    content_length INTEGER,
                    content_type TEXT,
                    response_time REAL,
                    is_critical BOOLEAN DEFAULT FALSE,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (domain_id) REFERENCES domains (id),
                    FOREIGN KEY (subdomain_id) REFERENCES subdomains (id)
                )
            ''')
            
            # Tabla de diccionarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dictionary_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    source TEXT DEFAULT 'manual',
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')
            
            # Tabla de escaneos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_type TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    domains_count INTEGER DEFAULT 0,
                    paths_found INTEGER DEFAULT 0,
                    critical_findings INTEGER DEFAULT 0,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    config TEXT
                )
            ''')
            
            # Tabla de alertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    url TEXT,
                    status TEXT DEFAULT 'new',
                    analyst_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            ''')
            
            # Crear índices para optimizar consultas
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domains_domain ON domains(domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_paths_domain ON discovered_paths(domain_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_paths_critical ON discovered_paths(is_critical)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_paths_discovered ON discovered_paths(discovered_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)')
            
            conn.commit()
            conn.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch: bool = False) -> Any:
        """Ejecutar consulta SQL de forma thread-safe"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            cursor = conn.cursor()
            
            try:
                cursor.execute(query, params)
                
                if fetch:
                    if 'SELECT' in query.upper():
                        result = cursor.fetchall()
                    else:
                        result = cursor.fetchone()
                else:
                    result = cursor.rowcount
                    
                conn.commit()
                return result
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
    
    def add_domain(self, domain: str, port: int = 443, protocol: str = 'https') -> int:
        """Agregar dominio a la base de datos"""
        query = '''
            INSERT OR REPLACE INTO domains (domain, port, protocol, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        self.execute_query(query, (domain, port, protocol))
        
        # Obtener ID del dominio
        query = 'SELECT id FROM domains WHERE domain = ?'
        result = self.execute_query(query, (domain,), fetch=True)
        return result[0]['id'] if result else None
    
    def get_active_domains(self) -> List[Dict]:
        """Obtener dominios activos"""
        query = 'SELECT * FROM domains WHERE status = "active" ORDER BY domain'
        return [dict(row) for row in self.execute_query(query, fetch=True)]
    
    def add_discovered_path(self, domain_id: int, path: str, full_url: str, 
                          status_code: int, **kwargs) -> int:
        """Agregar ruta descubierta"""
        is_critical = any(critical in path.lower() 
                         for critical in self.config.get('fuzzing.critical_paths'))
        
        query = '''
            INSERT OR REPLACE INTO discovered_paths 
            (domain_id, path, full_url, status_code, content_length, 
             content_type, response_time, is_critical, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        params = (
            domain_id, path, full_url, status_code,
            kwargs.get('content_length'),
            kwargs.get('content_type'),
            kwargs.get('response_time'),
            is_critical
        )
        
        self.execute_query(query, params)
        
        # Si es crítico, crear alerta
        if is_critical:
            self.create_alert(
                'critical_path',
                'high',
                f'Ruta crítica encontrada: {path}',
                f'Se encontró una ruta crítica en {full_url}',
                full_url
            )
    
    def create_alert(self, alert_type: str, severity: str, title: str, 
                    message: str, url: str = None) -> int:
        """Crear nueva alerta"""
        query = '''
            INSERT INTO alerts (type, severity, title, message, url)
            VALUES (?, ?, ?, ?, ?)
        '''
        self.execute_query(query, (alert_type, severity, title, message, url))
    
    def get_recent_findings(self, hours: int = 24) -> List[Dict]:
        """Obtener hallazgos recientes"""
        query = '''
            SELECT dp.*, d.domain
            FROM discovered_paths dp
            JOIN domains d ON dp.domain_id = d.id
            WHERE dp.discovered_at >= datetime('now', '-{} hours')
            ORDER BY dp.discovered_at DESC
        '''.format(hours)
        
        return [dict(row) for row in self.execute_query(query, fetch=True)]
    
    def get_critical_findings(self, unresolved_only: bool = True) -> List[Dict]:
        """Obtener hallazgos críticos"""
        query = '''
            SELECT dp.*, d.domain
            FROM discovered_paths dp
            JOIN domains d ON dp.domain_id = d.id
            WHERE dp.is_critical = TRUE
        '''
        
        if unresolved_only:
            query += ' AND dp.id NOT IN (SELECT DISTINCT url FROM alerts WHERE status = "resolved" AND url = dp.full_url)'
        
        query += ' ORDER BY dp.discovered_at DESC'
        
        return [dict(row) for row in self.execute_query(query, fetch=True)]