# integrations/ffuf_integration.py
import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import get_logger

class FFUFIntegration:
    """Integración con ffuf para fuzzing rápido"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.ffuf_path = config.get('tools.ffuf.path', 'ffuf')
        self.default_options = config.get('tools.ffuf.default_options', [])
    
    def scan_domain(self, base_url: str, paths: List[str]) -> List[Dict]:
        """Ejecutar ffuf en un dominio"""
        results = []
        
        try:
            # Crear archivo temporal con rutas
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in paths:
                    f.write(path + '\n')
                wordlist_file = f.name
            
            # Crear archivo temporal para resultados
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = f.name
            
            # Construir comando ffuf
            cmd = [
                self.ffuf_path,
                '-w', wordlist_file,
                '-u', f"{base_url}/FUZZ",
                '-o', output_file,
                '-of', 'json'
            ] + self.default_options
            
            # Ejecutar ffuf
            self.logger.info(f"Ejecutando ffuf en {base_url}")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if process.returncode == 0:
                # Leer resultados
                try:
                    with open(output_file, 'r') as f:
                        ffuf_data = json.load(f)
                    
                    for result in ffuf_data.get('results', []):
                        results.append({
                            'url': result['url'],
                            'path': result['input']['FUZZ'],
                            'status_code': result['status'],
                            'content_length': result['length'],
                            'content_type': '',
                            'response_time': result['duration'] / 1000,  # Convertir a segundos
                            'is_critical': any(critical in result['input']['FUZZ'].lower() 
                                             for critical in self.config.get('fuzzing.critical_paths'))
                        })
                        
                    self.logger.info(f"ffuf encontró {len(results)} rutas")
                    
                except Exception as e:
                    self.logger.error(f"Error procesando resultados de ffuf: {e}")
            else:
                self.logger.error(f"Error ejecutando ffuf: {process.stderr}")
            
            # Limpiar archivos temporales
            Path(wordlist_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout ejecutando ffuf")
        except Exception as e:
            self.logger.error(f"Error en integración ffuf: {e}")
        
        return results