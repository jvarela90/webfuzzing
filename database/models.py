# database/models.py
"""
Modelos de datos para WebFuzzing Pro
Definición de estructuras de tablas y relaciones
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ScanStatus(Enum):
    """Estados de escaneo"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class AlertSeverity(Enum):
    """Niveles de severidad de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Estados de alertas"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

@dataclass
class Domain:
    """Modelo para dominios"""
    id: Optional[int] = None
    domain: str = ""
    protocol: str = "https"
    port: int = 443
    is_active: bool = True
    last_scan: Optional[str] = None
    total_findings: int = 0
    critical_findings: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    scan_frequency: int = 24  # horas
    custom_headers: Optional[str] = None
    auth_required: bool = False
    auth_token: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'domain': self.domain,
            'protocol': self.protocol,
            'port': self.port,
            'is_active': self.is_active,
            'last_scan': self.last_scan,
            'total_findings': self.total_findings,
            'critical_findings': self.critical_findings,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'scan_frequency': self.scan_frequency,
            'custom_headers': self.custom_headers,
            'auth_required': self.auth_required,
            'auth_token': self.auth_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Domain':
        """Crear desde diccionario"""
        return cls(**data)

@dataclass 
class DiscoveredPath:
    """Modelo para rutas descubiertas"""
    id: Optional[int] = None
    domain_id: int = 0
    path: str = ""
    full_url: str = ""
    status_code: int = 0
    content_length: int = 0
    content_type: str = ""
    response_time: float = 0.0
    is_critical: bool = False
    discovered_at: Optional[str] = None
    last_checked: Optional[str] = None
    method: str = "GET"
    response_hash: Optional[str] = None
    headers: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'path': self.path,
            'full_url': self.full_url,
            'status_code': self.status_code,
            'content_length': self.content_length,
            'content_type': self.content_type,
            'response_time': self.response_time,
            'is_critical': self.is_critical,
            'discovered_at': self.discovered_at,
            'last_checked': self.last_checked,
            'method': self.method,
            'response_hash': self.response_hash,
            'headers': self.headers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiscoveredPath':
        """Crear desde diccionario"""
        return cls(**data)

@dataclass
class ScanSession:
    """Modelo para sesiones de escaneo"""
    id: Optional[int] = None
    domain_id: int = 0
    status: str = ScanStatus.PENDING.value
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    paths_found: int = 0
    critical_found: int = 0
    scan_type: str = "full"
    wordlist_used: Optional[str] = None
    config_used: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'status': self.status,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'paths_found': self.paths_found,
            'critical_found': self.critical_found,
            'scan_type': self.scan_type,
            'wordlist_used': self.wordlist_used,
            'config_used': self.config_used,
            'error_message': self.error_message
        }

@dataclass
class Alert:
    """Modelo para alertas"""
    id: Optional[int] = None
    domain_id: Optional[int] = None
    path_id: Optional[int] = None
    alert_type: str = "finding"
    severity: str = AlertSeverity.MEDIUM.value
    status: str = AlertStatus.NEW.value
    title: str = ""
    message: str = ""
    url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    resolved_at: Optional[str] = None
    analyst_notes: Optional[str] = None
    false_positive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'path_id': self.path_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'status': self.status,
            'title': self.title,
            'message': self.message,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'resolved_at': self.resolved_at,
            'analyst_notes': self.analyst_notes,
            'false_positive': self.false_positive
        }

@dataclass
class WordlistEntry:
    """Modelo para entradas de wordlists"""
    id: Optional[int] = None
    wordlist_name: str = ""
    word: str = ""
    category: str = "general"
    priority: int = 1
    is_active: bool = True
    success_rate: float = 0.0
    last_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'wordlist_name': self.wordlist_name,
            'word': self.word,
            'category': self.category,
            'priority': self.priority,
            'is_active': self.is_active,
            'success_rate': self.success_rate,
            'last_used': self.last_used
        }

@dataclass
class SystemConfig:
    """Modelo para configuración del sistema"""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    category: str = "general"
    description: Optional[str] = None
    is_encrypted: bool = False
    updated_at: Optional[str] = None
    updated_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'category': self.category,
            'description': self.description,
            'is_encrypted': self.is_encrypted,
            'updated_at': self.updated_at,
            'updated_by': self.updated_by
        }

class DatabaseSchema:
    """Esquema de base de datos SQL"""
    
    TABLES = {
        'domains': '''
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL UNIQUE,
                protocol TEXT DEFAULT 'https',
                port INTEGER DEFAULT 443,
                is_active BOOLEAN DEFAULT 1,
                last_scan TIMESTAMP,
                total_findings INTEGER DEFAULT 0,
                critical_findings INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_frequency INTEGER DEFAULT 24,
                custom_headers TEXT,
                auth_required BOOLEAN DEFAULT 0,
                auth_token TEXT
            )
        ''',
        
        'discovered_paths': '''
            CREATE TABLE IF NOT EXISTS discovered_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                full_url TEXT NOT NULL,
                status_code INTEGER,
                content_length INTEGER DEFAULT 0,
                content_type TEXT,
                response_time REAL DEFAULT 0.0,
                is_critical BOOLEAN DEFAULT 0,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                method TEXT DEFAULT 'GET',
                response_hash TEXT,
                headers TEXT,
                FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE,
                UNIQUE(domain_id, path)
            )
        ''',
        
        'scan_sessions': '''
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                paths_found INTEGER DEFAULT 0,
                critical_found INTEGER DEFAULT 0,
                scan_type TEXT DEFAULT 'full',
                wordlist_used TEXT,
                config_used TEXT,
                error_message TEXT,
                FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE
            )
        ''',
        
        'alerts': '''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_id INTEGER,
                path_id INTEGER,
                alert_type TEXT DEFAULT 'finding',
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'new',
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                analyst_notes TEXT,
                false_positive BOOLEAN DEFAULT 0,
                FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE SET NULL,
                FOREIGN KEY (path_id) REFERENCES discovered_paths (id) ON DELETE SET NULL
            )
        ''',
        
        'wordlist_entries': '''
            CREATE TABLE IF NOT EXISTS wordlist_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wordlist_name TEXT NOT NULL,
                word TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                priority INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                last_used TIMESTAMP,
                UNIQUE(wordlist_name, word)
            )
        ''',
        
        'system_config': '''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                description TEXT,
                is_encrypted BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT DEFAULT 'system'
            )
        '''
    }
    
    INDEXES = [
        'CREATE INDEX IF NOT EXISTS idx_domains_active ON domains(is_active)',
        'CREATE INDEX IF NOT EXISTS idx_domains_last_scan ON domains(last_scan)',
        'CREATE INDEX IF NOT EXISTS idx_paths_domain_id ON discovered_paths(domain_id)',
        'CREATE INDEX IF NOT EXISTS idx_paths_critical ON discovered_paths(is_critical)',
        'CREATE INDEX IF NOT EXISTS idx_paths_discovered_at ON discovered_paths(discovered_at)',
        'CREATE INDEX IF NOT EXISTS idx_paths_status_code ON discovered_paths(status_code)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_domain_id ON scan_sessions(domain_id)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_status ON scan_sessions(status)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON scan_sessions(started_at)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_domain_id ON alerts(domain_id)',
        'CREATE INDEX IF NOT EXISTS idx_wordlist_name ON wordlist_entries(wordlist_name)',
        'CREATE INDEX IF NOT EXISTS idx_wordlist_active ON wordlist_entries(is_active)',
        'CREATE INDEX IF NOT EXISTS idx_config_category ON system_config(category)'
    ]
    
    @classmethod
    def create_all_tables(cls, cursor: sqlite3.Cursor) -> None:
        """Crear todas las tablas e índices"""
        # Crear tablas
        for table_name, sql in cls.TABLES.items():
            cursor.execute(sql)
        
        # Crear índices
        for index_sql in cls.INDEXES:
            cursor.execute(index_sql)
    
    @classmethod
    def get_table_info(cls, table_name: str) -> Optional[str]:
        """Obtener SQL de creación de tabla"""
        return cls.TABLES.get(table_name)