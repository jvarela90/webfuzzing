# integrations/ffuf_integration.py
"""
Integración con FFUF (Fast web fuzzer) para fuzzing avanzado
"""

import os
import subprocess
import json
import tempfile
import logging
from typing import Dict, List, Optional, Any
import time

class FFUFIntegration:
    """Integración con la herramienta FFUF"""
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializar integración de FFUF"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuración de FFUF
        self.ffuf_path = self.config.get('ffuf.path', 'ffuf')
        self.default_wordlist = self.config.get('ffuf.wordlist', 'data/wordlists/common.txt')
        self.default_threads = self.config.get('ffuf.threads', 40)
        self.default_timeout = self.config.get('ffuf.timeout', 10)
        self.default_delay = self.config.get('ffuf.delay', '0')
        self.default_rate = self.config.get('ffuf.rate', 0)  # requests per second
        
        # Verificar si FFUF está disponible
        self.is_available = self._check_ffuf_availability()
    
    def _check_ffuf_availability(self) -> bool:
        """Verificar si FFUF está disponible"""
        try:
            # Intentar ejecutar ffuf -h
            result = subprocess.run([
                self.ffuf_path, '-h'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info("FFUF encontrado y disponible")
                return True
            else:
                self.logger.warning("FFUF no disponible")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.warning(f"FFUF no disponible: {e}")
            return False
    
    def fuzz_directories(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Fuzzing de directorios con FFUF
        
        Args:
            url: URL objetivo (debe contener FUZZ como placeholder)
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con resultados del fuzzing
        """
        if not self.is_available:
            raise RuntimeError("FFUF no está disponible")
        
        # Asegurar que la URL contiene FUZZ
        if 'FUZZ' not in url:
            if url.endswith('/'):
                url += 'FUZZ'
            else:
                url += '/FUZZ'
        
        return self._execute_ffuf(url, **kwargs)
    
    def fuzz_files(self, url: str, extensions: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Fuzzing de archivos con extensiones específicas
        
        Args:
            url: URL objetivo
            extensions: Lista de extensiones a probar
            **kwargs: Parámetros adicionales
        """
        if not self.is_available:
            raise RuntimeError("FFUF no está disponible")
        
        if not extensions:
            extensions = ['php', 'html', 'txt', 'js', 'asp', 'aspx', 'jsp']
        
        # Preparar URL con FUZZ
        if 'FUZZ' not in url:
            if url.endswith('/'):
                url += 'FUZZ'
            else:
                url += '/FUZZ'
        
        # Agregar extensiones al comando
        kwargs['extensions'] = extensions
        
        return self._execute_ffuf(url, **kwargs)
    
    def fuzz_parameters(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """
        Fuzzing de parámetros GET/POST
        
        Args:
            url: URL objetivo
            method: Método HTTP (GET/POST)
            **kwargs: Parámetros adicionales
        """
        if not self.is_available:
            raise RuntimeError("FFUF no está disponible")
        
        if method.upper() == 'GET':
            # Fuzzing de parámetros GET
            if '?' not in url:
                url += '?FUZZ=test'
            else:
                url += '&FUZZ=test'
        else:
            # Fuzzing de parámetros POST
            kwargs['method'] = 'POST'
            kwargs['data'] = 'FUZZ=test'
        
        return self._execute_ffuf(url, **kwargs)
    
    def fuzz_subdomains(self, domain: str, **kwargs) -> Dict[str, Any]:
        """
        Fuzzing de subdominios
        
        Args:
            domain: Dominio base (ej: example.com)
            **kwargs: Parámetros adicionales
        """
        if not self.is_available:
            raise RuntimeError("FFUF no está disponible")
        
        # Construir URL para fuzzing de subdominios
        protocol = kwargs.get('protocol', 'https')
        url = f"{protocol}://FUZZ.{domain}"
        
        # Usar wordlist específico para subdominios si está disponible
        if 'wordlist' not in kwargs:
            subdomains_wordlist = self.config.get('ffuf.subdomains_wordlist', 'data/wordlists/subdomains.txt')
            if os.path.exists(subdomains_wordlist):
                kwargs['wordlist'] = subdomains_wordlist
        
        return self._execute_ffuf(url, **kwargs)
    
    def fuzz_virtual_hosts(self, target_ip: str, domain: str, **kwargs) -> Dict[str, Any]:
        """
        Fuzzing de virtual hosts
        
        Args:
            target_ip: IP del servidor objetivo
            domain: Dominio base
            **kwargs: Parámetros adicionales
        """
        if not self.is_available:
            raise RuntimeError("FFUF no está disponible")
        
        # Configurar fuzzing de Host header
        protocol = kwargs.get('protocol', 'http')
        url = f"{protocol}://{target_ip}/"
        
        # Configurar header Host
        headers = kwargs.get('headers', {})
        headers['Host'] = f'FUZZ.{domain}'
        kwargs['headers'] = headers
        
        return self._execute_ffuf(url, **kwargs)
    
    def _execute_ffuf(self, url: str, **kwargs) -> Dict[str, Any]:
        """Ejecutar comando FFUF"""
        
        # Configurar parámetros
        wordlist = kwargs.get('wordlist', self.default_wordlist)
        threads = kwargs.get('threads', self.default_threads)
        timeout = kwargs.get('timeout', self.default_timeout)
        delay = kwargs.get('delay', self.default_delay)
        rate = kwargs.get('rate', self.default_rate)
        
        # Crear archivo temporal para resultados
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Construir comando FFUF
            cmd = [
                self.ffuf_path,
                '-u', url,
                '-w', wordlist,
                '-t', str(threads),
                '-timeout', str(timeout),
                '-o', output_file,
                '-of', 'json'
            ]
            
            # Delay entre requests
            if delay and delay != '0':
                cmd.extend(['-p', str(delay)])
            
            # Rate limiting
            if rate > 0:
                cmd.extend(['-rate', str(rate)])
            
            # Extensiones
            extensions = kwargs.get('extensions')
            if extensions:
                cmd.extend(['-e', ','.join(extensions)])
            
            # Método HTTP
            method = kwargs.get('method')
            if method and method.upper() != 'GET':
                cmd.extend(['-X', method.upper()])
            
            # Datos POST
            data = kwargs.get('data')
            if data:
                cmd.extend(['-d', data])
            
            # Headers personalizados
            headers = kwargs.get('headers', {})
            for key, value in headers.items():
                cmd.extend(['-H', f"{key}: {value}"])
            
            # User-Agent
            user_agent = kwargs.get('user_agent', 'WebFuzzing-Pro/1.0')
            cmd.extend(['-H', f"User-Agent: {user_agent}"])
            
            # Proxy
            proxy = kwargs.get('proxy')
            if proxy:
                cmd.extend(['-x', proxy])
            
            # Filtros por código de estado
            filter_status = kwargs.get('filter_status')
            if filter_status:
                cmd.extend(['-fc', ','.join(map(str, filter_status))])
            
            # Matcher por código de estado
            match_status = kwargs.get('match_status')
            if match_status:
                cmd.extend(['-mc', ','.join(map(str, match_status))])
            
            # Filtros por tamaño
            filter_size = kwargs.get('filter_size')
            if filter_size:
                cmd.extend(['-fs', str(filter_size)])
            
            # Filtros por palabras
            filter_words = kwargs.get('filter_words')
            if filter_words:
                cmd.extend(['-fw', str(filter_words)])
            
            # Filtros por líneas
            filter_lines = kwargs.get('filter_lines')
            if filter_lines:
                cmd.extend(['-fl', str(filter_lines)])
            
            # Modo recursivo
            if kwargs.get('recursive', False):
                recursion_depth = kwargs.get('recursion_depth', 1)
                cmd.extend(['-recursion', '-recursion-depth', str(recursion_depth)])
            
            # Modo silencioso
            if kwargs.get('silent', True):
                cmd.append('-s')
            
            # Tiempo máximo de ejecución
            max_time = kwargs.get('max_time')
            if max_time:
                cmd.extend(['-maxtime', str(max_time)])
            
            # Ejecutar comando
            self.logger.info(f"Ejecutando FFUF en: {url}")
            self.logger.debug(f"Comando: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get('command_timeout', 3600)  # 1 hora máximo
            )
            
            execution_time = time.time() - start_time
            
            # Procesar resultados
            findings = self._parse_ffuf_output(output_file)
            
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
            self.logger.error(f"Timeout en fuzzing de {url}")
            return {
                'success': False,
                'url': url,
                'error': 'Timeout durante el fuzzing',
                'findings': []
            }
            
        except Exception as e:
            self.logger.error(f"Error ejecutando FFUF: {e}")
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
    
    def _parse_ffuf_output(self, output_file: str) -> List[Dict[str, Any]]:
        """Parsear salida de FFUF"""
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
                
                # FFUF genera JSON válido
                data = json.loads(content)
                
                # Extraer resultados
                results = data.get('results', [])
                
                for result in results:
                    finding = {
                        'path': result.get('input', {}).get('FUZZ', ''),
                        'full_url': result.get('url', ''),
                        'status_code': result.get('status', 0),
                        'content_length': result.get('length', 0),
                        'content_type': result.get('content-type', ''),
                        'response_time': result.get('duration', 0) / 1000000,  # ns to ms
                        'method': 'GET',
                        'words': result.get('words', 0),
                        'lines': result.get('lines', 0),
                        'is_critical': self._is_critical_finding(result)
                    }
                    
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando JSON de FFUF: {e}")
        except Exception as e:
            self.logger.error(f"Error parseando salida de FFUF: {e}")
        
        return findings
    
    def _is_critical_finding(self, result: Dict[str, Any]) -> bool:
        """Determinar si un hallazgo es crítico"""
        path = result.get('input', {}).get('FUZZ', '').lower()
        status_code = result.get('status', 0)
        content_length = result.get('length', 0)
        
        # Rutas críticas comunes
        critical_paths = [
            'admin', 'administrator', 'wp-admin', 'phpmyadmin',
            'config', 'backup', 'database', 'db', 'sql',
            'test', 'staging', 'dev', 'debug',
            '.env', '.git', '.htaccess', 'web.config',
            'api', 'v1', 'v2', 'swagger', 'docs',
            'login', 'signin', 'auth', 'panel'
        ]
        
        # Extensiones críticas
        critical_extensions = [
            '.sql', '.bak', '.backup', '.old', '.config',
            '.env', '.key', '.pem', '.p12', '.pfx', '.log'
        ]
        
        # Verificar rutas críticas
        for critical_path in critical_paths:
            if critical_path in path:
                return True
        
        # Verificar extensiones críticas
        for ext in critical_extensions:
            if path.endswith(ext):
                return True
        
        # Códigos de estado críticos con contenido
        if status_code in [200, 500] and content_length > 0:
            sensitive_terms = ['password', 'secret', 'key', 'token', 'private', 'internal']
            for term in sensitive_terms:
                if term in path:
                    return True
        
        # Subdominios críticos
        subdomain_critical = ['admin', 'test', 'dev', 'staging', 'api', 'internal', 'vpn']
        for sub in subdomain_critical:
            if path == sub:
                return True
        
        return False
    
    def auto_calibrate(self, url: str, wordlist: str = None) -> Dict[str, Any]:
        """Auto-calibrar filtros para reducir falsos positivos"""
        if not wordlist:
            wordlist = self.default_wordlist
        
        # Ejecutar un pequeño test para calibrar
        test_url = url.replace('FUZZ', 'nonexistentpath12345')
        
        try:
            result = subprocess.run([
                self.ffuf_path,
                '-u', test_url,
                '-w', wordlist,
                '-ac',  # Auto-calibration
                '-t', '10',
                '-maxtime', '30',
                '-s'  # Silent
            ], capture_output=True, text=True, timeout=60)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado de la integración"""
        status = {
            'name': 'FFUF',
            'available': self.is_available,
            'path': self.ffuf_path,
            'default_wordlist': self.default_wordlist,
            'default_threads': self.default_threads
        }
        
        if self.is_available:
            try:
                # Obtener versión de FFUF
                result = subprocess.run([
                    self.ffuf_path, '-V'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    status['version'] = result.stdout.strip()
                    
            except:
                pass
        
        return status
    
    def generate_report(self, results: Dict[str, Any], output_format: str = 'json') -> str:
        """Generar reporte de resultados"""
        if output_format == 'json':
            return json.dumps(results, indent=2)
        
        elif output_format == 'html':
            # Generar reporte HTML básico
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>FFUF Fuzzing Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .critical { background-color: #ffebee; }
                    .normal { background-color: #f5f5f5; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h1>FFUF Fuzzing Report</h1>
                <p><strong>URL:</strong> {url}</p>
                <p><strong>Total Found:</strong> {total}</p>
                <p><strong>Execution Time:</strong> {time:.2f}s</p>
                
                <table>
                    <tr>
                        <th>Path</th>
                        <th>Status</th>
                        <th>Length</th>
                        <th>Critical</th>
                    </tr>
            """.format(
                url=results.get('url', ''),
                total=results.get('total_found', 0),
                time=results.get('execution_time', 0)
            )
            
            for finding in results.get('findings', []):
                css_class = 'critical' if finding.get('is_critical') else 'normal'
                html += f"""
                    <tr class="{css_class}">
                        <td>{finding.get('path', '')}</td>
                        <td>{finding.get('status_code', '')}</td>
                        <td>{finding.get('content_length', '')}</td>
                        <td>{'Yes' if finding.get('is_critical') else 'No'}</td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            
            return html
        
        else:
            return str(results)