#!/usr/bin/env python3
"""
Generador Inteligente de Wordlists para Fuzzing Web
Genera wordlists dinámicas basadas en análisis de dominios y ML
"""

import os
import re
import json
import requests
import itertools
import string
import logging
import hashlib
from typing import List, Set, Dict, Tuple
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import concurrent.futures
from collections import Counter
import nltk
from nltk.corpus import words as nltk_words
from nltk.tokenize import word_tokenize

# Descargar recursos NLTK si no están presentes
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')

class IntelligentWordlistGenerator:
    """Generador inteligente que aprende y se adapta"""
    
    def __init__(self, base_dir="data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Archivos de aprendizaje
        self.learned_words_file = self.base_dir / "learned_words.json"
        self.success_patterns_file = self.base_dir / "success_patterns.json"
        self.domain_analysis_file = self.base_dir / "domain_analysis.json"
        
        # Diccionarios base
        self.base_paths = self.load_base_dictionaries()
        self.learned_words = self.load_learned_words()
        self.success_patterns = self.load_success_patterns()
        
        # Configuración para generación
        self.max_combination_length = 12
        self.min_word_frequency = 2
        
    def load_base_dictionaries(self) -> Set[str]:
        """Cargar diccionarios base y SecLists"""
        words = set()
        
        # Diccionario base común
        base_words = [
            # Directorios administrativos
            'admin', 'administrator', 'administration', 'panel', 'control',
            'dashboard', 'backend', 'backoffice', 'manager', 'manage',
            
            # APIs y servicios
            'api', 'v1', 'v2', 'v3', 'rest', 'soap', 'graphql', 'webhook',
            'service', 'services', 'endpoint', 'endpoints',
            
            # Archivos de configuración
            'config', 'configuration', 'settings', 'setup', 'install',
            'env', 'environment', 'properties', 'ini', 'conf',
            
            # Respaldos y temporales
            'backup', 'backups', 'bak', 'old', 'tmp', 'temp', 'temporary',
            'archive', 'archives', 'download', 'downloads', 'upload', 'uploads',
            
            # Desarrollo y testing
            'test', 'testing', 'dev', 'development', 'stage', 'staging',
            'beta', 'alpha', 'demo', 'debug', 'logs', 'log',
            
            # Bases de datos
            'db', 'database', 'mysql', 'postgres', 'oracle', 'mssql',
            'phpmyadmin', 'adminer', 'sql', 'data',
            
            # CMS comunes
            'wp-admin', 'wp-content', 'wp-includes', 'wordpress',
            'drupal', 'joomla', 'magento', 'prestashop',
            
            # Directorios web comunes
            'assets', 'static', 'public', 'private', 'secure',
            'images', 'img', 'css', 'js', 'fonts', 'media',
            
            # Autenticación
            'login', 'signin', 'signup', 'register', 'auth', 'oauth',
            'password', 'passwd', 'pwd', 'forgot', 'reset',
            
            # Control de versiones
            '.git', '.svn', '.hg', '.bzr', 'git', 'svn',
            
            # Archivos sensibles
            'secret', 'secrets', 'key', 'keys', 'token', 'tokens',
            'certificate', 'cert', 'certs', 'ssl', 'tls'
        ]
        
        words.update(base_words)
        
        # Cargar desde SecLists si está disponible
        seclists_paths = [
            '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt',
            '/opt/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt',
            './SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt'
        ]
        
        for path in seclists_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            word = line.strip()
                            if word and not word.startswith('#') and len(word) <= 25:
                                words.add(word.lower())
                    self.logger.info(f"Cargadas palabras desde {path}")
                    break
                except Exception as e:
                    self.logger.warning(f"Error cargando {path}: {e}")
        
        return words
    
    def load_learned_words(self) -> Dict[str, int]:
        """Cargar palabras aprendidas con sus frecuencias de éxito"""
        if self.learned_words_file.exists():
            try:
                with open(self.learned_words_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error cargando learned_words: {e}")
        return {}
    
    def save_learned_words(self):
        """Guardar palabras aprendidas"""
        try:
            with open(self.learned_words_file, 'w') as f:
                json.dump(self.learned_words, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando learned_words: {e}")
    
    def load_success_patterns(self) -> Dict[str, List[str]]:
        """Cargar patrones de éxito por dominio"""
        if self.success_patterns_file.exists():
            try:
                with open(self.success_patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error cargando success_patterns: {e}")
        return {}
    
    def save_success_patterns(self):
        """Guardar patrones de éxito"""
        try:
            with open(self.success_patterns_file, 'w') as f:
                json.dump(self.success_patterns, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando success_patterns: {e}")
    
    def analyze_domain(self, domain: str) -> Dict[str, List[str]]:
        """Analizar dominio para extraer información contextual"""
        parsed = urlparse(domain)
        hostname = parsed.netloc.lower()
        
        analysis = {
            'domain_parts': [],
            'company_variations': [],
            'technology_indicators': [],
            'language_indicators': [],
            'subdomain_patterns': []
        }
        
        # Extraer partes del dominio
        domain_parts = hostname.replace('www.', '').split('.')
        company_name = domain_parts[0] if domain_parts else ''
        
        analysis['domain_parts'] = domain_parts
        
        # Generar variaciones de la empresa
        if company_name:
            variations = self.generate_company_variations(company_name)
            analysis['company_variations'] = variations
        
        # Detectar indicadores de tecnología
        tech_indicators = self.detect_technology_indicators(hostname)
        analysis['technology_indicators'] = tech_indicators
        
        # Detectar patrones de idioma
        lang_indicators = self.detect_language_indicators(hostname)
        analysis['language_indicators'] = lang_indicators
        
        return analysis
    
    def generate_company_variations(self, company_name: str) -> List[str]:
        """Generar variaciones inteligentes del nombre de la empresa"""
        variations = set()
        
        # Variaciones básicas
        variations.update([
            company_name,
            company_name.lower(),
            company_name.upper(),
            company_name.capitalize()
        ])
        
        # Variaciones con prefijos/sufijos comunes
        prefixes = ['', 'my', 'app', 'web', 'api', 'admin', 'dev', 'test', 'beta']
        suffixes = ['', 'api', 'app', 'web', 'admin', 'panel', 'dashboard', 'portal',
                   'dev', 'test', 'staging', 'beta', 'v1', 'v2', 'old', 'new']
        
        for prefix in prefixes:
            for suffix in suffixes:
                if prefix or suffix:  # No agregar el nombre solo dos veces
                    # Con guión bajo
                    if prefix and suffix:
                        variations.add(f"{prefix}_{company_name}_{suffix}")
                    elif prefix:
                        variations.add(f"{prefix}_{company_name}")
                    elif suffix:
                        variations.add(f"{company_name}_{suffix}")
                    
                    # Sin guión bajo
                    if prefix and suffix:
                        variations.add(f"{prefix}{company_name}{suffix}")
                    elif prefix:
                        variations.add(f"{prefix}{company_name}")
                    elif suffix:
                        variations.add(f"{company_name}{suffix}")
        
        return list(variations)
    
    def detect_technology_indicators(self, hostname: str) -> List[str]:
        """Detectar indicadores de tecnología en el hostname"""
        tech_words = []
        
        # Patrones de tecnología conocidos
        tech_patterns = {
            'php': ['php', 'phpmyadmin', 'wp-', 'wordpress'],
            'java': ['java', 'jsp', 'spring', 'struts', 'tomcat'],
            'python': ['django', 'flask', 'pyramid', 'python'],
            'ruby': ['ruby', 'rails', 'ror'],
            'nodejs': ['node', 'npm', 'express'],
            'dotnet': ['asp', 'aspx', 'net', 'iis'],
            'cms': ['wp', 'wordpress', 'drupal', 'joomla', 'magento'],
            'api': ['api', 'rest', 'graphql', 'soap', 'json']
        }
        
        for tech, patterns in tech_patterns.items():
            for pattern in patterns:
                if pattern in hostname:
                    tech_words.append(tech)
                    tech_words.extend(patterns)
        
        return list(set(tech_words))
    
    def detect_language_indicators(self, hostname: str) -> List[str]:
        """Detectar indicadores de idioma/región"""
        lang_indicators = []
        
        # Patrones de idioma/región
        lang_patterns = {
            'es': ['es', 'esp', 'spain', 'español', 'spanish'],
            'en': ['en', 'eng', 'english'],
            'fr': ['fr', 'fra', 'french', 'français'],
            'de': ['de', 'deu', 'german', 'deutsch'],
            'it': ['it', 'ita', 'italian', 'italiano'],
            'pt': ['pt', 'por', 'portuguese', 'português'],
            'br': ['br', 'brasil', 'brazil'],
            'mx': ['mx', 'mexico'],
            'ar': ['ar', 'argentina'],
            'co': ['co', 'colombia'],
            'cl': ['cl', 'chile']
        }
        
        for lang, patterns in lang_patterns.items():
            for pattern in patterns:
                if pattern in hostname:
                    lang_indicators.extend(patterns)
        
        return list(set(lang_indicators))
    
    def generate_bruteforce_combinations(self, length: int, charset: str = None) -> List[str]:
        """Generar combinaciones por fuerza bruta de manera inteligente"""
        if charset is None:
            charset = string.ascii_lowercase
        
        combinations = []
        
        # Limitar generación para evitar explosión combinatoria
        if length <= 3:
            for combo in itertools.product(charset, repeat=length):
                word = ''.join(combo)
                combinations.append(word)
        elif length <= 6:
            # Para longitudes medias, usar patrones más comunes
            common_starts = ['a', 'ad', 'ap', 'da', 'de', 'in', 'lo', 'pa', 'pr', 'se', 'te', 'up']
            for start in common_starts:
                remaining_length = length - len(start)
                if remaining_length > 0 and remaining_length <= 3:
                    for combo in itertools.product(charset, repeat=remaining_length):
                        word = start + ''.join(combo)
                        combinations.append(word)
        
        return combinations[:1000]  # Limitar a 1000 combinaciones por longitud
    
    def generate_contextual_wordlist(self, domain: str, base_wordlist: List[str] = None) -> List[str]:
        """Generar wordlist contextual basada en el dominio"""
        if base_wordlist is None:
            base_wordlist = list(self.base_paths)
        
        # Analizar dominio
        domain_analysis = self.analyze_domain(domain)
        
        # Conjunto final de palabras
        contextual_words = set(base_wordlist)
        
        # Agregar variaciones de la empresa
        contextual_words.update(domain_analysis['company_variations'])
        
        # Agregar indicadores de tecnología
        contextual_words.update(domain_analysis['technology_indicators'])
        
        # Agregar indicadores de idioma
        contextual_words.update(domain_analysis['language_indicators'])
        
        # Agregar palabras aprendidas con alta frecuencia de éxito
        for word, frequency in self.learned_words.items():
            if frequency >= self.min_word_frequency:
                contextual_words.add(word)
        
        # Agregar patrones específicos del dominio si existen
        domain_key = urlparse(domain).netloc
        if domain_key in self.success_patterns:
            contextual_words.update(self.success_patterns[domain_key])
        
        # Generar combinaciones por fuerza bruta para palabras cortas
        company_name = domain_analysis['domain_parts'][0] if domain_analysis['domain_parts'] else ''
        if company_name and len(company_name) <= 4:
            short_combos = self.generate_bruteforce_combinations(3)
            # Combinar con nombre de empresa
            for combo in short_combos[:50]:  # Limitar cantidad
                contextual_words.add(f"{company_name}{combo}")
                contextual_words.add(f"{combo}{company_name}")
        
        # Extensiones comunes
        extensions = ['php', 'html', 'htm', 'asp', 'aspx', 'jsp', 'do', 'action', 
                     'json', 'xml', 'txt', 'log', 'conf', 'config', 'bak', 'old']
        
        # Agregar variaciones con extensiones
        final_words = set()
        for word in contextual_words:
            final_words.add(word)
            final_words.add(f"{word}/")  # Como directorio
            
            # Agregar con extensiones para archivos
            if not word.endswith('/') and '.' not in word:
                for ext in extensions[:8]:  # Solo las más comunes
                    final_words.add(f"{word}.{ext}")
        
        # Filtrar palabras demasiado largas o con caracteres no válidos
        filtered_words = []
        for word in final_words:
            if (len(word) <= 50 and 
                re.match(r'^[a-zA-Z0-9._/-]+$', word) and
                word.strip()):
                filtered_words.append(word)
        
        return sorted(list(set(filtered_words)))
    
    def learn_from_findings(self, findings: List[Dict], domain: str):
        """Aprender de hallazgos exitosos para mejorar futuras wordlists"""
        domain_key = urlparse(domain).netloc
        
        if domain_key not in self.success_patterns:
            self.success_patterns[domain_key] = []
        
        for finding in findings:
            url = finding.get('url', '')
            status_code = finding.get('status_code', 0)
            path = finding.get('path', '')
            
            # Solo aprender de códigos de estado exitosos
            if status_code in [200, 201, 301, 302, 403]:
                # Extraer la palabra/path que funcionó
                if path:
                    # Agregar la palabra exacta
                    if path not in self.success_patterns[domain_key]:
                        self.success_patterns[domain_key].append(path)
                    
                    # Incrementar frecuencia en learned_words
                    self.learned_words[path] = self.learned_words.get(path, 0) + 1
                    
                    # Extraer patrones de la palabra exitosa
                    self.extract_patterns_from_successful_path(path, domain_key)
        
        # Guardar aprendizaje
        self.save_learned_words()
        self.save_success_patterns()
    
    def extract_patterns_from_successful_path(self, path: str, domain_key: str):
        """Extraer patrones de rutas exitosas para generar variaciones"""
        # Extraer palabras base
        base_words = re.findall(r'[a-zA-Z]+', path)
        
        for word in base_words:
            if len(word) >= 3:  # Solo palabras significativas
                # Agregar la palabra base
                if word.lower() not in self.success_patterns[domain_key]:
                    self.success_patterns[domain_key].append(word.lower())
                
                # Generar variaciones comunes
                variations = [
                    f"{word}s",     # Plural
                    f"{word}ing",   # Gerundio
                    f"{word}ed",    # Pasado
                    f"{word}er",    # Comparativo
                    f"old{word}",   # Con prefijo
                    f"new{word}",   # Con prefijo
                    f"{word}old",   # Con sufijo
                    f"{word}new",   # Con sufijo
                ]
                
                for variation in variations:
                    if variation not in self.success_patterns[domain_key]:
                        self.success_patterns[domain_key].append(variation)
    
    def generate_adaptive_wordlist(self, domain: str, previous_findings: List[Dict] = None) -> List[str]:
        """Generar wordlist adaptativa que mejora con cada escaneo"""
        # Aprender de hallazgos previos si existen
        if previous_findings:
            self.learn_from_findings(previous_findings, domain)
        
        # Generar wordlist contextual
        contextual_wordlist = self.generate_contextual_wordlist(domain)
        
        # Agregar palabras de alta prioridad basadas en aprendizaje
        priority_words = self.get_priority_words(domain)
        
        # Combinar y priorizar
        final_wordlist = list(set(priority_words + contextual_wordlist))
        
        # Ordenar por probabilidad de éxito (palabras aprendidas primero)
        final_wordlist.sort(key=lambda word: self.learned_words.get(word, 0), reverse=True)
        
        return final_wordlist
    
    def get_priority_words(self, domain: str) -> List[str]:
        """Obtener palabras de alta prioridad basadas en aprendizaje previo"""
        domain_key = urlparse(domain).netloc
        priority_words = []
        
        # Palabras específicas del dominio con historial de éxito
        if domain_key in self.success_patterns:
            priority_words.extend(self.success_patterns[domain_key])
        
        # Palabras globalmente exitosas
        sorted_learned = sorted(self.learned_words.items(), key=lambda x: x[1], reverse=True)
        top_learned = [word for word, freq in sorted_learned[:100] if freq >= self.min_word_frequency]
        priority_words.extend(top_learned)
        
        return list(set(priority_words))
    
    def generate_multilanguage_wordlist(self, languages: List[str] = None) -> List[str]:
        """Generar wordlist multiidioma"""
        if languages is None:
            languages = ['en', 'es', 'fr', 'de', 'it', 'pt']
        
        multi_words = set()
        
        # Palabras comunes por idioma
        language_words = {
            'en': ['admin', 'login', 'user', 'password', 'config', 'backup', 'test'],
            'es': ['admin', 'usuario', 'contraseña', 'configuracion', 'respaldo', 'prueba'],
            'fr': ['admin', 'utilisateur', 'motdepasse', 'configuration', 'sauvegarde', 'test'],
            'de': ['admin', 'benutzer', 'passwort', 'konfiguration', 'sicherung', 'test'],
            'it': ['admin', 'utente', 'password', 'configurazione', 'backup', 'prova'],
            'pt': ['admin', 'usuario', 'senha', 'configuracao', 'backup', 'teste']
        }
        
        for lang in languages:
            if lang in language_words:
                multi_words.update(language_words[lang])
        
        return list(multi_words)
    
    def export_wordlist(self, wordlist: List[str], filename: str, format: str = 'txt') -> str:
        """Exportar wordlist en diferentes formatos"""
        output_path = self.base_dir / f"{filename}.{format}"
        
        try:
            if format == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for word in wordlist:
                        f.write(word + '\n')
            
            elif format == 'json':
                wordlist_data = {
                    'generated_at': datetime.now().isoformat(),
                    'total_words': len(wordlist),
                    'words': wordlist
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(wordlist_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Wordlist exportada: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error exportando wordlist: {e}")
            return ""
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas del generador"""
        return {
            'total_learned_words': len(self.learned_words),
            'total_base_words': len(self.base_paths),
            'domains_analyzed': len(self.success_patterns),
            'most_successful_words': sorted(
                self.learned_words.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            'last_updated': datetime.now().isoformat()
        }

# Función principal para testing
def main():
    """Función principal para testing del generador"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Intelligent Wordlist Generator')
    parser.add_argument('--domain', required=True, help='Dominio para análisis')
    parser.add_argument('--output', default='generated_wordlist', help='Nombre del archivo de salida')
    parser.add_argument('--format', choices=['txt', 'json'], default='txt', help='Formato de salida')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Crear generador
    generator = IntelligentWordlistGenerator()
    
    # Mostrar estadísticas si se solicita
    if args.stats:
        stats = generator.get_statistics()
        print("\n📊 ESTADÍSTICAS DEL GENERADOR:")
        print("=" * 50)
        for key, value in stats.items():
            if key == 'most_successful_words':
                print(f"{key}: {value[:5]}")  # Solo mostrar top 5
            else:
                print(f"{key}: {value}")
    
    # Generar wordlist adaptativa
    print(f"\n🧠 Generando wordlist inteligente para: {args.domain}")
    wordlist = generator.generate_adaptive_wordlist(args.domain)
    
    # Exportar wordlist
    output_file = generator.export_wordlist(wordlist, args.output, args.format)
    
    print(f"\n✅ Wordlist generada:")
    print(f"   Archivo: {output_file}")
    print(f"   Total de palabras: {len(wordlist)}")
    print(f"   Primeras 10 palabras: {wordlist[:10]}")

if __name__ == "__main__":
    main()