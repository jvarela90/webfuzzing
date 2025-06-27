# core/dictionary_manager.py
import os
import requests
import json
from pathlib import Path
from typing import List, Set, Dict, Any
import itertools
import string
import random
from collections import Counter
from datetime import datetime, timedelta

from utils.logger import get_logger

class DictionaryManager:
    """Gestor inteligente de diccionarios para fuzzing"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.dictionaries_dir = config.get_dictionaries_dir()
        self.discovered_file = config.base_dir / config.get('files.discovered_paths')
        
        # Estadísticas de uso
        self.path_stats = {}
        self.load_stats()
    
    def load_base_dictionaries(self) -> Set[str]:
        """Cargar diccionarios base desde archivos"""
        paths = set()
        
        # Cargar todos los archivos .txt del directorio de diccionarios
        for dict_file in self.dictionaries_dir.glob('*.txt'):
            try:
                with open(dict_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Limpiar la ruta
                            clean_path = self.clean_path(line)
                            if clean_path:
                                paths.add(clean_path)
                
                self.logger.info(f"Cargado diccionario: {dict_file.name}")
                
            except Exception as e:
                self.logger.warning(f"Error cargando {dict_file}: {e}")
        
        return paths
    
    def load_discovered_paths(self) -> Set[str]:
        """Cargar rutas descubiertas previamente"""
        paths = set()
        
        if self.discovered_file.exists():
            try:
                with open(self.discovered_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            clean_path = self.clean_path(line)
                            if clean_path:
                                paths.add(clean_path)
                
                self.logger.info(f"Cargadas {len(paths)} rutas descubiertas previamente")
                
            except Exception as e:
                self.logger.warning(f"Error cargando rutas descubiertas: {e}")
        
        return paths
    
    def download_seclists(self) -> Set[str]:
        """Descargar diccionarios de SecLists (GitHub)"""
        paths = set()
        
        # URLs de diccionarios útiles de SecLists
        seclist_urls = [
            "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt",
            "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-small.txt",
            "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/big.txt"
        ]
        
        for url in seclist_urls:
            try:
                self.logger.info(f"Descargando diccionario: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Procesar líneas
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        clean_path = self.clean_path(line)
                        if clean_path:
                            paths.add(clean_path)
                
                # Guardar localmente para uso futuro
                filename = url.split('/')[-1]
                local_file = self.dictionaries_dir / f"seclist_{filename}"
                
                with open(local_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                self.logger.info(f"Diccionario guardado: {local_file}")
                
            except Exception as e:
                self.logger.warning(f"Error descargando {url}: {e}")
        
        return paths
    
    def generate_smart_combinations(self, base_words: Set[str], max_combinations: int = 1000) -> Set[str]:
        """Generar combinaciones inteligentes basadas en patrones comunes"""
        combinations = set()
        
        # Sufijos comunes
        suffixes = ['', '1', '2', '3', '_old', '_new', '_backup', '_test', '_dev', 
                   '_prod', '_staging', '_temp', '.bak', '.old', '.tmp']
        
        # Prefijos comunes  
        prefixes = ['', 'old_', 'new_', 'test_', 'dev_', 'backup_', 'tmp_']
        
        # Extensiones comunes
        extensions = ['', '.php', '.asp', '.jsp', '.html', '.txt', '.xml', '.json',
                     '.config', '.conf', '.ini', '.log']
        
        # Palabras base más comunes (limitar para evitar explosión combinatoria)
        common_words = ['admin', 'test', 'dev', 'api', 'www', 'mail', 'ftp', 'blog']
        
        # Agregar palabras base más utilizadas
        if base_words:
            # Obtener las más exitosas basadas en estadísticas
            successful_words = self.get_most_successful_paths(limit=20)
            common_words.extend([word.split('/')[0] for word in successful_words])
        
        # Generar combinaciones
        count = 0
        for word in common_words:
            if count >= max_combinations:
                break
                
            for prefix in prefixes[:5]:  # Limitar prefijos
                for suffix in suffixes[:8]:  # Limitar sufijos
                    for ext in extensions[:6]:  # Limitar extensiones
                        if count >= max_combinations:
                            break
                        
                        combination = f"{prefix}{word}{suffix}{ext}"
                        if combination != word:  # Evitar duplicados exactos
                            combinations.add(combination)
                            count += 1
        
        return combinations
    
    def generate_bruteforce_paths(self, length_range: tuple = (3, 8), 
                                 max_paths: int = 2000) -> Set[str]:
        """Generar rutas por fuerza bruta con longitudes variables"""
        paths = set()
        
        # Caracteres para generar rutas
        alphabet = self.config.get('fuzzing.alphabet', string.ascii_letters)
        numbers = self.config.get('fuzzing.numbers', string.digits)
        special_chars = self.config.get('fuzzing.special_chars', '_-')
        
        # Combinaciones de caracteres
        chars = alphabet + numbers + special_chars
        
        # Patrones comunes para mayor efectividad
        patterns = [
            alphabet,  # Solo letras
            numbers,   # Solo números
            alphabet + numbers,  # Alfanumérico
            alphabet[:26],  # Solo minúsculas
            alphabet[26:],  # Solo mayúsculas
        ]
        
        min_len, max_len = length_range
        
        for length in range(min_len, min(max_len + 1, 9)):  # Limitar para rendimiento
            # Calcular cuántas rutas generar para esta longitud
            paths_for_length = min(max_paths // (max_len - min_len + 1), 500)
            
            for pattern in patterns:
                if len(paths) >= max_paths:
                    break
                
                # Generar rutas aleatorias con este patrón
                for _ in range(paths_for_length // len(patterns)):
                    if len(paths) >= max_paths:
                        break
                    
                    path = ''.join(random.choices(pattern, k=length))
                    paths.add(path)
                    
                    # Agregar variaciones con extensiones
                    for ext in ['.php', '.html', '.txt']:
                        if len(paths) >= max_paths:
                            break
                        paths.add(path + ext)
        
        return paths
    
    def clean_path(self, path: str) -> str:
        """Limpiar y normalizar una ruta"""
        if not path:
            return ""
        
        # Remover espacios y caracteres no deseados
        path = path.strip()
        
        # Remover protocolo si está presente
        if path.startswith(('http://', 'https://')):
            path = '/'.join(path.split('/')[3:])
        
        # Normalizar barras
        path = path.strip('/')
        
        # Filtrar rutas muy largas o con caracteres problemáticos
        if len(path) > 100 or any(char in path for char in ['\n', '\r', '\t']):
            return ""
        
        return path
    
    def update_path_stats(self, path: str, success: bool):
        """Actualizar estadísticas de uso de una ruta"""
        if path not in self.path_stats:
            self.path_stats[path] = {
                'uses': 0,
                'successes': 0,
                'last_used': None,
                'success_rate': 0.0
            }
        
        stats = self.path_stats[path]
        stats['uses'] += 1
        if success:
            stats['successes'] += 1
        
        stats['success_rate'] = stats['successes'] / stats['uses']
        stats['last_used'] = datetime.now().isoformat()
    
    def get_most_successful_paths(self, limit: int = 50) -> List[str]:
        """Obtener las rutas más exitosas"""
        sorted_paths = sorted(
            self.path_stats.items(),
            key=lambda x: (x[1]['success_rate'], x[1]['successes']),
            reverse=True
        )
        
        return [path for path, _ in sorted_paths[:limit]]
    
    def save_stats(self):
        """Guardar estadísticas de uso"""
        stats_file = self.config.base_dir / 'data' / 'path_stats.json'
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.path_stats, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Error guardando estadísticas: {e}")
    
    def load_stats(self):
        """Cargar estadísticas de uso"""
        stats_file = self.config.base_dir / 'data' / 'path_stats.json'
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.path_stats = json.load(f)
                self.logger.info(f"Cargadas estadísticas de {len(self.path_stats)} rutas")
            except Exception as e:
                self.logger.warning(f"Error cargando estadísticas: {e}")
                self.path_stats = {}
    
    def get_optimized_dictionary(self, max_size: int = 10000) -> List[str]:
        """Obtener diccionario optimizado basado en estadísticas y patrones"""
        all_paths = set()
        
        # 1. Cargar diccionarios base (prioridad alta)
        base_paths = self.load_base_dictionaries()
        all_paths.update(base_paths)
        self.logger.info(f"Diccionarios base: {len(base_paths)} rutas")
        
        # 2. Cargar rutas descubiertas (prioridad muy alta)
        discovered_paths = self.load_discovered_paths()
        all_paths.update(discovered_paths)
        self.logger.info(f"Rutas descubiertas: {len(discovered_paths)} rutas")
        
        # 3. Rutas más exitosas (prioridad alta)
        successful_paths = set(self.get_most_successful_paths(500))
        all_paths.update(successful_paths)
        
        # 4. Si hay espacio, agregar combinaciones inteligentes
        if len(all_paths) < max_size * 0.7:
            smart_combinations = self.generate_smart_combinations(
                base_paths, 
                max_combinations=min(2000, max_size - len(all_paths))
            )
            all_paths.update(smart_combinations)
            self.logger.info(f"Combinaciones inteligentes: {len(smart_combinations)} rutas")
        
        # 5. Si aún hay espacio, agregar fuerza bruta
        if len(all_paths) < max_size * 0.8:
            bruteforce_paths = self.generate_bruteforce_paths(
                max_paths=min(1000, max_size - len(all_paths))
            )
            all_paths.update(bruteforce_paths)
            self.logger.info(f"Rutas fuerza bruta: {len(bruteforce_paths)} rutas")
        
        # 6. Descargar SecLists si el diccionario es muy pequeño
        if len(all_paths) < 1000:
            self.logger.info("Diccionario pequeño, descargando SecLists...")
            seclist_paths = self.download_seclists()
            all_paths.update(seclist_paths)
            self.logger.info(f"SecLists: {len(seclist_paths)} rutas adicionales")
        
        # Convertir a lista y limitar tamaño
        final_paths = list(all_paths)
        
        # Priorizar rutas basadas en estadísticas
        if len(final_paths) > max_size:
            # Ordenar por éxito y frecuencia de uso
            prioritized = []
            
            # Primero las rutas con estadísticas exitosas
            for path in final_paths:
                if path in self.path_stats:
                    stats = self.path_stats[path]
                    priority = stats['success_rate'] * 10 + min(stats['uses'], 10)
                else:
                    priority = 1.0 if path in discovered_paths else 0.5
                
                prioritized.append((path, priority))
            
            # Ordenar por prioridad y tomar las mejores
            prioritized.sort(key=lambda x: x[1], reverse=True)
            final_paths = [path for path, _ in prioritized[:max_size]]
        
        # Mezclar para mejor distribución
        random.shuffle(final_paths)
        
        self.logger.info(f"Diccionario final optimizado: {len(final_paths)} rutas")
        return final_paths
