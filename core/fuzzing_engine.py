# core/fuzzing_engine.py
import requests
import csv
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import itertools
import string
import random
from datetime import datetime

from config.database import DatabaseManager
from utils.logger import get_logger
from integrations.ffuf_integration import FFUFIntegration
from integrations.dirsearch_integration import DirsearchIntegration

class FuzzingEngine:
    """Motor principal de fuzzing web"""
    
    def __init__(self, config):
        self.config = config
        self.db = DatabaseManager(config)
        self.logger = get_logger(__name__)
        
        # Configuración de fuzzing
        self.timeout = config.get('fuzzing.timeout')
        self.max_workers = config.get('fuzzing.max_workers')
        self.user_agent = config.get('fuzzing.user_agent')
        self.retry_count = config.get('fuzzing.retry_count')
        self.delay = config.get('fuzzing.delay_between_requests')
        self.status_codes = config.get('fuzzing.status_codes_of_interest')
        self.critical_paths = config.get('fuzzing.critical_paths')
        
        # Integración con herramientas externas
        self.ffuf = FFUFIntegration(config) if config.get('tools.ffuf.enabled') else None
        self.dirsearch = DirsearchIntegration(config) if config.get('tools.dirsearch.enabled') else None
        
        # Estadísticas de ejecución
        self.stats = {
            'requests_made': 0,
            'paths_found': 0,
            'critical_found': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }

    def load_domains_from_csv(self, csv_file: str = None) -> List[Dict]:
        """Cargar dominios desde archivo CSV"""
        csv_file = csv_file or str(self.config.get_domains_file())
        domains = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or row[0].startswith('#'):
                        continue
                        
                    domain_info = row[0].strip()
                    if ':' in domain_info:
                        host, port = domain_info.split(':')
                        port = int(port)
                    else:
                        host = domain_info
                        port = 443 if not host.startswith('http://') else 80
                    
                    # Determinar protocolo
                    if host.startswith(('http://', 'https://')):
                        protocol = 'https' if host.startswith('https://') else 'http'
                        host = host.replace('http://', '').replace('https://', '')
                    else:
                        protocol = 'https' if port == 443 else 'http'
                    
                    domain_entry = {
                        'host': host,
                        'port': port,
                        'protocol': protocol,
                        'base_url': f"{protocol}://{host}:{port}" if port not in [80, 443] else f"{protocol}://{host}"
                    }
                    
                    domains.append(domain_entry)
                    
                    # Agregar a base de datos
                    self.db.add_domain(host, port, protocol)
                    
        except FileNotFoundError:
            self.logger.error(f"Archivo de dominios no encontrado: {csv_file}")
        except Exception as e:
            self.logger.error(f"Error cargando dominios: {e}")
            
        self.logger.info(f"Cargados {len(domains)} dominios")
        return domains

    def load_dictionary(self) -> List[str]:
        """Cargar diccionario de rutas desde múltiples fuentes"""
        paths = set()
        
        # Cargar diccionarios base
        dict_dir = self.config.get_dictionaries_dir()
        for dict_file in dict_dir.glob('*.txt'):
            try:
                with open(dict_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        path = line.strip()
                        if path and not path.startswith('#'):
                            paths.add(path.lstrip('/'))
            except Exception as e:
                self.logger.warning(f"Error cargando diccionario {dict_file}: {e}")
        
        # Cargar rutas descubiertas previamente
        discovered_file = self.config.base_dir / self.config.get('files.discovered_paths')
        if discovered_file.exists():
            try:
                with open(discovered_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        path = line.strip()
                        if path:
                            paths.add(path.lstrip('/'))
            except Exception as e:
                self.logger.warning(f"Error cargando rutas descubiertas: {e}")
        
        # Agregar rutas comunes básicas si el diccionario está vacío
        if not paths:
            basic_paths = [
                'admin', 'admin/', 'administrator', 'login', 'panel',
                'config', 'config.php', 'wp-admin/', 'backup', 'test',
                'dev', 'development', '.git/', '.env', 'api', 'api/',
                'dashboard', 'phpmyadmin', 'mysql', 'database'
            ]
            paths.update(basic_paths)
        
        paths_list = sorted(list(paths))
        self.logger.info(f"Diccionario cargado con {len(paths_list)} rutas")
        return paths_list

    def generate_bruteforce_paths(self, max_length: int = None) -> List[str]:
        """Generar rutas por fuerza bruta con combinaciones alfabéticas"""
        max_length = max_length or self.config.get('fuzzing.max_path_length')
        alphabet = self.config.get('fuzzing.alphabet')
        numbers = self.config.get('fuzzing.numbers')
        special_chars = self.config.get('fuzzing.special_chars')
        
        # Caracteres a usar
        chars = alphabet + numbers + special_chars
        
        generated_paths = []
        
        # Generar combinaciones de diferentes longitudes (de 3 a max_length)
        for length in range(3, min(max_length + 1, 8)):  # Limitar a 7 para evitar explosión combinatoria
            # Generar algunas combinaciones aleatorias
            for _ in range(min(100, 26 ** length)):  # Limitar cantidad
                path = ''.join(random.choices(chars, k=length))
                generated_paths.append(path)
                
                # Agregar variaciones con extensiones comunes
                for ext in ['.php', '.html', '.asp', '.jsp', '.txt']:
                    generated_paths.append(path + ext)
        
        # Agregar patrones comunes
        common_patterns = []
        for word in ['admin', 'test', 'dev', 'api', 'panel']:
            for suffix in ['', '1', '2', '_old', '_new', '_backup']:
                common_patterns.append(word + suffix)
                common_patterns.append(word + suffix + '/')
        
        generated_paths.extend(common_patterns)
        
        # Eliminar duplicados y ordenar
        unique_paths = list(set(generated_paths))
        random.shuffle(unique_paths)  # Mezclar para mejor distribución
        
        self.logger.info(f"Generadas {len(unique_paths)} rutas por fuerza bruta")
        return unique_paths[:5000]  # Limitar a 5000 para rendimiento

    def test_single_url(self, url: str, domain_id: int) -> Optional[Dict]:
        """Probar una URL específica"""
        try:
            self.stats['requests_made'] += 1
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=False,
                verify=False  # Para desarrollo
            )
            
            if response.status_code in self.status_codes:
                path = url.split('/', 3)[3] if len(url.split('/')) > 3 else ''
                
                result = {
                    'url': url,
                    'path': path,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'content_type': response.headers.get('content-type', ''),
                    'response_time': response.elapsed.total_seconds(),
                    'is_critical': any(critical in path.lower() for critical in self.critical_paths)
                }
                
                # Guardar en base de datos
                self.db.add_discovered_path(
                    domain_id=domain_id,
                    path=path,
                    full_url=url,
                    status_code=response.status_code,
                    content_length=result['content_length'],
                    content_type=result['content_type'],
                    response_time=result['response_time']
                )
                
                self.stats['paths_found'] += 1
                if result['is_critical']:
                    self.stats['critical_found'] += 1
                    self.logger.warning(f"Ruta crítica encontrada: {url}")
                
                return result
                
        except requests.exceptions.Timeout:
            self.logger.debug(f"Timeout en {url}")
        except requests.exceptions.ConnectionError:
            self.logger.debug(f"Error de conexión en {url}")
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.debug(f"Error probando {url}: {e}")
            
        return None

    def fuzz_domain(self, domain: Dict, paths: List[str]) -> List[Dict]:
        """Realizar fuzzing en un dominio específico"""
        self.logger.info(f"Iniciando fuzzing en {domain['base_url']}")
        
        # Obtener ID del dominio
        domain_id = self.db.add_domain(domain['host'], domain['port'], domain['protocol'])
        
        results = []
        urls_to_test = []
        
        # Preparar URLs para probar
        for path in paths:
            url = urljoin(domain['base_url'] + '/', path.lstrip('/'))
            urls_to_test.append((url, domain_id))
        
        # Ejecutar fuzzing con múltiples hilos
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.test_single_url, url, domain_id): url 
                for url, domain_id in urls_to_test
            }
            
            for future in as_completed(future_to_url):
                result = future.result()
                if result:
                    results.append(result)
                    self.logger.info(f"[{result['status_code']}] {result['url']}")
                
                # Pequeña pausa entre requests
                if self.delay > 0:
                    time.sleep(self.delay)
        
        self.logger.info(f"Fuzzing completado en {domain['base_url']}: {len(results)} rutas encontradas")
        return results

    def run_integrated_scan(self, domain: Dict, paths: List[str]) -> List[Dict]:
        """Ejecutar escaneo integrado con herramientas externas"""
        all_results = []
        
        # Fuzzing nativo
        native_results = self.fuzz_domain(domain, paths)
        all_results.extend(native_results)
        
        # Integración con ffuf si está disponible
        if self.ffuf:
            try:
                ffuf_results = self.ffuf.scan_domain(domain['base_url'], paths)
                all_results.extend(ffuf_results)
                self.logger.info(f"ffuf encontró {len(ffuf_results)} rutas adicionales")
            except Exception as e:
                self.logger.error(f"Error ejecutando ffuf: {e}")
        
        # Integración con dirsearch si está disponible
        if self.dirsearch:
            try:
                dirsearch_results = self.dirsearch.scan_domain(domain['base_url'], paths)
                all_results.extend(dirsearch_results)
                self.logger.info(f"dirsearch encontró {len(dirsearch_results)} rutas adicionales")
            except Exception as e:
                self.logger.error(f"Error ejecutando dirsearch: {e}")
        
        # Eliminar duplicados
        unique_results = []
        seen_urls = set()
        for result in all_results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        return unique_results

    def save_discovered_paths(self, results: List[Dict]):
        """Guardar nuevas rutas descubiertas al diccionario"""
        discovered_file = self.config.base_dir / self.config.get('files.discovered_paths')
        
        # Leer rutas existentes
        existing_paths = set()
        if discovered_file.exists():
            with open(discovered_file, 'r', encoding='utf-8') as f:
                existing_paths = set(line.strip() for line in f)
        
        # Agregar nuevas rutas
        new_paths = set()
        for result in results:
            path = result.get('path', '').strip()
            if path and path not in existing_paths:
                new_paths.add(path)
        
        if new_paths:
            with open(discovered_file, 'a', encoding='utf-8') as f:
                for path in sorted(new_paths):
                    f.write(path + '\n')
            
            self.logger.info(f"Agregadas {len(new_paths)} nuevas rutas al diccionario")

    def generate_report(self, all_results: List[Dict], scan_duration: float) -> str:
        """Generar reporte de resultados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.config.get_results_dir() / f"reporte_{timestamp}.txt"
        
        # Agrupar resultados por dominio
        results_by_domain = {}
        for result in all_results:
            domain = urlparse(result['url']).netloc
            if domain not in results_by_domain:
                results_by_domain[domain] = []
            results_by_domain[domain].append(result)
        
        # Generar reporte
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"REPORTE DE FUZZING WEB\n")
            f.write(f"={'=' * 50}\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duración: {scan_duration:.2f} segundos\n")
            f.write(f"Requests realizados: {self.stats['requests_made']}\n")
            f.write(f"Rutas encontradas: {self.stats['paths_found']}\n")
            f.write(f"Rutas críticas: {self.stats['critical_found']}\n")
            f.write(f"Errores: {self.stats['errors']}\n\n")
            
            # Resumen por dominio
            f.write("RESUMEN POR DOMINIO\n")
            f.write("-" * 30 + "\n")
            for domain, results in results_by_domain.items():
                critical_count = sum(1 for r in results if r.get('is_critical', False))
                f.write(f"{domain}: {len(results)} rutas ({critical_count} críticas)\n")
            
            f.write("\n\nRESULTADOS DETALLADOS\n")
            f.write("=" * 50 + "\n\n")
            
            for domain, results in results_by_domain.items():
                f.write(f"\nDOMINIO: {domain}\n")
                f.write("-" * (len(domain) + 9) + "\n")
                
                # Primero las rutas críticas
                critical_results = [r for r in results if r.get('is_critical', False)]
                if critical_results:
                    f.write("\n🚨 RUTAS CRÍTICAS:\n")
                    for result in critical_results:
                        f.write(f"  [{result['status_code']}] {result['url']}\n")
                
                # Luego las demás rutas
                normal_results = [r for r in results if not r.get('is_critical', False)]
                if normal_results:
                    f.write("\n📁 OTRAS RUTAS:\n")
                    for result in normal_results:
                        f.write(f"  [{result['status_code']}] {result['url']}\n")
        
        self.logger.info(f"Reporte generado: {report_file}")
        return str(report_file)

    def run_scan(self, domains_file: str = None, output_dir: str = None) -> Dict:
        """Ejecutar escaneo completo"""
        self.stats['start_time'] = time.time()
        self.logger.info("Iniciando escaneo de fuzzing web")
        
        try:
            # Cargar dominios
            domains = self.load_domains_from_csv(domains_file)
            if not domains:
                raise Exception("No se pudieron cargar dominios")
            
            # Cargar diccionario base
            base_paths = self.load_dictionary()
            
            # Generar rutas por fuerza bruta
            bruteforce_paths = self.generate_bruteforce_paths()
            
            # Combinar todos los paths
            all_paths = list(set(base_paths + bruteforce_paths))
            self.logger.info(f"Total de rutas a probar: {len(all_paths)}")
            
            # Realizar fuzzing en todos los dominios
            all_results = []
            for domain in domains:
                domain_results = self.run_integrated_scan(domain, all_paths)
                all_results.extend(domain_results)
            
            # Guardar nuevas rutas descubiertas
            self.save_discovered_paths(all_results)
            
            # Generar reporte
            self.stats['end_time'] = time.time()
            scan_duration = self.stats['end_time'] - self.stats['start_time']
            report_file = self.generate_report(all_results, scan_duration)
            
            # Estadísticas finales
            scan_stats = {
                'total_domains': len(domains),
                'total_paths_tested': len(all_paths) * len(domains),
                'paths_found': self.stats['paths_found'],
                'critical_found': self.stats['critical_found'],
                'scan_duration': scan_duration,
                'report_file': report_file,
                'results': all_results
            }
            
            self.logger.info(f"Escaneo completado en {scan_duration:.2f} segundos")
            self.logger.info(f"Dominios: {len(domains)}, Rutas encontradas: {self.stats['paths_found']}, Críticas: {self.stats['critical_found']}")
            
            return scan_stats
            
        except Exception as e:
            self.logger.error(f"Error durante el escaneo: {e}")
            raise e