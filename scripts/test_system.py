# scripts/test_system.py
"""
Script de prueba para verificar que todos los componentes del sistema funcionan correctamente
"""

import sys
import os
import time
import json
import requests
from pathlib import Path
import subprocess
import sqlite3

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

class SystemTester:
    """Clase para probar todos los componentes del sistema"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / "config.json"
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def print_header(self, title):
        """Imprimir encabezado de sección"""
        print(f"\n{'='*50}")
        print(f" {title}")
        print(f"{'='*50}")
    
    def test_result(self, test_name, success, message=""):
        """Registrar resultado de prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_python_imports(self):
        """Probar importaciones de Python"""
        self.print_header("PRUEBAS DE DEPENDENCIAS")
        
        required_modules = [
            'flask', 'requests', 'schedule', 'sqlite3', 
            'concurrent.futures', 'threading', 'json', 'csv'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                self.test_result(f"Importar {module}", True)
            except ImportError as e:
                self.test_result(f"Importar {module}", False, str(e))
    
    def test_file_structure(self):
        """Probar estructura de archivos"""
        self.print_header("PRUEBAS DE ESTRUCTURA DE ARCHIVOS")
        
        required_files = [
            "main.py",
            "requirements.txt",
            "config.json",
            "config/settings.py",
            "config/database.py",
            "core/fuzzing_engine.py",
            "web/app.py",
            "api/routes.py",
            "utils/logger.py",
            "scripts/scheduler.py"
        ]
        
        required_dirs = [
            "data",
            "data/diccionarios", 
            "data/resultados",
            "logs",
            "backups"
        ]
        
        # Verificar archivos
        for file_path in required_files:
            full_path = self.base_dir / file_path
            exists = full_path.exists()
            self.test_result(f"Archivo {file_path}", exists)
        
        # Verificar directorios
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            exists = full_path.exists() and full_path.is_dir()
            self.test_result(f"Directorio {dir_path}", exists)
    
    def test_configuration(self):
        """Probar configuración"""
        self.print_header("PRUEBAS DE CONFIGURACIÓN")
        
        # Verificar archivo de configuración
        if not self.config_file.exists():
            self.test_result("Archivo config.json", False, "No existe")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            self.test_result("Cargar config.json", True)
            
            # Verificar secciones principales
            required_sections = ['system', 'fuzzing', 'database', 'web', 'api']
            for section in required_sections:
                exists = section in config
                self.test_result(f"Sección [{section}] en config", exists)
                
        except Exception as e:
            self.test_result("Cargar config.json", False, str(e))
    
    def test_database(self):
        """Probar base de datos"""
        self.print_header("PRUEBAS DE BASE DE DATOS")
        
        try:
            from config.settings import Config
            from config.database import DatabaseManager
            
            config = Config()
            db = DatabaseManager(config)
            
            self.test_result("Inicializar DatabaseManager", True)
            
            # Probar operaciones básicas
            domains = db.get_active_domains()
            self.test_result("Consultar dominios", True, f"{len(domains)} dominios encontrados")
            
            # Probar inserción
            test_domain_id = db.add_domain("test.example.com", 443, "https")
            self.test_result("Insertar dominio de prueba", True, f"ID: {test_domain_id}")
            
        except Exception as e:
            self.test_result("Operaciones de base de datos", False, str(e))
    
    def test_fuzzing_engine(self):
        """Probar motor de fuzzing"""
        self.print_header("PRUEBAS DEL MOTOR DE FUZZING")
        
        try:
            from config.settings import Config
            from core.fuzzing_engine import FuzzingEngine
            
            config = Config()
            engine = FuzzingEngine(config)
            
            self.test_result("Inicializar FuzzingEngine", True)
            
            # Probar carga de diccionario
            dictionary = engine.load_dictionary()
            self.test_result("Cargar diccionario", len(dictionary) > 0, 
                           f"{len(dictionary)} rutas cargadas")
            
            # Probar generación de rutas
            bruteforce_paths = engine.generate_bruteforce_paths(4)  # Longitud pequeña para prueba
            self.test_result("Generar rutas por fuerza bruta", len(bruteforce_paths) > 0,
                           f"{len(bruteforce_paths)} rutas generadas")
            
        except Exception as e:
            self.test_result("Motor de fuzzing", False, str(e))
    
    def test_web_app(self):
        """Probar aplicación web"""
        self.print_header("PRUEBAS DE APLICACIÓN WEB")
        
        try:
            from config.settings import Config
            from web.app import create_app
            
            config = Config()
            app = create_app(config)
            
            self.test_result("Crear aplicación Flask", True)
            
            # Probar cliente de prueba
            with app.test_client() as client:
                response = client.get('/')
                self.test_result("Ruta principal (/)", response.status_code == 200)
                
                response = client.get('/findings')
                self.test_result("Ruta /findings", response.status_code in [200, 302])
                
                response = client.get('/alerts')
                self.test_result("Ruta /alerts", response.status_code in [200, 302])
                
        except Exception as e:
            self.test_result("Aplicación web", False, str(e))
    
    def test_api(self):
        """Probar API REST"""
        self.print_header("PRUEBAS DE API REST")
        
        try:
            from config.settings import Config
            from api.routes import create_api
            
            config = Config()
            api = create_api(config)
            
            self.test_result("Crear API Flask", True)
            
            # Probar endpoints sin autenticación
            with api.test_client() as client:
                response = client.get('/api/v1/health')
                self.test_result("Endpoint /api/v1/health", response.status_code == 200)
                
                # Probar endpoint que requiere API key
                response = client.get('/api/v1/stats')
                self.test_result("Endpoint sin API key (debe fallar)", response.status_code == 401)
                
                # Probar con API key
                headers = {'X-API-Key': config.get('api.api_key')}
                response = client.get('/api/v1/stats', headers=headers)
                self.test_result("Endpoint con API key", response.status_code == 200)
                
        except Exception as e:
            self.test_result("API REST", False, str(e))
    
    def test_notifications(self):
        """Probar sistema de notificaciones"""
        self.print_header("PRUEBAS DE NOTIFICACIONES")
        
        try:
            from config.settings import Config
            from utils.notifications import NotificationManager
            
            config = Config()
            notifications = NotificationManager(config)
            
            self.test_result("Inicializar NotificationManager", True)
            
            # Verificar configuración de Telegram
            telegram_enabled = config.get('notifications.telegram.enabled')
            self.test_result("Configuración Telegram", True, 
                           f"Habilitado: {telegram_enabled}")
            
            # Verificar configuración de Email
            email_enabled = config.get('notifications.email.enabled')
            self.test_result("Configuración Email", True,
                           f"Habilitado: {email_enabled}")
            
        except Exception as e:
            self.test_result("Sistema de notificaciones", False, str(e))
    
    def test_scheduler(self):
        """Probar programador de tareas"""
        self.print_header("PRUEBAS DEL PROGRAMADOR")
        
        try:
            from config.settings import Config
            from scripts.scheduler import TaskScheduler
            
            config = Config()
            scheduler = TaskScheduler(config)
            
            self.test_result("Inicializar TaskScheduler", True)
            
            # Verificar tareas programadas
            tasks = scheduler.get_next_scheduled_tasks()
            self.test_result("Obtener tareas programadas", len(tasks) > 0,
                           f"{len(tasks)} tareas configuradas")
            
        except Exception as e:
            self.test_result("Programador de tareas", False, str(e))
    
    def test_external_tools(self):
        """Probar herramientas externas"""
        self.print_header("PRUEBAS DE HERRAMIENTAS EXTERNAS")
        
        # Probar ffuf
        try:
            result = subprocess.run(['ffuf', '-h'], 
                                  capture_output=True, 
                                  timeout=10)
            self.test_result("ffuf disponible", result.returncode == 0)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.test_result("ffuf disponible", False, "No encontrado en PATH")
        
        # Probar dirsearch
        try:
            result = subprocess.run(['python3', '-m', 'dirsearch', '-h'], 
                                  capture_output=True,
                                  timeout=10)
            self.test_result("dirsearch disponible", result.returncode == 0)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Intentar con python (Windows)
            try:
                result = subprocess.run(['python', '-m', 'dirsearch', '-h'], 
                                      capture_output=True,
                                      timeout=10)
                self.test_result("dirsearch disponible", result.returncode == 0)
            except:
                self.test_result("dirsearch disponible", False, "No encontrado")
    
    def test_sample_data(self):
        """Probar datos de ejemplo"""
        self.print_header("PRUEBAS DE DATOS DE EJEMPLO")
        
        # Verificar archivo de dominios
        domains_file = self.base_dir / "data" / "dominios.csv"
        if domains_file.exists():
            try:
                with open(domains_file, 'r') as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.test_result("Archivo dominios.csv", len(lines) >= 0,
                               f"{len(lines)} dominios configurados")
            except Exception as e:
                self.test_result("Leer dominios.csv", False, str(e))
        else:
            self.test_result("Archivo dominios.csv", False, "No existe")
        
        # Verificar diccionarios
        dict_dir = self.base_dir / "data" / "diccionarios"
        if dict_dir.exists():
            dict_files = list(dict_dir.glob('*.txt'))
            self.test_result("Archivos de diccionario", len(dict_files) > 0,
                           f"{len(dict_files)} diccionarios encontrados")
        else:
            self.test_result("Directorio diccionarios", False, "No existe")
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🧪 WebFuzzing Pro - Sistema de Pruebas")
        print("=" * 50)
        
        # Ejecutar todas las pruebas
        self.test_python_imports()
        self.test_file_structure()
        self.test_configuration()
        self.test_database()
        self.test_fuzzing_engine()
        self.test_web_app()
        self.test_api()
        self.test_notifications()
        self.test_scheduler()
        self.test_external_tools()
        self.test_sample_data()
        
        # Resumen final
        self.print_header("RESUMEN DE PRUEBAS")
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total de pruebas: {total_tests}")
        print(f"Exitosas: {self.passed_tests} ✅")
        print(f"Fallidas: {self.failed_tests} ❌")
        print(f"Tasa de éxito: {pass_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo para usar.")
        else:
            print(f"\n⚠️ {self.failed_tests} pruebas fallaron. Revisar configuración.")
            print("\nPruebas fallidas:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return self.failed_tests == 0

def main():
    """Función principal"""
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Sistema listo para ejecutar:")
        print("  python main.py --mode all")
        sys.exit(0)
    else:
        print("\n🔧 Ejecutar setup antes de usar:")
        print("  python scripts/install.py")
        print("  python scripts/setup_environment.py")
        sys.exit(1)

if __name__ == "__main__":
    main()