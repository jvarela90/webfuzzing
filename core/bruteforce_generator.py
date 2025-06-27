# core/bruteforce_generator.py
import itertools
import string
import random
import threading
from typing import List, Set, Iterator, Dict, Any
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from utils.logger import get_logger

class BruteforceGenerator:
    """Generador inteligente de rutas por fuerza bruta"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Configuración de caracteres
        self.alphabet = config.get('fuzzing.alphabet', string.ascii_letters)
        self.numbers = config.get('fuzzing.numbers', string.digits)
        self.special_chars = config.get('fuzzing.special_chars', '_-.')
        self.max_length = config.get('fuzzing.max_path_length', 12)
        
        # Estadísticas de generación
        self.stats = {
            'total_generated': 0,
            'successful_patterns': [],
            'start_time': None,
            'generation_time': 0
        }
        
        # Cache de patrones exitosos
        self.successful_patterns = set()
        self.load_successful_patterns()
    
    def generate_sequential(self, charset: str, length: int, max_count: int = 1000) -> Iterator[str]:
        """Generar rutas secuenciales con charset específico"""
        count = 0
        for combination in itertools.product(charset, repeat=length):
            if count >= max_count:
                break
            
            path = ''.join(combination)
            yield path
            count += 1
            self.stats['total_generated'] += 1
    
    def generate_random(self, charset: str, length: int, count: int) -> List[str]:
        """Generar rutas aleatorias"""
        paths = []
        for _ in range(count):
            path = ''.join(random.choices(charset, k=length))
            paths.append(path)
            self.stats['total_generated'] += 1
        
        return paths
    
    def generate_pattern_based(self, patterns: List[str], max_count: int = 500) -> List[str]:
        """Generar rutas basadas en patrones conocidos"""
        paths = []
        
        # Patrones comunes para aplicaciones web
        common_patterns = [
            # Patrones administrativos
            ('admin', ['', '1', '2', '_panel', '_area']),
            ('panel', ['', '_admin', '_control', '_user']),
            ('control', ['', '_panel', '_admin']),
            
            # Patrones de desarrollo
            ('dev', ['', '_test', '_stage', '_prod']),
            ('test', ['', '_dev', '_stage', '_env']),
            ('stage', ['', '_test', '_dev', '_prod']),
            
            # Patrones de API
            ('api', ['', '_v1', '_v2', '_test', '_dev']),
            ('v1', ['', '_api', '_test']),
            ('v2', ['', '_api', '_test']),
            
            # Patrones de backup
            ('backup', ['', '_old', '_new', '_temp']),
            ('old', ['', '_backup', '_temp']),
            ('temp', ['', '_backup', '_old']),
        ]
        
        # Combinar patrones base con patrones proporcionados
        all_patterns = common_patterns + [(p, ['', '1', '2']) for p in patterns]
        
        for base, suffixes in all_patterns:
            if len(paths) >= max_count:
                break
                
            for suffix in suffixes:
                path = base + suffix
                paths.append(path)
                
                # Agregar variaciones con extensiones
                for ext in ['.php', '.html', '.asp', '.jsp']:
                    if len(paths) >= max_count:
                        break
                    paths.append(path + ext)
        
        self.stats['total_generated'] += len(paths)
        return paths
    
    def generate_smart_combinations(self, base_words: List[str], max_count: int = 1000) -> List[str]:
        """Generar combinaciones inteligentes basadas en palabras base"""
        paths = []
        
        # Prefijos y sufijos comunes
        prefixes = ['', 'new_', 'old_', 'tmp_', 'test_', 'dev_', 'admin_']
        suffixes = ['', '_new', '_old', '_tmp', '_test', '_dev', '_admin', '_backup']
        separators = ['', '-', '_', '.']
        
        # Números comunes
        numbers = ['', '1', '2', '3', '01', '02', '03', '2023', '2024', '2025']
        
        count = 0
        for word in base_words[:20]:  # Limitar palabras base
            if count >= max_count:
                break
                
            for prefix in prefixes[:5]:  # Limitar prefijos
                for suffix in suffixes[:5]:  # Limitar sufijos
                    for separator in separators[:3]:  # Limitar separadores
                        for num in numbers[:5]:  # Limitar números
                            if count >= max_count:
                                break
                            
                            # Generar combinación
                            parts = [prefix, word, suffix, num]
                            path = separator.join(filter(None, parts))
                            
                            if path and path != word:  # Evitar duplicados exactos
                                paths.append(path)
                                count += 1
        
        self.stats['total_generated'] += len(paths)
        return paths
    
    def generate_numeric_sequences(self, max_count: int = 200) -> List[str]:
        """Generar secuencias numéricas comunes"""
        paths = []
        
        # Rangos numéricos comunes
        ranges = [
            (1, 11),      # 1-10
            (1, 101),     # 1-100
            (2020, 2026), # Años recientes
            (80, 8081),   # Puertos comunes
        ]
        
        for start, end in ranges:
            for i in range(start, min(end, start + max_count // len(ranges))):
                paths.append(str(i))
                
                # Agregar variaciones con ceros
                if i < 100:
                    paths.append(f"{i:02d}")
                if i < 1000:
                    paths.append(f"{i:03d}")
        
        self.stats['total_generated'] += len(paths)
        return paths
    
    def generate_date_based(self, max_count: int = 100) -> List[str]:
        """Generar rutas basadas en fechas"""
        paths = []
        current_year = datetime.now().year
        
        # Formatos de fecha comunes
        for year in range(current_year - 3, current_year + 2):
            paths.extend([
                str(year),
                str(year)[-2:],  # Año corto
                f"backup_{year}",
                f"log_{year}",
                f"data_{year}"
            ])
            
            for month in range(1, 13):
                if len(paths) >= max_count:
                    break
                    
                paths.extend([
                    f"{year}{month:02d}",
                    f"{year}_{month:02d}",
                    f"backup_{year}{month:02d}",
                    f"log_{year}_{month:02d}"
                ])
        
        self.stats['total_generated'] += len(paths)
        return paths[:max_count]
    
    def generate_technology_based(self, max_count: int = 300) -> List[str]:
        """Generar rutas basadas en tecnologías comunes"""
        paths = []
        
        # Tecnologías y frameworks comunes
        technologies = [
            'php', 'asp', 'jsp', 'python', 'node', 'ruby',
            'wordpress', 'joomla', 'drupal', 'laravel', 'symfony',
            'react', 'angular', 'vue', 'bootstrap', 'jquery',
            'mysql', 'postgres', 'mongodb', 'redis', 'elastic',
            'apache', 'nginx', 'tomcat', 'iis', 'docker'
        ]
        
        # Sufijos relacionados con tecnologías
        tech_suffixes = [
            '', '_config', '_admin', '_panel', '_test', '_dev',
            '_backup', '_log', '_data', '_cache', '_tmp'
        ]
        
        for tech in technologies:
            if len(paths) >= max_count:
                break
                
            for suffix in tech_suffixes:
                if len(paths) >= max_count:
                    break
                    
                path = tech + suffix
                paths.append(path)
                
                # Agregar extensiones relacionadas
                if 'php' in tech.lower():
                    paths.append(path + '.php')
                elif 'asp' in tech.lower():
                    paths.append(path + '.asp')
                elif 'jsp' in tech.lower():
                    paths.append(path + '.jsp')
        
        self.stats['total_generated'] += len(paths)
        return paths[:max_count]
    
    def generate_multilength_alphabetic(self, min_length: int = 3, 
                                      max_length: int = 8, 
                                      max_total: int = 2000) -> List[str]:
        """Generar rutas alfabéticas de múltiples longitudes"""
        paths = []
        paths_per_length = max_total // (max_length - min_length + 1)
        
        for length in range(min_length, min_length + 1):
            # Solo letras minúsculas para eficiencia
            charset = string.ascii_lowercase
            
            if length <= 4:
                # Para longitudes pequeñas, usar generación secuencial
                for path in self.generate_sequential(charset, length, paths_per_length):
                    paths.append(path)
                    if len(paths) >= max_total:
                        break
            else:
                # Para longitudes mayores, usar generación aleatoria
                random_paths = self.generate_random(charset, length, paths_per_length)
                paths.extend(random_paths)
            
            if len(paths) >= max_total:
                break
        
        return paths[:max_total]
    
    def generate_comprehensive_wordlist(self, max_size: int = 5000, 
                                      base_words: List[str] = None) -> List[str]:
        """Generar wordlist completa combinando todas las técnicas"""
        self.stats['start_time'] = time.time()
        self.logger.info("Iniciando generación comprehensiva de wordlist")
        
        all_paths = set()
        base_words = base_words or []
        
        # 1. Patrones conocidos exitosos (prioridad alta)
        if self.successful_patterns:
            pattern_paths = self.generate_pattern_based(
                list(self.successful_patterns), 
                max_count=min(1000, max_size // 6)
            )
            all_paths.update(pattern_paths)
            self.logger.info(f"Patrones exitosos: {len(pattern_paths)} rutas")
        
        # 2. Combinaciones inteligentes con palabras base
        if base_words:
            smart_paths = self.generate_smart_combinations(
                base_words, 
                max_count=min(1500, max_size // 4)
            )
            all_paths.update(smart_paths)
            self.logger.info(f"Combinaciones inteligentes: {len(smart_paths)} rutas")
        
        # 3. Rutas basadas en tecnologías
        tech_paths = self.generate_technology_based(
            max_count=min(800, max_size // 6)
        )
        all_paths.update(tech_paths)
        self.logger.info(f"Rutas tecnológicas: {len(tech_paths)} rutas")
        
        # 4. Secuencias numéricas
        numeric_paths = self.generate_numeric_sequences(
            max_count=min(300, max_size // 15)
        )
        all_paths.update(numeric_paths)
        self.logger.info(f"Secuencias numéricas: {len(numeric_paths)} rutas")
        
        # 5. Rutas basadas en fechas
        date_paths = self.generate_date_based(
            max_count=min(200, max_size // 20)
        )
        all_paths.update(date_paths)
        self.logger.info(f"Rutas de fechas: {len(date_paths)} rutas")
        
        # 6. Si aún hay espacio, agregar rutas alfabéticas
        remaining_space = max_size - len(all_paths)
        if remaining_space > 0:
            alpha_paths = self.generate_multilength_alphabetic(
                min_length=3,
                max_length=min(6, self.max_length),
                max_total=remaining_space
            )
            all_paths.update(alpha_paths)
            self.logger.info(f"Rutas alfabéticas: {len(alpha_paths)} rutas")
        
        # Convertir a lista y mezclar
        final_paths = list(all_paths)
        random.shuffle(final_paths)
        
        # Limitar al tamaño máximo
        final_paths = final_paths[:max_size]
        
        # Actualizar estadísticas
        self.stats['generation_time'] = time.time() - self.stats['start_time']
        
        self.logger.info(f"Wordlist generada: {len(final_paths)} rutas únicas")
        self.logger.info(f"Tiempo de generación: {self.stats['generation_time']:.2f}s")
        
        return final_paths
    
    def mark_pattern_successful(self, pattern: str):
        """Marcar un patrón como exitoso para futura referencia"""
        # Extraer patrón base (sin extensión)
        base_pattern = pattern.split('.')[0]
        
        # Agregar variaciones del patrón
        self.successful_patterns.add(base_pattern)
        
        # Agregar palabras individuales si el patrón contiene separadores
        for separator in ['_', '-', '.']:
            if separator in base_pattern:
                parts = base_pattern.split(separator)
                self.successful_patterns.update(parts)
        
        self.save_successful_patterns()
        self.logger.info(f"Patrón marcado como exitoso: {pattern}")
    
    def save_successful_patterns(self):
        """Guardar patrones exitosos en archivo"""
        try:
            patterns_file = self.config.base_dir / 'data' / 'successful_patterns.txt'
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                for pattern in sorted(self.successful_patterns):
                    f.write(pattern + '\n')
                    
        except Exception as e:
            self.logger.warning(f"Error guardando patrones exitosos: {e}")
    
    def load_successful_patterns(self):
        """Cargar patrones exitosos desde archivo"""
        try:
            patterns_file = self.config.base_dir / 'data' / 'successful_patterns.txt'
            
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.successful_patterns = set(
                        line.strip() for line in f if line.strip()
                    )
                
                self.logger.info(f"Cargados {len(self.successful_patterns)} patrones exitosos")
                
        except Exception as e:
            self.logger.warning(f"Error cargando patrones exitosos: {e}")
            self.successful_patterns = set()
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de generación"""
        return {
            'total_generated': self.stats['total_generated'],
            'successful_patterns_count': len(self.successful_patterns),
            'generation_time': self.stats['generation_time'],
            'patterns_per_second': (
                self.stats['total_generated'] / self.stats['generation_time'] 
                if self.stats['generation_time'] > 0 else 0
            )
        }
