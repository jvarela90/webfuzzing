# tests/test_fuzzing_engine.py
import unittest
import tempfile
import shutil
from pathlib import Path
import json
import sys
import os

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from core.fuzzing_engine import FuzzingEngine
from core.dictionary_manager import DictionaryManager
from core.bruteforce_generator import BruteforceGenerator

class TestFuzzingEngine(unittest.TestCase):
    """Tests para el motor de fuzzing"""
    
    def setUp(self):
        """Configurar entorno de prueba"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Crear estructura de directorios de prueba
        (self.test_dir / 'data').mkdir()
        (self.test_dir / 'data' / 'diccionarios').mkdir()
        (self.test_dir / 'data' / 'resultados').mkdir()
        (self.test_dir / 'logs').mkdir()
        (self.test_dir / 'backups').mkdir()
        
        # Crear archivo de configuración de prueba
        config_data = {
            "system": {"name": "Test", "version": "1.0.0"},
            "fuzzing": {
                "max_workers": 2,
                "timeout": 1,
                "user_agent": "Test Agent",
                "retry_count": 1,
                "delay_between_requests": 0,
                "status_codes_of_interest": [200, 403],
                "critical_paths": [".git", "admin"],
                "max_path_length": 6
            },
            "database": {"type": "sqlite", "name": "test.db"},
            "files": {
                "domains_file": "data/dominios.csv",
                "dictionaries_dir": "data/diccionarios",
                "results_dir": "data/resultados",
                "discovered_paths": "data/descubiertos.txt"
            }
        }
        
        config_file = self.test_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Crear archivos de prueba
        self.create_test_files()
        
        # Configurar config
        self.config = Config(str(config_file))
        self.config.base_dir = self.test_dir
        
        # Inicializar motor
        self.engine = FuzzingEngine(self.config)
    
    def tearDown(self):
        """Limpiar después de las pruebas"""
        shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Crear archivos de prueba"""
        # Archivo de dominios
        domains_file = self.test_dir / 'data' / 'dominios.csv'
        with open(domains_file, 'w') as f:
            f.write("httpbin.org\n")
            f.write("example.com:80\n")
        
        # Diccionario básico
        dict_file = self.test_dir / 'data' / 'diccionarios' / 'basic.txt'
        with open(dict_file, 'w') as f:
            f.write("admin\n")
            f.write("test\n")
            f.write("api\n")
        
        # Archivo de rutas descubiertas
        discovered_file = self.test_dir / 'data' / 'descubiertos.txt'
        with open(discovered_file, 'w') as f:
            f.write("login\n")
            f.write("panel\n")
    
    def test_load_domains_from_csv(self):
        """Probar carga de dominios desde CSV"""
        domains = self.engine.load_domains_from_csv()
        
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['host'], 'httpbin.org')
        self.assertEqual(domains[0]['protocol'], 'https')
        self.assertEqual(domains[1]['port'], 80)
    
    def test_load_dictionary(self):
        """Probar carga de diccionario"""
        dictionary = self.engine.load_dictionary()
        
        self.assertGreater(len(dictionary), 0)
        self.assertIn('admin', dictionary)
        self.assertIn('test', dictionary)
        self.assertIn('login', dictionary)  # De rutas descubiertas
    
    def test_generate_bruteforce_paths(self):
        """Probar generación de rutas por fuerza bruta"""
        paths = self.engine.generate_bruteforce_paths(4)
        
        self.assertGreater(len(paths), 0)
        self.assertLessEqual(len(paths), 5000)
    
    def test_test_single_url_invalid(self):
        """Probar prueba de URL inválida"""
        result = self.engine.test_single_url("http://invalid-domain-12345.com/test", 1)
        
        # Debe retornar None para dominios inválidos
        self.assertIsNone(result)

class TestDictionaryManager(unittest.TestCase):
    """Tests para el gestor de diccionarios"""
    
    def setUp(self):
        """Configurar entorno de prueba"""
        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / 'data').mkdir()
        (self.test_dir / 'data' / 'diccionarios').mkdir()
        
        # Configuración mínima
        config_data = {
            "fuzzing": {"max_path_length": 8},
            "files": {"dictionaries_dir": "data/diccionarios"}
        }
        
        config_file = self.test_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        self.config = Config(str(config_file))
        self.config.base_dir = self.test_dir
        
        self.manager = DictionaryManager(self.config)
    
    def tearDown(self):
        """Limpiar después de las pruebas"""
        shutil.rmtree(self.test_dir)
    
    def test_clean_path(self):
        """Probar limpieza de rutas"""
        # Casos válidos
        self.assertEqual(self.manager.clean_path("/admin/"), "admin")
        self.assertEqual(self.manager.clean_path("https://example.com/test"), "test")
        self.assertEqual(self.manager.clean_path("  /api/v1  "), "api/v1")
        
        # Casos inválidos
        self.assertEqual(self.manager.clean_path(""), "")
        self.assertEqual(self.manager.clean_path("a" * 101), "")  # Muy largo
    
    def test_generate_smart_combinations(self):
        """Probar generación de combinaciones inteligentes"""
        base_words = {'admin', 'test', 'api'}
        combinations = self.manager.generate_smart_combinations(base_words, 50)
        
        self.assertGreater(len(combinations), 0)
        self.assertLessEqual(len(combinations), 50)
    
    def test_update_path_stats(self):
        """Probar actualización de estadísticas"""
        path = "test_path"
        
        # Primera actualización
        self.manager.update_path_stats(path, True)
        stats = self.manager.path_stats[path]
        
        self.assertEqual(stats['uses'], 1)
        self.assertEqual(stats['successes'], 1)
        self.assertEqual(stats['success_rate'], 1.0)
        
        # Segunda actualización (fallo)
        self.manager.update_path_stats(path, False)
        stats = self.manager.path_stats[path]
        
        self.assertEqual(stats['uses'], 2)
        self.assertEqual(stats['successes'], 1)
        self.assertEqual(stats['success_rate'], 0.5)

class TestBruteforceGenerator(unittest.TestCase):
    """Tests para el generador de fuerza bruta"""
    
    def setUp(self):
        """Configurar entorno de prueba"""
        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / 'data').mkdir()
        
        config_data = {
            "fuzzing": {
                "alphabet": "abcd",  # Reducido para pruebas
                "numbers": "01",
                "special_chars": "_",
                "max_path_length": 4
            }
        }
        
        config_file = self.test_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        self.config = Config(str(config_file))
        self.config.base_dir = self.test_dir
        
        self.generator = BruteforceGenerator(self.config)
    
    def tearDown(self):
        """Limpiar después de las pruebas"""
        shutil.rmtree(self.test_dir)
    
    def test_generate_random(self):
        """Probar generación aleatoria"""
        paths = self.generator.generate_random("abc", 3, 10)
        
        self.assertEqual(len(paths), 10)
        for path in paths:
            self.assertEqual(len(path), 3)
            self.assertTrue(all(c in "abc" for c in path))
    
    def test_generate_pattern_based(self):
        """Probar generación basada en patrones"""
        patterns = ['test', 'admin']
        paths = self.generator.generate_pattern_based(patterns, 20)
        
        self.assertGreater(len(paths), 0)
        self.assertLessEqual(len(paths), 20)
    
    def test_generate_numeric_sequences(self):
        """Probar generación de secuencias numéricas"""
        paths = self.generator.generate_numeric_sequences(50)
        
        self.assertGreater(len(paths), 0)
        self.assertLessEqual(len(paths), 50)
        
        # Verificar que contiene números
        numeric_paths = [p for p in paths if p.isdigit()]
        self.assertGreater(len(numeric_paths), 0)
    
    def test_mark_pattern_successful(self):
        """Probar marcado de patrones exitosos"""
        pattern = "admin_panel.php"
        
        initial_count = len(self.generator.successful_patterns)
        self.generator.mark_pattern_successful(pattern)
        
        self.assertGreater(len(self.generator.successful_patterns), initial_count)
        self.assertIn("admin_panel", self.generator.successful_patterns)
    
    def test_comprehensive_wordlist_generation(self):
        """Probar generación de wordlist comprehensiva"""
        base_words = ['test', 'admin']
        wordlist = self.generator.generate_comprehensive_wordlist(100, base_words)
        
        self.assertGreater(len(wordlist), 0)
        self.assertLessEqual(len(wordlist), 100)
        
        # Verificar que no hay duplicados
        self.assertEqual(len(wordlist), len(set(wordlist)))

class TestIntegration(unittest.TestCase):
    """Tests de integración del sistema completo"""
    
    def setUp(self):
        """Configurar entorno de prueba"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Crear estructura completa
        dirs = ['data', 'data/diccionarios', 'data/resultados', 'logs', 'backups']
        for dir_name in dirs:
            (self.test_dir / dir_name).mkdir(parents=True)
        
        # Configuración completa
        config_data = {
            "system": {"name": "Integration Test", "version": "1.0.0"},
            "fuzzing": {
                "max_workers": 1,
                "timeout": 1,
                "max_path_length": 4,
                "critical_paths": [".git", "admin"]
            },
            "database": {"type": "sqlite", "name": "integration_test.db"},
            "files": {
                "domains_file": "data/dominios.csv",
                "dictionaries_dir": "data/diccionarios",
                "results_dir": "data/resultados",
                "discovered_paths": "data/descubiertos.txt"
            }
        }
        
        config_file = self.test_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Crear archivos de datos
        self.create_test_data()
        
        self.config = Config(str(config_file))
        self.config.base_dir = self.test_dir
    
    def tearDown(self):
        """Limpiar después de las pruebas"""
        shutil.rmtree(self.test_dir)
    
    def create_test_data(self):
        """Crear datos de prueba"""
        # Dominios
        with open(self.test_dir / 'data' / 'dominios.csv', 'w') as f:
            f.write("httpbin.org\n")
        
        # Diccionario
        with open(self.test_dir / 'data' / 'diccionarios' / 'test.txt', 'w') as f:
            f.write("status\nget\npost\n")
        
        # Rutas descubiertas vacías
        (self.test_dir / 'data' / 'descubiertos.txt').touch()
    
    def test_full_workflow(self):
        """Probar flujo completo del sistema"""
        # Inicializar componentes
        engine = FuzzingEngine(self.config)
        dict_manager = DictionaryManager(self.config)
        brute_generator = BruteforceGenerator(self.config)
        
        # 1. Cargar dominios
        domains = engine.load_domains_from_csv()
        self.assertGreater(len(domains), 0)
        
        # 2. Generar diccionario
        dictionary = dict_manager.get_optimized_dictionary(50)
        self.assertGreater(len(dictionary), 0)
        
        # 3. Generar rutas por fuerza bruta
        brute_paths = brute_generator.generate_comprehensive_wordlist(30)
        self.assertGreater(len(brute_paths), 0)
        
        # 4. Combinar rutas
        all_paths = list(set(dictionary + brute_paths))
        self.assertGreater(len(all_paths), 0)
        
        # 5. Probar fuzzing en dominio real (httpbin.org)
        domain = domains[0]
        results = engine.fuzz_domain(domain, all_paths[:10])  # Limitar para prueba
        
        # httpbin.org debería tener algunas rutas válidas
        # (Esto puede fallar si httpbin.org no está disponible)
        self.assertIsInstance(results, list)

def run_tests():
    """Ejecutar todas las pruebas"""
    # Crear suite de pruebas
    suite = unittest.TestSuite()
    
    # Agregar tests
    test_classes = [
        TestFuzzingEngine,
        TestDictionaryManager, 
        TestBruteforceGenerator,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN DE PRUEBAS")
    print(f"{'='*50}")
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Exitosos: {result.testsRun - len(result.errors) - len(result.failures)}")
    
    if result.errors:
        print(f"\nERRORES:")
        for test, error in result.errors:
            print(f"  - {test}: {error.split('\\n')[-2] if error else 'Unknown'}")
    
    if result.failures:
        print(f"\nFALLOS:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure.split('\\n')[-2] if failure else 'Unknown'}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)