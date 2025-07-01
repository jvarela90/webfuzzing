# database/manager.py
"""
Gestor de base de datos para WebFuzzing Pro
Maneja todas las operaciones de base de datos
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from contextlib import contextmanager
import threading
import logging

from .models import (
    Domain, DiscoveredPath, ScanSession, Alert, WordlistEntry, 
    SystemConfig, DatabaseSchema, ScanStatus, AlertSeverity, AlertStatus
)

class DatabaseManager:
    """Gestor principal de base de datos"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Inicializar gestor de base de datos"""
        self.config = config or {}
        self.db_path = self.config.get('database.path', 'webfuzzing.db')
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # Crear directorio de base de datos si no existe
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Inicializar base de datos
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Inicializar esquema de base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Habilitar claves foráneas
                cursor.execute('PRAGMA foreign_keys = ON')
                
                # Crear todas las tablas e índices
                DatabaseSchema.create_all_tables(cursor)
                
                # Insertar configuración por defecto
                self._insert_default_config(cursor)
                
                conn.commit()
                self.logger.info("Base de datos inicializada correctamente")
                
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def _insert_default_config(self, cursor: sqlite3.Cursor) -> None:
        """Insertar configuración por defecto"""
        default_configs = [
            ('api.api_key', 'demo-key-change-this', 'api', 'Clave API para autenticación'),
            ('scan.default_wordlist', 'common.txt', 'scan', 'Wordlist por defecto'),
            ('scan.max_concurrent', '10', 'scan', 'Máximo de escaneos concurrentes'),
            ('scan.timeout', '30', 'scan', 'Timeout de requests en segundos'),
            ('scan.user_agent', 'WebFuzzing-Pro/1.0', 'scan', 'User-Agent por defecto'),
            ('notifications.telegram.enabled', 'false', 'notifications', 'Habilitar notificaciones Telegram'),
            ('notifications.email.enabled', 'false', 'notifications', 'Habilitar notificaciones email'),
            ('system.debug', 'false', 'system', 'Modo debug'),
            ('system.version', '1.0.0', 'system', 'Versión del sistema')
        ]
        
        for key, value, category, description in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO system_config (key, value, category, description)
                VALUES (?, ?, ?, ?)
            ''', (key, value, category, description))
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones de base de datos"""
        conn = None
        try:
            with self._lock:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA foreign_keys = ON')
                yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Error en conexión de base de datos: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Tuple = (), fetch: bool = False) -> Union[List[Dict], int]:
        """Ejecutar consulta SQL"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise
    
    # ===========================================
    # MÉTODOS PARA DOMINIOS
    # ===========================================
    
    def add_domain(self, domain: str, port: int = 443, protocol: str = 'https', **kwargs) -> int:
        """Agregar nuevo dominio"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar si el dominio ya existe
                cursor.execute('SELECT id FROM domains WHERE domain = ?', (domain,))
                existing = cursor.fetchone()
                
                if existing:
                    raise ValueError(f"El dominio {domain} ya existe")
                
                # Insertar nuevo dominio
                cursor.execute('''
                    INSERT INTO domains (
                        domain, protocol, port, scan_frequency, 
                        custom_headers, auth_required, auth_token
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    domain, protocol, port,
                    kwargs.get('scan_frequency', 24),
                    kwargs.get('custom_headers'),
                    kwargs.get('auth_required', False),
                    kwargs.get('auth_token')
                ))
                
                domain_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Dominio agregado: {domain} (ID: {domain_id})")
                return domain_id
                
        except Exception as e:
            self.logger.error(f"Error agregando dominio: {e}")
            raise
    
    def get_active_domains(self) -> List[Dict]:
        """Obtener dominios activos"""
        return self.execute_query('''
            SELECT * FROM domains 
            WHERE is_active = 1 
            ORDER BY domain
        ''', fetch=True)
    
    def get_domain_by_id(self, domain_id: int) -> Optional[Dict]:
        """Obtener dominio por ID"""
        results = self.execute_query('''
            SELECT * FROM domains WHERE id = ?
        ''', (domain_id,), fetch=True)
        
        return results[0] if results else None
    
    def update_domain_stats(self, domain_id: int, total_findings: int = None, critical_findings: int = None) -> None:
        """Actualizar estadísticas de dominio"""
        updates = []
        params = []
        
        if total_findings is not None:
            updates.append('total_findings = ?')
            params.append(total_findings)
            
        if critical_findings is not None:
            updates.append('critical_findings = ?')
            params.append(critical_findings)
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(domain_id)
            
            query = f'''
                UPDATE domains 
                SET {', '.join(updates)}
                WHERE id = ?
            '''
            
            self.execute_query(query, tuple(params))
    
    def update_domain_last_scan(self, domain_id: int) -> None:
        """Actualizar timestamp de último escaneo"""
        self.execute_query('''
            UPDATE domains 
            SET last_scan = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (domain_id,))
    
    # ===========================================
    # MÉTODOS PARA RUTAS DESCUBIERTAS
    # ===========================================
    
    def add_discovered_path(self, domain_id: int, path: str, full_url: str, 
                           status_code: int, **kwargs) -> int:
        """Agregar ruta descubierta"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar si la ruta ya existe
                cursor.execute('''
                    SELECT id FROM discovered_paths 
                    WHERE domain_id = ? AND path = ?
                ''', (domain_id, path))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Actualizar ruta existente
                    cursor.execute('''
                        UPDATE discovered_paths 
                        SET status_code = ?, content_length = ?, content_type = ?,
                            response_time = ?, last_checked = CURRENT_TIMESTAMP,
                            method = ?, response_hash = ?, headers = ?
                        WHERE id = ?
                    ''', (
                        status_code,
                        kwargs.get('content_length', 0),
                        kwargs.get('content_type', ''),
                        kwargs.get('response_time', 0.0),
                        kwargs.get('method', 'GET'),
                        kwargs.get('response_hash'),
                        kwargs.get('headers'),
                        existing['id']
                    ))
                    
                    conn.commit()
                    return existing['id']
                else:
                    # Insertar nueva ruta
                    cursor.execute('''
                        INSERT INTO discovered_paths (
                            domain_id, path, full_url, status_code, content_length,
                            content_type, response_time, is_critical, method,
                            response_hash, headers
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        domain_id, path, full_url, status_code,
                        kwargs.get('content_length', 0),
                        kwargs.get('content_type', ''),
                        kwargs.get('response_time', 0.0),
                        kwargs.get('is_critical', False),
                        kwargs.get('method', 'GET'),
                        kwargs.get('response_hash'),
                        kwargs.get('headers')
                    ))
                    
                    path_id = cursor.lastrowid
                    conn.commit()
                    
                    self.logger.info(f"Ruta descubierta: {full_url} (ID: {path_id})")
                    return path_id
                    
        except Exception as e:
            self.logger.error(f"Error agregando ruta descubierta: {e}")
            raise
    
    def get_recent_findings(self, hours: int = 24) -> List[Dict]:
        """Obtener hallazgos recientes"""
        return self.execute_query('''
            SELECT dp.*, d.domain
            FROM discovered_paths dp
            JOIN domains d ON dp.domain_id = d.id
            WHERE dp.discovered_at >= datetime('now', '-{} hours')
            ORDER BY dp.discovered_at DESC
            LIMIT 1000
        '''.format(hours), fetch=True)
    
    def get_critical_findings(self) -> List[Dict]:
        """Obtener hallazgos críticos"""
        return self.execute_query('''
            SELECT dp.*, d.domain
            FROM discovered_paths dp
            JOIN domains d ON dp.domain_id = d.id
            WHERE dp.is_critical = 1
            ORDER BY dp.discovered_at DESC
            LIMIT 500
        ''', fetch=True)
    
    def get_findings_by_domain(self, domain_id: int, limit: int = 100) -> List[Dict]:
        """Obtener hallazgos por dominio"""
        return self.execute_query('''
            SELECT * FROM discovered_paths
            WHERE domain_id = ?
            ORDER BY discovered_at DESC
            LIMIT ?
        ''', (domain_id, limit), fetch=True)
    
    # ===========================================
    # MÉTODOS PARA SESIONES DE ESCANEO
    # ===========================================
    
    def create_scan_session(self, domain_id: int, scan_type: str = 'full', **kwargs) -> int:
        """Crear sesión de escaneo"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO scan_sessions (
                        domain_id, scan_type, wordlist_used, config_used
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    domain_id, scan_type,
                    kwargs.get('wordlist_used'),
                    kwargs.get('config_used')
                ))
                
                session_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Sesión de escaneo creada: {session_id}")
                return session_id
                
        except Exception as e:
            self.logger.error(f"Error creando sesión de escaneo: {e}")
            raise
    
    def update_scan_session(self, session_id: int, **kwargs) -> None:
        """Actualizar sesión de escaneo"""
        updates = []
        params = []
        
        for field in ['status', 'total_requests', 'successful_requests', 
                     'failed_requests', 'paths_found', 'critical_found', 'error_message']:
            if field in kwargs:
                updates.append(f'{field} = ?')
                params.append(kwargs[field])
        
        if 'finished' in kwargs and kwargs['finished']:
            updates.append('finished_at = CURRENT_TIMESTAMP')
        
        if updates:
            params.append(session_id)
            query = f'''
                UPDATE scan_sessions 
                SET {', '.join(updates)}
                WHERE id = ?
            '''
            self.execute_query(query, tuple(params))
    
    def get_active_scan_sessions(self) -> List[Dict]:
        """Obtener sesiones de escaneo activas"""
        return self.execute_query('''
            SELECT ss.*, d.domain
            FROM scan_sessions ss
            JOIN domains d ON ss.domain_id = d.id
            WHERE ss.status IN ('pending', 'running')
            ORDER BY ss.started_at DESC
        ''', fetch=True)
    
    # ===========================================
    # MÉTODOS PARA ALERTAS
    # ===========================================
    
    def create_alert(self, alert_type: str, severity: str, title: str, 
                    message: str, url: Optional[str] = None, **kwargs) -> int:
        """Crear nueva alerta"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO alerts (
                        domain_id, path_id, alert_type, severity, title, 
                        message, url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    kwargs.get('domain_id'),
                    kwargs.get('path_id'),
                    alert_type, severity, title, message, url
                ))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Alerta creada: {title} (ID: {alert_id})")
                return alert_id
                
        except Exception as e:
            self.logger.error(f"Error creando alerta: {e}")
            raise
    
    def get_alerts(self, status: str = 'all', limit: int = 100) -> List[Dict]:
        """Obtener alertas"""
        if status == 'all':
            query = '''
                SELECT a.*, d.domain
                FROM alerts a
                LEFT JOIN domains d ON a.domain_id = d.id
                ORDER BY a.created_at DESC
                LIMIT ?
            '''
            params = (limit,)
        else:
            query = '''
                SELECT a.*, d.domain
                FROM alerts a
                LEFT JOIN domains d ON a.domain_id = d.id
                WHERE a.status = ?
                ORDER BY a.created_at DESC
                LIMIT ?
            '''
            params = (status, limit)
        
        return self.execute_query(query, params, fetch=True)
    
    def update_alert_status(self, alert_id: int, status: str, notes: Optional[str] = None) -> None:
        """Actualizar estado de alerta"""
        params = [status]
        updates = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        
        if notes:
            updates.append('analyst_notes = ?')
            params.append(notes)
        
        if status == 'resolved':
            updates.append('resolved_at = CURRENT_TIMESTAMP')
        
        params.append(alert_id)
        
        query = f'''
            UPDATE alerts 
            SET {', '.join(updates)}
            WHERE id = ?
        '''
        
        self.execute_query(query, tuple(params))
    
    # ===========================================
    # MÉTODOS PARA WORDLISTS
    # ===========================================
    
    def add_wordlist_entries(self, wordlist_name: str, words: List[str], 
                           category: str = 'general') -> int:
        """Agregar entradas a wordlist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                added_count = 0
                
                for word in words:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO wordlist_entries 
                            (wordlist_name, word, category) 
                            VALUES (?, ?, ?)
                        ''', (wordlist_name, word.strip(), category))
                        
                        if cursor.rowcount > 0:
                            added_count += 1
                            
                    except Exception as e:
                        self.logger.warning(f"Error agregando palabra '{word}': {e}")
                        continue
                
                conn.commit()
                self.logger.info(f"Agregadas {added_count} palabras a {wordlist_name}")
                return added_count
                
        except Exception as e:
            self.logger.error(f"Error agregando wordlist: {e}")
            raise
    
    def get_wordlist(self, wordlist_name: str, active_only: bool = True) -> List[str]:
        """Obtener palabras de wordlist"""
        query = 'SELECT word FROM wordlist_entries WHERE wordlist_name = ?'
        params = [wordlist_name]
        
        if active_only:
            query += ' AND is_active = 1'
        
        query += ' ORDER BY priority DESC, success_rate DESC'
        
        results = self.execute_query(query, tuple(params), fetch=True)
        return [row['word'] for row in results]
    
    # ===========================================
    # MÉTODOS PARA CONFIGURACIÓN
    # ===========================================
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración"""
        results = self.execute_query('''
            SELECT value FROM system_config WHERE key = ?
        ''', (key,), fetch=True)
        
        if results:
            value = results[0]['value']
            # Intentar convertir tipos básicos
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            elif value.isdigit():
                return int(value)
            else:
                try:
                    return float(value)
                except ValueError:
                    return value
        
        return default
    
    def set_config(self, key: str, value: Any, category: str = 'general', 
                  description: str = None) -> None:
        """Establecer valor de configuración"""
        # Convertir valor a string
        str_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_config 
                (key, value, category, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, str_value, category, description))
            
            conn.commit()
    
    def get_all_config(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Obtener toda la configuración"""
        if category:
            results = self.execute_query('''
                SELECT key, value FROM system_config WHERE category = ?
            ''', (category,), fetch=True)
        else:
            results = self.execute_query('''
                SELECT key, value FROM system_config
            ''', fetch=True)
        
        config = {}
        for row in results:
            key = row['key']
            value = row['value']
            
            # Conversión de tipos
            if value.lower() in ('true', 'false'):
                config[key] = value.lower() == 'true'
            elif value.isdigit():
                config[key] = int(value)
            else:
                try:
                    config[key] = float(value)
                except ValueError:
                    config[key] = value
        
        return config
    
    # ===========================================
    # MÉTODOS DE ESTADÍSTICAS
    # ===========================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas generales"""
        stats = {}
        
        # Contar dominios activos
        result = self.execute_query('''
            SELECT COUNT(*) as count FROM domains WHERE is_active = 1
        ''', fetch=True)
        stats['total_domains'] = result[0]['count']
        
        # Contar hallazgos recientes (24h)
        result = self.execute_query('''
            SELECT COUNT(*) as count FROM discovered_paths 
            WHERE discovered_at >= datetime('now', '-24 hours')
        ''', fetch=True)
        stats['recent_findings'] = result[0]['count']
        
        # Contar hallazgos críticos
        result = self.execute_query('''
            SELECT COUNT(*) as count FROM discovered_paths WHERE is_critical = 1
        ''', fetch=True)
        stats['critical_findings'] = result[0]['count']
        
        # Contar alertas nuevas
        result = self.execute_query('''
            SELECT COUNT(*) as count FROM alerts WHERE status = 'new'
        ''', fetch=True)
        stats['new_alerts'] = result[0]['count']
        
        # Contar sesiones activas
        result = self.execute_query('''
            SELECT COUNT(*) as count FROM scan_sessions 
            WHERE status IN ('pending', 'running')
        ''', fetch=True)
        stats['active_scans'] = result[0]['count']
        
        return stats
    
    # ===========================================
    # MÉTODOS DE MANTENIMIENTO
    # ===========================================
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Limpiar datos antiguos"""
        results = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Limpiar sesiones de escaneo antiguas
                cursor.execute('''
                    DELETE FROM scan_sessions 
                    WHERE finished_at < datetime('now', '-{} days')
                    AND status = 'completed'
                '''.format(days))
                results['scan_sessions'] = cursor.rowcount
                
                # Limpiar alertas resueltas antiguas
                cursor.execute('''
                    DELETE FROM alerts 
                    WHERE resolved_at < datetime('now', '-{} days')
                    AND status = 'resolved'
                '''.format(days))
                results['alerts'] = cursor.rowcount
                
                # Limpiar rutas no críticas antiguas
                cursor.execute('''
                    DELETE FROM discovered_paths 
                    WHERE last_checked < datetime('now', '-{} days')
                    AND is_critical = 0
                '''.format(days * 2))  # Mantener rutas no críticas por más tiempo
                results['paths'] = cursor.rowcount
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error en limpieza de datos: {e}")
            raise
        
        return results
    
    def backup_database(self, backup_path: str) -> bool:
        """Crear backup de la base de datos"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Backup creado: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtener información de la base de datos"""
        info = {}
        
        try:
            # Tamaño del archivo
            if os.path.exists(self.db_path):
                info['file_size'] = os.path.getsize(self.db_path)
            
            # Información de tablas
            tables_info = self.execute_query('''
                SELECT name, sql FROM sqlite_master 
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            ''', fetch=True)
            
            info['tables'] = {}
            for table in tables_info:
                table_name = table['name']
                count_result = self.execute_query(f'''
                    SELECT COUNT(*) as count FROM {table_name}
                ''', fetch=True)
                info['tables'][table_name] = count_result[0]['count']
            
            # Versión SQLite
            version_result = self.execute_query('SELECT sqlite_version()', fetch=True)
            info['sqlite_version'] = version_result[0]['sqlite_version()']
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de BD: {e}")
            info['error'] = str(e)
        
        return info
    
    def close(self) -> None:
        """Cerrar conexiones (para cleanup)"""
        self.logger.info("DatabaseManager cerrado")