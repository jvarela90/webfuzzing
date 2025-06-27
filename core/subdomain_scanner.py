# core/subdomain_scanner.py
import dns.resolver
import requests
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Dict, Any
import time
import random

from utils.logger import get_logger

class SubdomainScanner:
    """Escáner de subdominios para descubrimiento automático"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.timeout = config.get('fuzzing.timeout', 5)
        self.max_workers = config.get('fuzzing.max_workers', 10)
        
        # Lista de subdominios comunes
        self.common_subdomains = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'mail', 'm', 'imap', 'test',
            'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'vpn', 'ns3',
            'mail2', 'new', 'mysql', 'old', 'www1', 'beta', 'api', 'stage', 'staging',
            'app', 'stats', 'monitor', 'demo', 'support', 'static', 'cdn', 'media',
            'secure', 'auth', 'login', 'panel', 'control', 'manage', 'dashboard'
        ]
    
    def resolve_subdomain(self, subdomain: str, domain: str) -> Dict[str, Any]:
        """Resolver un subdominio específico"""
        full_domain = f"{subdomain}.{domain}"
        result = {
            'subdomain': subdomain,
            'full_domain': full_domain,
            'resolved': False,
            'ip_addresses': [],
            'http_status': None,
            'https_status': None,
            'response_time': None
        }
        
        try:
            # Resolución DNS
            answers = dns.resolver.resolve(full_domain, 'A')
            result['resolved'] = True
            result['ip_addresses'] = [str(answer) for answer in answers]
            
            # Probar conectividad HTTP/HTTPS
            start_time = time.time()
            
            # Probar HTTPS primero
            try:
                response = requests.get(f"https://{full_domain}", 
                                      timeout=self.timeout, 
                                      verify=False,
                                      allow_redirects=False)
                result['https_status'] = response.status_code
            except:
                pass
            
            # Probar HTTP si HTTPS falló
            if not result['https_status']:
                try:
                    response = requests.get(f"http://{full_domain}", 
                                          timeout=self.timeout,
                                          allow_redirects=False)
                    result['http_status'] = response.status_code
                except:
                    pass
            
            result['response_time'] = time.time() - start_time
            
        except dns.resolver.NXDOMAIN:
            pass  # Subdominio no existe
        except dns.resolver.NoAnswer:
            pass  # Sin respuesta DNS
        except Exception as e:
            self.logger.debug(f"Error resolviendo {full_domain}: {e}")
        
        return result
    
    def scan_common_subdomains(self, domain: str) -> List[Dict[str, Any]]:
        """Escanear subdominios comunes"""
        self.logger.info(f"Escaneando subdominios comunes para {domain}")
        
        found_subdomains = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_subdomain = {
                executor.submit(self.resolve_subdomain, sub, domain): sub 
                for sub in self.common_subdomains
            }
            
            # Recoger resultados
            for future in as_completed(future_to_subdomain):
                result = future.result()
                if result['resolved']:
                    found_subdomains.append(result)
                    self.logger.info(f"Subdominio encontrado: {result['full_domain']}")
        
        return found_subdomains
    
    def bruteforce_subdomains(self, domain: str, wordlist: List[str] = None, 
                             max_attempts: int = 1000) -> List[Dict[str, Any]]:
        """Hacer fuerza bruta de subdominios con lista personalizada"""
        if not wordlist:
            # Generar lista básica si no se proporciona
            wordlist = self.generate_subdomain_wordlist(max_attempts)
        
        wordlist = wordlist[:max_attempts]  # Limitar intentos
        
        self.logger.info(f"Fuerza bruta de subdominios para {domain} - {len(wordlist)} intentos")
        
        found_subdomains = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_subdomain = {
                executor.submit(self.resolve_subdomain, sub, domain): sub 
                for sub in wordlist
            }
            
            for future in as_completed(future_to_subdomain):
                result = future.result()
                if result['resolved']:
                    found_subdomains.append(result)
                    self.logger.info(f"Subdominio encontrado (fuerza bruta): {result['full_domain']}")
                
                # Pequeña pausa para no sobrecargar DNS
                time.sleep(0.1)
        
        return found_subdomains
    
    def generate_subdomain_wordlist(self, max_size: int = 1000) -> List[str]:
        """Generar lista de subdominios para fuerza bruta"""
        wordlist = set(self.common_subdomains)
        
        # Patrones numéricos
        for i in range(1, 21):
            wordlist.add(str(i))
            wordlist.add(f"web{i}")
            wordlist.add(f"server{i}")
            wordlist.add(f"host{i}")
        
        # Combinaciones con años
        current_year = time.localtime().tm_year
        for year in range(current_year - 5, current_year + 2):
            wordlist.add(str(year))
            wordlist.add(f"backup{year}")
        
        # Palabras comunes con prefijos/sufijos
        base_words = ['admin', 'test', 'dev', 'prod', 'stage', 'beta', 'alpha']
        suffixes = ['', '1', '2', 'new', 'old', 'backup']
        
        for word in base_words:
            for suffix in suffixes:
                if suffix:
                    wordlist.add(f"{word}{suffix}")
                    wordlist.add(f"{word}-{suffix}")
                    wordlist.add(f"{word}_{suffix}")
        
        # Convertir a lista y limitar tamaño
        final_list = list(wordlist)[:max_size]
        
        # Mezclar para mejor distribución
        random.shuffle(final_list)
        
        return final_list
    
    def scan_certificate_transparency(self, domain: str) -> List[str]:
        """Buscar subdominios en Certificate Transparency logs"""
        subdomains = set()
        
        try:
            # Usar crt.sh API
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                
                for cert in certificates:
                    name_value = cert.get('name_value', '')
                    
                    # Procesar nombres de dominio del certificado
                    for name in name_value.split('\n'):
                        name = name.strip().lower()
                        
                        # Filtrar y validar
                        if domain in name and name.endswith(f".{domain}"):
                            subdomain = name.replace(f".{domain}", "")
                            if subdomain and '.' not in subdomain:  # Solo subdominios de primer nivel
                                subdomains.add(subdomain)
                
                self.logger.info(f"Certificate Transparency: {len(subdomains)} subdominios únicos")
                
        except Exception as e:
            self.logger.warning(f"Error consultando Certificate Transparency: {e}")
        
        return list(subdomains)
    
    def comprehensive_scan(self, domain: str, include_bruteforce: bool = True) -> Dict[str, Any]:
        """Escaneo completo de subdominios combinando múltiples técnicas"""
        self.logger.info(f"Iniciando escaneo completo de subdominios para {domain}")
        
        start_time = time.time()
        all_subdomains = []
        unique_subdomains = set()
        
        # 1. Subdominios comunes
        common_results = self.scan_common_subdomains(domain)
        all_subdomains.extend(common_results)
        unique_subdomains.update([r['subdomain'] for r in common_results])
        
        # 2. Certificate Transparency
        try:
            ct_subdomains = self.scan_certificate_transparency(domain)
            
            # Resolver subdominios encontrados en CT
            if ct_subdomains:
                self.logger.info(f"Resolviendo {len(ct_subdomains)} subdominios de CT")
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    ct_futures = {
                        executor.submit(self.resolve_subdomain, sub, domain): sub 
                        for sub in ct_subdomains if sub not in unique_subdomains
                    }
                    
                    for future in as_completed(ct_futures):
                        result = future.result()
                        if result['resolved']:
                            all_subdomains.append(result)
                            unique_subdomains.add(result['subdomain'])
        
        except Exception as e:
            self.logger.warning(f"Error en Certificate Transparency: {e}")
        
        # 3. Fuerza bruta (opcional)
        if include_bruteforce:
            # Generar wordlist excluyendo subdominios ya encontrados
            wordlist = self.generate_subdomain_wordlist(1500)
            remaining_wordlist = [w for w in wordlist if w not in unique_subdomains]
            
            if remaining_wordlist:
                bruteforce_results = self.bruteforce_subdomains(
                    domain, 
                    remaining_wordlist[:1000],  # Limitar a 1000 para rendimiento
                    max_attempts=1000
                )
                all_subdomains.extend(bruteforce_results)
        
        # Estadísticas finales
        scan_duration = time.time() - start_time
        
        # Agrupar por estado HTTP
        active_subdomains = [s for s in all_subdomains 
                           if s.get('https_status') or s.get('http_status')]
        
        results = {
            'domain': domain,
            'scan_duration': scan_duration,
            'total_found': len(all_subdomains),
            'active_subdomains': len(active_subdomains),
            'subdomains': all_subdomains,
            'summary': {
                'with_https': len([s for s in all_subdomains if s.get('https_status')]),
                'with_http': len([s for s in all_subdomains if s.get('http_status')]),
                'dns_only': len([s for s in all_subdomains 
                               if not s.get('https_status') and not s.get('http_status')])
            }
        }
        
        self.logger.info(f"Escaneo completo de subdominios finalizado:")
        self.logger.info(f"  - Duración: {scan_duration:.2f}s")
        self.logger.info(f"  - Subdominios encontrados: {len(all_subdomains)}")
        self.logger.info(f"  - Subdominios activos: {len(active_subdomains)}")
        
        return results
