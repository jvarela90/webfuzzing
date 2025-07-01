# integrations/dirsearch_integration.py
"""
Integración con Dirsearch para fuzzing de directorios
"""

import os
import subprocess
import json
import tempfile
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import time

class DirsearchIntegration:
    """Integración con la herramienta Dirsearch"""
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializar integración de Dirsearch"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuración de Dirsearch
        self.dirsearch_path = self.config.get('dirsearch.path', 'dirsearch')
        self.default_wordlist = self.config.get('dirsearch.wordlist', 'data/wordlists/common.txt')
        self.default_extensions = self.config.get('dirsearch.extensions', ['php', 'html', 'js', 'txt', 'asp', 'aspx'])
        self.default_threads = self.config.get('dirsearch.threads', 30)
        self.default_timeout = self.config.get('dirsearch.timeout', 30)
        
        # Verificar si Dirsearch está disponible
        self.is_available = self._check_dirsearch_availability()
    
    def _check_dirsearch_availability(self) -> bool:
        """Verificar si Dirsearch está disponible"""
        try:
            # Intentar ejecutar dirsearch --help
            result = subprocess.run([
                self.dirsearch_path, '--help'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info("Dirsearch encontrado y disponible")
                return True
            else:
                self.logger.warning("Dirsearch no disponible")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.warning(f"Dirsearch no disponible: {e}")
            return False
    
    def scan_directory(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecutar escaneo de directorios con Dirsearch
        
        Args:
            url: URL objetivo
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con resultados del escaneo
        """
        if not self.is_available:
            raise RuntimeError("Dirsearch no está disponible")
        
        # Configurar parámetros del escaneo
        wordlist = kwargs.get('wordlist', self.default_wordlist)
        extensions = kwargs.get('extensions', self.default_extensions)
        threads = kwargs.get('threads', self.default_threads)
        timeout = kwargs.get('timeout', self.default_timeout)
        exclude_status = kwargs.get('exclude_status', [404, 403])
        include_status = kwargs.get('include_status', [200, 204, 301, 302, 307, 401, 500])
        
        # Crear archivo temporal para resultados
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Construir comando de Dirsearch
            cmd = [
                self.dirsearch_path,
                '-u', url,
                '-w', wordlist,
                '-t', str(threads),
                '--timeout', str(timeout),
                '--format', 'json',
                '-o', output_file
            ]
            
            # Agregar extensiones
            if extensions:
                cmd.extend(['-e', ','.join(extensions)])
            
            # Agregar códigos de estado a excluir
            if exclude_status:
                cmd.extend(['--exclude-status', ','.join(map(str, exclude_status))])
            
            # Agregar códigos de estado a incluir
            if include_status:
                cmd.extend(['--include-status', ','.join(map(str, include_status))])
            
            # Headers personalizados
            headers = kwargs.get('headers', {})
            for key, value in headers.items():
                cmd.extend(['-H', f"{key}: {value}"])
            
            # User-Agent
            user_agent = kwargs.get('user_agent', 'WebFuzzing-Pro/1.0')
            cmd.extend(['--user-agent', user_agent])
            
            # Proxy
            proxy = kwargs.get('proxy')
            if proxy:
                cmd.extend(['--proxy', proxy])
            
            # Ejecutar comando
            self.logger.info(f"Ejecutando Dirsearch en: {url}")
            self.logger.debug(f"Comando: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get('max_time', 3600)  # 1 hora máximo
            )
            
            execution_time = time.time() - start_time
            
            # Procesar resultados
            findings = self._parse_dirsearch_output(output_file)
            
            return {
                'success': result.returncode == 0,
                'url': url,
                'execution_time': execution_time,
                'findings': findings,
                'total_found': len(findings),
                'command_output': result.stdout,
                'error_output': result.stderr if result.stderr else None,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout en escaneo de {url}")
            return {
                'success': False,
                'url': url,
                'error': 'Timeout durante el escaneo',
                'findings': []
            }
            
        except Exception as e:
            self.logger.error(f"Error ejecutando Dirsearch: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'findings': []
            }
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(output_file)
            except:
                pass
    
    def _parse_dirsearch_output(self, output_file: str) -> List[Dict[str, Any]]:
        """Parsear salida de Dirsearch"""
        findings = []
        
        try:
            if not os.path.exists(output_file):
                self.logger.warning(f"Archivo de salida no encontrado: {output_file}")
                return findings
            
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                if not content:
                    self.logger.warning("Archivo de salida vacío")
                    return findings
                
                # Dirsearch puede generar múltiples líneas JSON
                for line in content.split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            
                            # Extraer información relevante
                            finding = {
                                'path': data.get('path', ''),
                                'full_url': data.get('url', ''),
                                'status_code': data.get('status', 0),
                                'content_length': data.get('content-length', 0),
                                'content_type': data.get('content-type', ''),
                                'response_time': data.get('response-time', 0),
                                'redirect_url': data.get('redirect', ''),
                                'method': 'GET',
                                'is_critical': self._is_critical_finding(data)
                            }
                            
                            findings.append(finding)
                            
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Error parseando línea JSON: {e}")
                            continue
                            
        except Exception as e:
            self.logger.error(f"Error parseando salida de Dirsearch: {e}")
        
        return findings
    
    def _is_critical_finding(self, data: Dict[str, Any]) -> bool:
        """Determinar si un hallazgo es crítico"""
        path = data.get('path', '').lower()
        status_code = data.get('status', 0)
        
        # Rutas críticas comunes
        critical_paths = [
            'admin', 'administrator', 'wp-admin', 'phpmyadmin',
            'config', 'backup', 'database', 'db', 'sql',
            'test', 'staging', 'dev', 'debug',
            '.env', '.git', '.htaccess', 'web.config',
            'api', 'v1', 'v2', 'swagger',
            'login', 'signin', 'auth'
        ]
        
        # Extensiones críticas
        critical_extensions = [
            '.sql', '.bak', '.backup', '.old', '.config',
            '.env', '.key', '.pem', '.p12', '.pfx'
        ]
        
        # Verificar rutas críticas
        for critical_path in critical_paths:
            if critical_path in path:
                return True
        
        # Verificar extensiones críticas
        for ext in critical_extensions:
            if path.endswith(ext):
                return True
        
        # Códigos de estado críticos
        if status_code in [200, 301, 302, 500]:
            # Verificar contenido sensible en la ruta
            sensitive_terms = ['password', 'secret', 'key', 'token', 'private']
            for term in sensitive_terms:
                if term in path:
                    return True
        
        return False
    
    def scan_multiple_domains(self, domains: List[str], **kwargs) -> Dict[str, Any]:
        """Escanear múltiples dominios"""
        results = {}
        
        for domain in domains:
            try:
                result = self.scan_directory(domain, **kwargs)
                results[domain] = result
                
                # Pausa entre escaneos para evitar sobrecarga
                delay = kwargs.get('delay_between_scans', 5)
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Error escaneando {domain}: {e}")
                results[domain] = {
                    'success': False,
                    'error': str(e),
                    'findings': []
                }
        
        return results
    
    def get_wordlists(self) -> List[str]:
        """Obtener lista de wordlists disponibles"""
        wordlists = []
        
        # Directorios comunes de wordlists
        wordlist_dirs = [
            'data/wordlists',
            '/usr/share/wordlists',
            '/usr/share/seclists',
            '/opt/SecLists'
        ]
        
        for directory in wordlist_dirs:
            if os.path.exists(directory):
                for file_path in Path(directory).rglob('*.txt'):
                    wordlists.append(str(file_path))
        
        return sorted(wordlists)
    
    def validate_wordlist(self, wordlist_path: str) -> Dict[str, Any]:
        """Validar wordlist"""
        info = {
            'exists': False,
            'readable': False,
            'line_count': 0,
            'file_size': 0,
            'sample_words': []
        }
        
        try:
            if os.path.exists(wordlist_path):
                info['exists'] = True
                info['file_size'] = os.path.getsize(wordlist_path)
                
                if os.access(wordlist_path, os.R_OK):
                    info['readable'] = True
                    
                    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        info['line_count'] = len(lines)
                        
                        # Obtener muestra de palabras
                        sample_size = min(10, len(lines))
                        info['sample_words'] = [
                            line.strip() for line in lines[:sample_size]
                        ]
                        
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def create_custom_wordlist(self, words: List[str], output_path: str) -> bool:
        """Crear wordlist personalizada"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for word in words:
                    f.write(f"{word.strip()}\n")
            
            self.logger.info(f"Wordlist creada: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando wordlist: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado de la integración"""
        return {
            'name': 'Dirsearch',
            'available': self.is_available,
            'path': self.dirsearch_path,
            'default_wordlist': self.default_wordlist,
            'default_extensions': self.default_extensions,
            'wordlists_available': len(self.get_wordlists())
        }