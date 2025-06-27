# integrations/dirsearch_integration.py
import subprocess
import tempfile
import re
from pathlib import Path
from typing import List, Dict
from utils.logger import get_logger

class DirsearchIntegration:
    """Integración con dirsearch"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.dirsearch_path = config.get('tools.dirsearch.path', 'python3 -m dirsearch')
        self.default_options = config.get('tools.dirsearch.default_options', [])
    
    def scan_domain(self, base_url: str, paths: List[str]) -> List[Dict]:
        """Ejecutar dirsearch en un dominio"""
        results = []
        
        try:
            # Crear archivo temporal con rutas
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in paths:
                    f.write(path + '\n')
                wordlist_file = f.name
            
            # Crear archivo temporal para resultados
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                output_file = f.name
            
            # Construir comando dirsearch
            cmd = [
                'python3', '-m', 'dirsearch',
                '-u', base_url,
                '-w', wordlist_file,
                '--plain-text-report', output_file
            ] + self.default_options
            
            # Ejecutar dirsearch
            self.logger.info(f"Ejecutando dirsearch en {base_url}")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if process.returncode == 0:
                # Leer y parsear resultados
                try:
                    with open(output_file, 'r') as f:
                        content = f.read()
                    
                    # Parsear salida de dirsearch
                    lines = content.split('\n')
                    for line in lines:
                        # Formato típico: [STATUS] SIZE - URL
                        match = re.match(r'\[(\d+)\]\s+(\d+)\s+-\s+(.+)', line.strip())
                        if match:
                            status_code = int(match.group(1))
                            size = int(match.group(2))
                            url = match.group(3)
                            
                            # Extraer path de la URL
                            path = url.replace(base_url, '').lstrip('/')
                            
                            results.append({
                                'url': url,
                                'path': path,
                                'status_code': status_code,
                                'content_length': size,
                                'content_type': '',
                                'response_time': 0,
                                'is_critical': any(critical in path.lower() 
                                                 for critical in self.config.get('fuzzing.critical_paths'))
                            })
                    
                    self.logger.info(f"dirsearch encontró {len(results)} rutas")
                    
                except Exception as e:
                    self.logger.error(f"Error procesando resultados de dirsearch: {e}")
            else:
                self.logger.error(f"Error ejecutando dirsearch: {process.stderr}")
            
            # Limpiar archivos temporales
            Path(wordlist_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout ejecutando dirsearch")
        except Exception as e:
            self.logger.error(f"Error en integración dirsearch: {e}")
        
        return results