import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Callable
from pathlib import Path
from loguru import logger
from dataclasses import dataclass
from config.settings import Config

@dataclass
class FuzzResult:
    """Resultado de una prueba de fuzzing"""
    url: str
    status_code: int
    response_time: float
    content_length: int
    payload: str
    vulnerable: bool = False
    error: Optional[str] = None

class FuzzingEngine:
    """Motor de fuzzing mejorado con async y rate limiting"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.session = None
        self.results = []
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'vulnerabilities_found': 0,
            'start_time': None,
            'end_time': None
        }
        
    async def __aenter__(self):
        """Context manager para manejo de sesiones"""
        connector = aiohttp.TCPConnector(
            limit=self.config.MAX_CONCURRENT_REQUESTS,
            limit_per_host=20
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.REQUEST_TIMEOUT
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.config.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cerrar sesión al finalizar"""
        if self.session:
            await self.session.close()
    
    async def load_payloads(self, payload_file: str) -> List[str]:
        """Cargar payloads desde archivo"""
        payload_path = Path(payload_file)
        if not payload_path.exists():
            logger.error(f"Archivo de payloads no encontrado: {payload_file}")
            return []
        
        try:
            with open(payload_path, 'r', encoding='utf-8') as f:
                payloads = [line.strip() for line in f if line.strip()]
            logger.info(f"Cargados {len(payloads)} payloads desde {payload_file}")
            return payloads
        except Exception as e:
            logger.error(f"Error cargando payloads: {e}")
            return []
    
    async def test_single_url(self, base_url: str, payload: str) -> FuzzResult:
        """Probar una URL con un payload específico"""
        # Reemplazar marcadores de posición
        test_url = base_url.replace('FUZZ', payload)
        start_time = time.time()
        
        try:
            async with self.session.get(test_url) as response:
                response_time = time.time() - start_time
                content = await response.text()
                
                result = FuzzResult(
                    url=test_url,
                    status_code=response.status,
                    response_time=response_time,
                    content_length=len(content),
                    payload=payload
                )
                
                # Detectar vulnerabilidades simples
                result.vulnerable = self._detect_vulnerability(content, response.status)
                
                self.stats['successful_requests'] += 1
                if result.vulnerable:
                    self.stats['vulnerabilities_found'] += 1
                    logger.warning(f"🚨 Posible vulnerabilidad encontrada: {test_url}")
                
                return result
                
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Error probando {test_url}: {e}")
            return FuzzResult(
                url=test_url,
                status_code=0,
                response_time=time.time() - start_time,
                content_length=0,
                payload=payload,
                error=str(e)
            )
    
    def _detect_vulnerability(self, content: str, status_code: int) -> bool:
        """Detectar vulnerabilidades básicas"""
        vulnerability_indicators = [
            'sql syntax error',
            'mysql_fetch_array',
            'warning: mysql',
            'oracle error',
            'microsoft odbc',
            'error in your sql syntax',
            '<script>alert(',
            'javascript:alert(',
            '../../../etc/passwd',
            'root:x:0:0:',
            'directory listing',
            'index of /'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in vulnerability_indicators)
    
    async def fuzz_url(self, 
                      base_url: str, 
                      payloads: List[str], 
                      progress_callback: Optional[Callable] = None) -> List[FuzzResult]:
        """Ejecutar fuzzing en una URL con múltiples payloads"""
        
        logger.info(f"🚀 Iniciando fuzzing de {base_url} con {len(payloads)} payloads")
        self.stats['start_time'] = time.time()
        self.stats['total_requests'] = len(payloads)
        
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_REQUESTS)
        
        async def bounded_test(payload):
            async with semaphore:
                result = await self.test_single_url(base_url, payload)
                if progress_callback:
                    progress_callback(len(self.results), len(payloads))
                return result
        
        # Ejecutar todas las pruebas de forma concurrente
        tasks = [bounded_test(payload) for payload in payloads]
        self.results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar excepciones
        self.results = [r for r in self.results if isinstance(r, FuzzResult)]
        
        self.stats['end_time'] = time.time()
        self._log_stats()
        
        return self.results
    
    def _log_stats(self):
        """Mostrar estadísticas del fuzzing"""
        duration = self.stats['end_time'] - self.stats['start_time']
        rps = self.stats['total_requests'] / duration if duration > 0 else 0
        
        logger.info("📊 Estadísticas del Fuzzing:")
        logger.info(f"   Total de requests: {self.stats['total_requests']}")
        logger.info(f"   Exitosos: {self.stats['successful_requests']}")
        logger.info(f"   Fallidos: {self.stats['failed_requests']}")
        logger.info(f"   Vulnerabilidades: {self.stats['vulnerabilities_found']}")
        logger.info(f"   Duración: {duration:.2f}s")
        logger.info(f"   Requests/seg: {rps:.2f}")
    
    def get_interesting_results(self) -> List[FuzzResult]:
        """Obtener resultados interesantes (códigos de estado específicos)"""
        interesting_codes = [200, 201, 204, 301, 302, 307, 403, 500, 503]
        return [r for r in self.results if r.status_code in interesting_codes]
    
    def get_vulnerable_results(self) -> List[FuzzResult]:
        """Obtener resultados con posibles vulnerabilidades"""
        return [r for r in self.results if r.vulnerable]
    
    def export_results(self, format='json', filename='fuzzing_results'):
        """Exportar resultados en diferentes formatos"""
        import json
        import csv
        
        if format == 'json':
            with open(f"{filename}.json", 'w') as f:
                json.dump([
                    {
                        'url': r.url,
                        'status_code': r.status_code,
                        'response_time': r.response_time,
                        'content_length': r.content_length,
                        'payload': r.payload,
                        'vulnerable': r.vulnerable,
                        'error': r.error
                    } for r in self.results
                ], f, indent=2)
        
        elif format == 'csv':
            with open(f"{filename}.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Status Code', 'Response Time', 'Content Length', 'Payload', 'Vulnerable', 'Error'])
                for r in self.results:
                    writer.writerow([r.url, r.status_code, r.response_time, r.content_length, r.payload, r.vulnerable, r.error])
        
        logger.info(f"Resultados exportados a {filename}.{format}")

# Función principal para usar desde línea de comandos
async def main():
    """Función principal para ejecución desde CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='URLControl Fuzzing Engine')
    parser.add_argument('--url', required=True, help='URL base para fuzzing (use FUZZ como placeholder)')
    parser.add_argument('--payloads', required=True, help='Archivo con payloads')
    parser.add_argument('--output', default='results', help='Nombre del archivo de salida')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Formato de salida')
    
    args = parser.parse_args()
    
    async with FuzzingEngine() as fuzzer:
        payloads = await fuzzer.load_payloads(args.payloads)
        if not payloads:
            logger.error("No se pudieron cargar payloads")
            return
        
        results = await fuzzer.fuzz_url(args.url, payloads)
        fuzzer.export_results(args.format, args.output)
        
        # Mostrar resumen
        interesting = fuzzer.get_interesting_results()
        vulnerable = fuzzer.get_vulnerable_results()
        
        logger.info(f"✅ Fuzzing completado: {len(interesting)} resultados interesantes, {len(vulnerable)} vulnerabilidades potenciales")

if __name__ == "__main__":
    asyncio.run(main())