#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Base de Datos Unificado
Sistema centralizado para todas las operaciones de base de datos
"""

import sqlite3
import json
import logging
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass

from .config import get_config
from .exceptions import (
    DatabaseError, DatabaseConnectionError, DatabaseIntegrityError,
    DatabaseMigrationError, handle_exceptions
)


@dataclass
class FindingRecord:
    """Registro de hallazgo"""
    id: Optional[int] = None
    domain_id: int = None
    url: str = ""
    path: str = ""
    status_code: int = 0
    is_critical: bool = False
    discovered_at: datetime = None
    content_hash: str = ""
    response_size: int = 0
    tool: str = "internal"


@dataclass
class DomainRecord:
    """Registro de dominio"""
    id: Optional[int] = None
    domain: str = ""
    protocol: str = "https"
    port: Optional[int] = None
    active: bool = True
    added_at: datetime = None
    last_scan: Optional[datetime] = None


@dataclass
class AlertRecord:
    """Registro de alerta"""
    id: Optional[int] = None
    finding_id: Optional[int] = None
    alert_type: str = ""
    message: str = ""
    status: str = "pending"
    analyst: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime = None
    attended_at: Optional[datetime] = None


class DatabaseManager:
    """Gestor centralizado de base de datos"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config()
        self.db_path = Path(db_path) if db_path else self.config.get_db_path()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self.init_database()
        
        # Configurar optimizaciones
        self._setup_optimizations()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones thread-safe"""
        conn = None
        try:
            with self._lock:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                
                # Habilitar WAL mode para mejor concurrencia
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA foreign_keys=ON")
                
                yield conn
                
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseConnectionError(f"Database connection failed: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def _setup_optimizations(self):
        """Configurar optimizaciones de base de datos"""
        try:
            with self.get_connection() as conn:
                # Índices para mejor performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_hallazgos_dominio ON hallazgos(dominio_id)",
                    "CREATE INDEX IF NOT EXISTS idx_hallazgos_fecha ON hallazgos(fecha_descubierto)",
                    "CREATE INDEX IF NOT EXISTS idx_hallazgos_critico ON hallazgos(es_critico)",
                    "CREATE INDEX IF NOT EXISTS idx_alertas_estado ON alertas(estado)",
                    "CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha_creada)",
                    "CREATE INDEX IF NOT EXISTS idx_dominios_activo ON dominios(activo)",
                ]
                
                for index_sql in indexes:
                    conn.execute(index_sql)
                
                conn.commit()
                self.logger.info("Database optimizations applied")
                
        except Exception as e:
            self.logger.warning(f"Could not apply optimizations: {e}")
    
    @handle_exceptions("Database initialization")
    def init_database(self):
        """Inicializar esquema de base de datos"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de dominios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dominios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dominio TEXT UNIQUE NOT NULL,
                    protocolo TEXT NOT NULL DEFAULT 'https',
                    puerto INTEGER,
                    activo BOOLEAN DEFAULT 1,
                    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ultimo_escaneo DATETIME,
                    metadata TEXT DEFAULT '{}',
                    CONSTRAINT valid_protocol CHECK (protocolo IN ('http', 'https'))
                )
            ''')
            
            # Tabla de hallazgos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hallazgos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dominio_id INTEGER NOT NULL,
                    url_completa TEXT NOT NULL,
                    ruta TEXT NOT NULL,
                    codigo_http INTEGER NOT NULL,
                    es_critico BOOLEAN DEFAULT 0,
                    fecha_descubierto DATETIME DEFAULT CURRENT_TIMESTAMP,
                    contenido_hash TEXT,
                    tamano_respuesta INTEGER DEFAULT 0,
                    herramienta TEXT DEFAULT 'internal',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (dominio_id) REFERENCES dominios (id) ON DELETE CASCADE,
                    CONSTRAINT valid_status_code CHECK (codigo_http BETWEEN 100 AND 599)
                )
            ''')
            
            # Tabla de alertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hallazgo_id INTEGER,
                    tipo_alerta TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    estado TEXT DEFAULT 'pendiente',
                    prioridad TEXT DEFAULT 'medium',
                    analista TEXT,
                    comentarios TEXT,
                    fecha_creada DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_atendida DATETIME,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (hallazgo_id) REFERENCES hallazgos (id) ON DELETE SET NULL,
                    CONSTRAINT valid_status CHECK (estado IN ('pendiente', 'en-revision', 'resuelto', 'falso-positivo')),
                    CONSTRAINT valid_priority CHECK (prioridad IN ('low', 'medium', 'high', 'critical'))
                )
            ''')
            
            # Tabla de usuarios (para el sistema de gestión)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'viewer',
                    activo BOOLEAN DEFAULT 1,
                    verificado BOOLEAN DEFAULT 0,
                    ultimo_login DATETIME,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    CONSTRAINT valid_role CHECK (rol IN ('admin', 'analyst', 'operator', 'viewer', 'auditor'))
                )
            ''')
            
            # Tabla de sesiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sesiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_expiracion DATETIME NOT NULL,
                    activa BOOLEAN DEFAULT 1,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de logs de auditoría
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    accion TEXT NOT NULL,
                    recurso TEXT,
                    recurso_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    exitoso BOOLEAN DEFAULT 1,
                    detalles TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
                )
            ''')
            
            # Tabla de configuración del sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    tipo TEXT DEFAULT 'string',
                    descripcion TEXT,
                    fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT valid_type CHECK (tipo IN ('string', 'integer', 'float', 'boolean', 'json'))
                )
            ''')
            
            # Tabla de estadísticas del sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estadisticas_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    total_hallazgos INTEGER DEFAULT 0,
                    hallazgos_criticos INTEGER DEFAULT 0,
                    dominios_escaneados INTEGER DEFAULT 0,
                    alertas_generadas INTEGER DEFAULT 0,
                    tiempo_escaneo_promedio REAL DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    UNIQUE(fecha)
                )
            ''')
            
            conn.commit()
            self.logger.info("Database schema initialized successfully")
    
    # =============================================================================
    # OPERACIONES CON DOMINIOS
    # =============================================================================
    
    def add_domain(self, domain: str, protocol: str = "https", 
                   port: Optional[int] = None, active: bool = True) -> int:
        """Agregar nuevo dominio"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO dominios (dominio, protocolo, puerto, activo)
                    VALUES (?, ?, ?, ?)
                ''', (domain, protocol, port, active))
                
                domain_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Domain added: {domain} (ID: {domain_id})")
                return domain_id
                
            except sqlite3.IntegrityError:
                raise DatabaseIntegrityError(f"Domain {domain} already exists")
    
    def get_domains(self, active_only: bool = True) -> List[DomainRecord]:
        """Obtener lista de dominios"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM dominios"
            params = []
            
            if active_only:
                query += " WHERE activo = ?"
                params.append(1)
            
            query += " ORDER BY fecha_agregado DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            domains = []
            for row in rows:
                domain = DomainRecord(
                    id=row['id'],
                    domain=row['dominio'],
                    protocol=row['protocolo'],
                    port=row['puerto'],
                    active=bool(row['activo']),
                    added_at=datetime.fromisoformat(row['fecha_agregado']) if row['fecha_agregado'] else None,
                    last_scan=datetime.fromisoformat(row['ultimo_escaneo']) if row['ultimo_escaneo'] else None
                )
                domains.append(domain)
            
            return domains
    
    def update_domain_last_scan(self, domain_id: int):
        """Actualizar última fecha de escaneo de dominio"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE dominios 
                SET ultimo_escaneo = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (domain_id,))
            conn.commit()
    
    def get_domain_by_name(self, domain_name: str) -> Optional[DomainRecord]:
        """Obtener dominio por nombre"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dominios WHERE dominio = ?", (domain_name,))
            row = cursor.fetchone()
            
            if row:
                return DomainRecord(
                    id=row['id'],
                    domain=row['dominio'],
                    protocol=row['protocolo'],
                    port=row['puerto'],
                    active=bool(row['activo']),
                    added_at=datetime.fromisoformat(row['fecha_agregado']) if row['fecha_agregado'] else None,
                    last_scan=datetime.fromisoformat(row['ultimo_escaneo']) if row['ultimo_escaneo'] else None
                )
            return None
    
    # =============================================================================
    # OPERACIONES CON HALLAZGOS
    # =============================================================================
    
    def save_findings(self, domain_id: int, findings: List[Dict[str, Any]]) -> int:
        """Guardar múltiples hallazgos"""
        
        if not findings:
            return 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            saved_count = 0
            for finding in findings:
                try:
                    cursor.execute('''
                        INSERT INTO hallazgos 
                        (dominio_id, url_completa, ruta, codigo_http, es_critico, 
                         tamano_respuesta, herramienta, contenido_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        domain_id,
                        finding.get('url', ''),
                        finding.get('path', ''),
                        finding.get('status_code', 0),
                        finding.get('is_critical', False),
                        finding.get('content_length', 0),
                        finding.get('tool', 'internal'),
                        finding.get('content_hash', '')
                    ))
                    
                    # Crear alerta si es crítico
                    if finding.get('is_critical', False):
                        finding_id = cursor.lastrowid
                        self._create_critical_alert(cursor, finding_id, finding)
                    
                    saved_count += 1
                    
                except sqlite3.IntegrityError as e:
                    self.logger.warning(f"Duplicate finding skipped: {finding.get('url', 'unknown')}")
                    continue
            
            conn.commit()
            self.logger.info(f"Saved {saved_count} findings for domain {domain_id}")
            return saved_count
    
    def _create_critical_alert(self, cursor, finding_id: int, finding: Dict[str, Any]):
        """Crear alerta crítica para un hallazgo"""
        
        path = finding.get('path', '')
        status_code = finding.get('status_code', 0)
        
        message = f"Critical path discovered: {path} (HTTP {status_code})"
        
        cursor.execute('''
            INSERT INTO alertas (hallazgo_id, tipo_alerta, mensaje, prioridad)
            VALUES (?, ?, ?, ?)
        ''', (finding_id, 'critica', message, 'critical'))
    
    def get_findings(self, domain_id: Optional[int] = None, 
                    critical_only: bool = False,
                    date_from: Optional[datetime] = None,
                    date_to: Optional[datetime] = None,
                    limit: int = 1000) -> List[Dict[str, Any]]:
        """Obtener hallazgos con filtros"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT h.*, d.dominio 
                FROM hallazgos h
                JOIN dominios d ON h.dominio_id = d.id
                WHERE 1=1
            '''
            params = []
            
            if domain_id:
                query += " AND h.dominio_id = ?"
                params.append(domain_id)
            
            if critical_only:
                query += " AND h.es_critico = 1"
            
            if date_from:
                query += " AND h.fecha_descubierto >= ?"
                params.append(date_from.isoformat())
            
            if date_to:
                query += " AND h.fecha_descubierto <= ?"
                params.append(date_to.isoformat())
            
            query += " ORDER BY h.fecha_descubierto DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            findings = []
            for row in rows:
                finding = {
                    'id': row['id'],
                    'domain_id': row['dominio_id'],
                    'domain': row['dominio'],
                    'url': row['url_completa'],
                    'path': row['ruta'],
                    'status_code': row['codigo_http'],
                    'is_critical': bool(row['es_critico']),
                    'discovered_at': row['fecha_descubierto'],
                    'response_size': row['tamano_respuesta'],
                    'tool': row['herramienta']
                }
                findings.append(finding)
            
            return findings
    
    # =============================================================================
    # OPERACIONES CON ALERTAS
    # =============================================================================
    
    def get_alerts(self, status: Optional[str] = None, 
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener alertas"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT a.*, h.url_completa, h.ruta, h.codigo_http, d.dominio
                FROM alertas a
                LEFT JOIN hallazgos h ON a.hallazgo_id = h.id
                LEFT JOIN dominios d ON h.dominio_id = d.id
            '''
            params = []
            
            if status:
                query += " WHERE a.estado = ?"
                params.append(status)
            
            query += " ORDER BY a.fecha_creada DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_alert(self, alert_id: int, status: str, analyst: str, 
                     comments: Optional[str] = None) -> bool:
        """Actualizar estado de alerta"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            attended_at = datetime.now().isoformat() if status != 'pendiente' else None
            
            cursor.execute('''
                UPDATE alertas 
                SET estado = ?, analista = ?, comentarios = ?, fecha_atendida = ?
                WHERE id = ?
            ''', (status, analyst, comments, attended_at, alert_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    # =============================================================================
    # ESTADÍSTICAS Y MÉTRICAS
    # =============================================================================
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Alertas pendientes
            cursor.execute("SELECT COUNT(*) FROM alertas WHERE estado = 'pendiente'")
            stats['pending_alerts'] = cursor.fetchone()[0]
            
            # Hallazgos críticos últimas 24h
            cursor.execute('''
                SELECT COUNT(*) FROM hallazgos 
                WHERE es_critico = 1 AND fecha_descubierto > datetime('now', '-1 day')
            ''')
            stats['critical_24h'] = cursor.fetchone()[0]
            
            # Dominios activos
            cursor.execute("SELECT COUNT(*) FROM dominios WHERE activo = 1")
            stats['active_domains'] = cursor.fetchone()[0]
            
            # Total de hallazgos
            cursor.execute("SELECT COUNT(*) FROM hallazgos")
            stats['total_findings'] = cursor.fetchone()[0]
            
            # Estadísticas por dominio
            cursor.execute('''
                SELECT d.dominio, COUNT(h.id) as total_findings,
                       SUM(CASE WHEN h.es_critico = 1 THEN 1 ELSE 0 END) as critical_findings
                FROM dominios d
                LEFT JOIN hallazgos h ON d.id = h.dominio_id
                WHERE d.activo = 1
                GROUP BY d.id, d.dominio
                HAVING total_findings > 0
                ORDER BY total_findings DESC
                LIMIT 10
            ''')
            stats['top_domains'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def record_daily_stats(self):
        """Registrar estadísticas diarias"""
        
        today = datetime.now().date()
        stats = self.get_system_stats()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO estadisticas_sistema 
                (fecha, total_hallazgos, hallazgos_criticos, dominios_escaneados, alertas_generadas)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                today.isoformat(),
                stats['total_findings'],
                stats['critical_24h'], 
                stats['active_domains'],
                stats['pending_alerts']
            ))
            
            conn.commit()
    
    # =============================================================================
    # UTILIDADES Y MANTENIMIENTO
    # =============================================================================
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Limpiar datos antiguos"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Limpiar hallazgos antiguos no críticos
            cursor.execute('''
                DELETE FROM hallazgos 
                WHERE fecha_descubierto < ? AND es_critico = 0
            ''', (cutoff_date.isoformat(),))
            
            cleaned_findings = cursor.rowcount
            
            # Limpiar sesiones expiradas
            cursor.execute('''
                DELETE FROM sesiones 
                WHERE fecha_expiracion < CURRENT_TIMESTAMP
            ''', )
            
            cleaned_sessions = cursor.rowcount
            
            conn.commit()
            
            self.logger.info(f"Cleaned {cleaned_findings} old findings and {cleaned_sessions} expired sessions")
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Crear backup de la base de datos"""
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"backup_fuzzing_{timestamp}.db"
        
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as source:
            backup = sqlite3.connect(backup_path)
            source.backup(backup)
            backup.close()
        
        self.logger.info(f"Database backup created: {backup_path}")
        return str(backup_path)
    
    def vacuum_database(self):
        """Optimizar base de datos"""
        
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
        
        self.logger.info("Database vacuum completed")


# Instancia global del gestor de base de datos
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Obtener instancia global del gestor de base de datos"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database():
    """Inicializar base de datos global"""
    get_db_manager()