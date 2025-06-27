# scripts/migrate_db.py
#!/usr/bin/env python3
"""
Script de migración de base de datos para WebFuzzing Pro
"""

import sys
import sqlite3
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Config
from utils.logger import get_logger

class DatabaseMigrator:
    """Gestor de migraciones de base de datos"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.db_path = config.base_dir / config.get('database.name')
        
        # Versiones de esquema
        self.migrations = {
            1: self.migration_v1_initial,
            2: self.migration_v2_add_indexes,
            3: self.migration_v3_add_performance_columns,
            4: self.migration_v4_add_scan_metadata
        }
    
    def get_current_version(self) -> int:
        """Obtener versión actual del esquema"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Verificar si existe tabla de versiones
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if not cursor.fetchone():
                # No existe tabla de versiones, crear
                cursor.execute("""
                    CREATE TABLE schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("INSERT INTO schema_version (version) VALUES (0)")
                conn.commit()
                version = 0
            else:
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                version = result[0] if result and result[0] else 0
            
            conn.close()
            return version
            
        except Exception as e:
            self.logger.error(f"Error obteniendo versión del esquema: {e}")
            return 0
    
    def set_version(self, version: int):
        """Establecer versión del esquema"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (version,)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error estableciendo versión {version}: {e}")
            raise e
    
    def migration_v1_initial(self, cursor):
        """Migración inicial - crear tablas base"""
        self.logger.info("Ejecutando migración v1: Esquema inicial")
        
        # Tablas ya creadas por DatabaseManager.__init__
        # Esta migración es principalmente para tracking
        pass
    
    def migration_v2_add_indexes(self, cursor):
        """Migración v2 - agregar índices adicionales"""
        self.logger.info("Ejecutando migración v2: Índices adicionales")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_domains_status ON domains(status)",
            "CREATE INDEX IF NOT EXISTS idx_domains_created ON domains(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_paths_status_code ON discovered_paths(status_code)",
            "CREATE INDEX IF NOT EXISTS idx_paths_content_length ON discovered_paths(content_length)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)",
            "CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)",
            "CREATE INDEX IF NOT EXISTS idx_scans_start_time ON scans(start_time)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def migration_v3_add_performance_columns(self, cursor):
        """Migración v3 - agregar columnas de rendimiento"""
        self.logger.info("Ejecutando migración v3: Columnas de rendimiento")
        
        # Agregar columnas si no existen
        columns_to_add = [
            ("discovered_paths", "response_headers", "TEXT"),
            ("discovered_paths", "redirect_url", "TEXT"),
            ("discovered_paths", "ssl_info", "TEXT"),
            ("domains", "last_response_time", "REAL"),
            ("domains", "avg_response_time", "REAL"),
            ("domains", "total_requests", "INTEGER DEFAULT 0")
        ]
        
        for table, column, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise e
    
    def migration_v4_add_scan_metadata(self, cursor):
        """Migración v4 - agregar metadatos de escaneo"""
        self.logger.info("Ejecutando migración v4: Metadatos de escaneo")
        
        # Crear tabla de metadatos de escaneo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scan_id) REFERENCES scans (id),
                UNIQUE(scan_id, key)
            )
        """)
        
        # Crear tabla de estadísticas de paths
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS path_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                total_found INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para las nuevas tablas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_metadata_scan_id ON scan_metadata(scan_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_stats_path ON path_statistics(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_stats_success_rate ON path_statistics(success_rate)")
    
    def migrate(self) -> bool:
        """Ejecutar migraciones pendientes"""
        try:
            current_version = self.get_current_version()
            latest_version = max(self.migrations.keys())
            
            if current_version >= latest_version:
                self.logger.info("Base de datos actualizada, no se requieren migraciones")
                return True
            
            self.logger.info(f"Migrando desde versión {current_version} a {latest_version}")
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            try:
                # Ejecutar migraciones pendientes
                for version in range(current_version + 1, latest_version + 1):
                    if version in self.migrations:
                        self.logger.info(f"Aplicando migración v{version}")
                        
                        # Ejecutar migración
                        self.migrations[version](cursor)
                        
                        # Actualizar versión
                        cursor.execute(
                            "INSERT INTO schema_version (version) VALUES (?)",
                            (version,)
                        )
                        
                        conn.commit()
                        self.logger.info(f"Migración v{version} completada")
                
                self.logger.info("Todas las migraciones completadas exitosamente")
                return True
                
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Error durante migración: {e}")
                raise e
            
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error en proceso de migración: {e}")
            return False
    
    def backup_database(self) -> str:
        """Crear backup antes de migrar"""
        if not self.db_path.exists():
            return None
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.db_path.parent / f"webfuzzing_backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(str(self.db_path), str(backup_path))
            self.logger.info(f"Backup creado: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return None

def main():
    """Función principal"""
    print("🔄 WebFuzzing Pro - Migrador de Base de Datos")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = Config()
        migrator = DatabaseMigrator(config)
        
        # Mostrar estado actual
        current_version = migrator.get_current_version()
        latest_version = max(migrator.migrations.keys())
        
        print(f"Versión actual: v{current_version}")
        print(f"Versión objetivo: v{latest_version}")
        
        if current_version >= latest_version:
            print("✅ Base de datos actualizada")
            return True
        
        # Crear backup
        print("\n💾 Creando backup...")
        backup_file = migrator.backup_database()
        if backup_file:
            print(f"✅ Backup creado: {backup_file}")
        
        # Ejecutar migraciones
        print(f"\n🔄 Ejecutando migraciones...")
        success = migrator.migrate()
        
        if success:
            print("\n✅ Migraciones completadas exitosamente")
            return True
        else:
            print("\n❌ Error durante las migraciones")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
