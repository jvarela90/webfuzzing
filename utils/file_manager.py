# utils/file_manager.py
import os
import shutil
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import zipfile
import tempfile

from utils.logger import get_logger

class FileManager:
    """Gestor de archivos del sistema"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.base_dir = config.base_dir
    
    def ensure_directory(self, path: Path) -> bool:
        """Asegurar que un directorio existe"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error creando directorio {path}: {e}")
            return False
    
    def save_json(self, data: Dict[str, Any], filepath: Path) -> bool:
        """Guardar datos en formato JSON"""
        try:
            self.ensure_directory(filepath.parent)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            return True
        except Exception as e:
            self.logger.error(f"Error guardando JSON {filepath}: {e}")
            return False
    
    def load_json(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Cargar datos desde archivo JSON"""
        try:
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            self.logger.error(f"Error cargando JSON {filepath}: {e}")
            return None
    
    def save_csv(self, data: List[Dict[str, Any]], filepath: Path, 
                 fieldnames: List[str] = None) -> bool:
        """Guardar datos en formato CSV"""
        try:
            if not data:
                return False
            
            self.ensure_directory(filepath.parent)
            
            # Determinar campos si no se proporcionan
            if not fieldnames:
                fieldnames = list(data[0].keys())
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            return True
        except Exception as e:
            self.logger.error(f"Error guardando CSV {filepath}: {e}")
            return False
    
    def load_csv(self, filepath: Path) -> List[Dict[str, Any]]:
        """Cargar datos desde archivo CSV"""
        data = []
        try:
            if not filepath.exists():
                return data
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        
        except Exception as e:
            self.logger.error(f"Error cargando CSV {filepath}: {e}")
        
        return data
    
    def backup_file(self, filepath: Path, backup_dir: Path = None) -> Optional[Path]:
        """Crear backup de un archivo"""
        try:
            if not filepath.exists():
                return None
            
            # Determinar directorio de backup
            if not backup_dir:
                backup_dir = self.base_dir / self.config.get('files.backup_dir')
            
            self.ensure_directory(backup_dir)
            
            # Generar nombre de backup con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_path = backup_dir / backup_name
            
            # Copiar archivo
            shutil.copy2(str(filepath), str(backup_path))
            
            self.logger.info(f"Backup creado: {backup_path}")
            return backup_path
        
        except Exception as e:
            self.logger.error(f"Error creando backup de {filepath}: {e}")
            return None
    
    def cleanup_old_files(self, directory: Path, days_old: int = 30, 
                         pattern: str = "*") -> int:
        """Limpiar archivos antiguos de un directorio"""
        cleaned_count = 0
        
        try:
            if not directory.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    file_time = file_path.stat().st_mtime
                    
                    if file_time < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                        self.logger.debug(f"Archivo eliminado: {file_path}")
            
            if cleaned_count > 0:
                self.logger.info(f"Limpieza completada: {cleaned_count} archivos eliminados de {directory}")
        
        except Exception as e:
            self.logger.error(f"Error en limpieza de {directory}: {e}")
        
        return cleaned_count
    
    def create_archive(self, source_dir: Path, archive_path: Path) -> bool:
        """Crear archivo ZIP de un directorio"""
        try:
            self.ensure_directory(archive_path.parent)
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        # Ruta relativa dentro del ZIP
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
            
            self.logger.info(f"Archivo creado: {archive_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error creando archivo {archive_path}: {e}")
            return False
    
    def get_directory_size(self, directory: Path) -> int:
        """Obtener tamaño total de un directorio en bytes"""
        total_size = 0
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.error(f"Error calculando tamaño de {directory}: {e}")
        
        return total_size
    
    def format_file_size(self, size_bytes: int) -> str:
        """Formatear tamaño de archivo en formato legible"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtener información del sistema de archivos"""
        info = {}
        
        try:
            # Información de directorios principales
            directories = {
                'data': self.config.get('files.results_dir'),
                'logs': 'logs',
                'backups': self.config.get('files.backup_dir'),
                'dictionaries': self.config.get('files.dictionaries_dir')
            }
            
            for name, dir_path in directories.items():
                full_path = self.base_dir / dir_path
                if full_path.exists():
                    size = self.get_directory_size(full_path)
                    file_count = len(list(full_path.rglob('*')))
                    
                    info[name] = {
                        'path': str(full_path),
                        'size_bytes': size,
                        'size_formatted': self.format_file_size(size),
                        'file_count': file_count,
                        'exists': True
                    }
                else:
                    info[name] = {
                        'path': str(full_path),
                        'exists': False
                    }
            
            # Espacio libre en disco
            if hasattr(shutil, 'disk_usage'):
                usage = shutil.disk_usage(str(self.base_dir))
                info['disk'] = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'total_formatted': self.format_file_size(usage.total),
                    'used_formatted': self.format_file_size(usage.used),
                    'free_formatted': self.format_file_size(usage.free),
                    'usage_percent': (usage.used / usage.total) * 100
                }
        
        except Exception as e:
            self.logger.error(f"Error obteniendo información del sistema: {e}")
        
        return info