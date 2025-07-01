#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del sistema WebFuzzing Pro
"""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Probar imports básicos"""
    print("🔍 Probando imports...")
    
    try:
        # Imports básicos
        from config.settings import Config, get_config
        from database.manager import DatabaseManager
        from database.models import Domain, DiscoveredPath, Alert
        from utils.logger import setup_logging, get_logger
        from integrations import IntegrationManager
        
        print("✅ Todos los imports básicos exitosos")
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Probar sistema de configuración"""
    print("\n🔧 Probando configuración...")
    
    try:
        # Crear configuración temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "api": {"port": 8000, "api_key": "test-key"},
                "database": {"path": "test.db"},
                "logging": {"level": "INFO"}
            }
            json.dump(test_config, f)
            temp_config_file = f.name
        
        try:
            from config.settings import Config
            
            # Probar carga de configuración
            config = Config(temp_config_file)
            
            # Probar acceso a valores
            assert config.get('api.port') == 8000
            assert config.get('api.api_key') == 'test-key'
            assert config.get('database.path') == 'test.db'
            assert config.get('nonexistent.key', 'default') == 'default'
            
            # Probar establecer valores
            config.set('test.value', 'test_data')
            assert config.get('test.value') == 'test_data'
            
            print("✅ Sistema de configuración funcionando")
            return True
            
        finally:
            # Limpiar archivo temporal
            os.unlink(temp_config_file)
            
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        traceback.print_exc()
        return False

def test_logging():
    """Probar sistema de logging"""
    print("\n📝 Probando logging...")
    
    try:
        from utils.logger import setup_logging, get_logger
        
        # Configurar logging de prueba
        log_config = {
            'level': 'DEBUG',
            'file': 'logs/test.log',
            'console': True
        }
        
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Configurar logging
        main_logger = setup_logging(log_config)
        test_logger = get_logger('test')
        
        # Probar diferentes niveles
        test_logger.debug("Mensaje de debug")
        test_logger.info("Mensaje de info")
        test_logger.warning("Mensaje de warning")
        
        print("✅ Sistema de logging funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en logging: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Probar sistema de base de datos"""
    print("\n🗄️ Probando base de datos...")
    
    try:
        from database.manager import DatabaseManager
        from database.models import Domain, DiscoveredPath
        
        # Crear base de datos temporal
        test_db_path = 'test_webfuzzing.db'
        
        # Configuración de prueba
        config = {
            'database': {
                'path': test_db_path
            }
        }
        
        try:
            # Inicializar base de datos
            db = DatabaseManager(config)
            
            # Probar agregar dominio
            domain_id = db.add_domain('test.example.com', 443, 'https')
            assert isinstance(domain_id, int)
            
            # Probar obtener dominios
            domains = db.get_active_domains()
            assert len(domains) == 1
            assert domains[0]['domain'] == 'test.example.com'
            
            # Probar agregar ruta descubierta
            path_id = db.add_discovered_path(
                domain_id, 
                '/admin', 
                'https://test.example.com/admin',
                200,
                content_length=1024,
                is_critical=True
            )
            assert isinstance(path_id, int)
            
            # Probar estadísticas
            stats = db.get_stats()
            assert stats['total_domains'] == 1
            assert stats['critical_findings'] == 1
            
            print("✅ Sistema de base de datos funcionando")
            return True
            
        finally:
            # Limpiar archivo de base de datos
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)
            
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        traceback.print_exc()
        return False

def test_integrations():
    """Probar sistema de integraciones"""
    print("\n🔗 Probando integraciones...")
    
    try:
        from integrations import IntegrationManager
        
        # Configuración de prueba
        config = {
            'ffuf': {'path': 'ffuf'},
            'dirsearch': {'path': 'dirsearch'},
            'telegram': {
                'enabled': False,
                'bot_token': 'test_token',
                'chat_ids': ['123456']
            }
        }
        
        # Crear gestor de integraciones
        integration_manager = IntegrationManager(config)
        
        # Probar obtener estado
        status = integration_manager.get_integration_status()
        assert isinstance(status, dict)
        
        # Probar integraciones disponibles
        available = integration_manager.get_available_integrations()
        assert isinstance(available, list)
        
        print("✅ Sistema de integraciones funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en integraciones: {e}")
        traceback.print_exc()
        return False

def test_api_routes():
    """Probar rutas de API"""
    print("\n🌐 Probando rutas de API...")
    
    try:
        from api.routes import create_api
        from config.settings import get_config
        
        # Crear configuración de prueba
        config = get_config()
        
        # Crear app de API
        app = create_api(config)
        
        # Verificar que la app se creó correctamente
        assert app is not None
        assert hasattr(app, 'route')
        
        print("✅ Rutas de API funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en rutas de API: {e}")
        traceback.print_exc()
        return False

def test_wordlists():
    """Probar wordlists"""
    print("\n📚 Probando wordlists...")
    
    try:
        # Verificar que existen las wordlists
        common_wordlist = 'data/wordlists/common.txt'
        subdomains_wordlist = 'data/wordlists/subdomains.txt'
        
        if not os.path.exists(common_wordlist):
            print(f"⚠️ Wordlist común no encontrada: {common_wordlist}")
        else:
            with open(common_wordlist, 'r') as f:
                words = f.read().splitlines()
                assert len(words) > 0
                print(f"✅ Wordlist común: {len(words)} palabras")
        
        if not os.path.exists(subdomains_wordlist):
            print(f"⚠️ Wordlist de subdominios no encontrada: {subdomains_wordlist}")
        else:
            with open(subdomains_wordlist, 'r') as f:
                subdomains = f.read().splitlines()
                assert len(subdomains) > 0
                print(f"✅ Wordlist de subdominios: {len(subdomains)} entradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en wordlists: {e}")
        traceback.print_exc()
        return False

def create_sample_config():
    """Crear configuración de ejemplo si no existe"""
    print("\n⚙️ Verificando configuración...")
    
    config_file = 'config.json'
    
    if not os.path.exists(config_file):
        if os.path.exists('config.json.example'):
            print("📋 Copiando config.json.example a config.json...")
            import shutil
            shutil.copy('config.json.example', config_file)
            print("✅ Configuración creada desde ejemplo")
        else:
            print("⚠️ No se encontró config.json.example")
    else:
        print("✅ config.json existe")

def check_directory_structure():
    """Verificar estructura de directorios"""
    print("\n📁 Verificando estructura de directorios...")
    
    required_dirs = [
        'api',
        'web',
        'config',
        'database', 
        'integrations',
        'utils',
        'data/wordlists',
        'logs'
    ]
    
    missing_dirs = []
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
            os.makedirs(directory, exist_ok=True)
            print(f"📂 Creado directorio: {directory}")
        else:
            print(f"✅ Directorio existe: {directory}")
    
    if missing_dirs:
        print(f"📂 Se crearon {len(missing_dirs)} directorios faltantes")
    
    return True

def main():
    """Función principal de pruebas"""
    print("🚀 WebFuzzing Pro - Test del Sistema")
    print("=" * 50)
    
    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    tests = [
        ("Estructura de directorios", check_directory_structure),
        ("Configuración de ejemplo", create_sample_config),
        ("Imports", test_imports),
        ("Configuración", test_config),
        ("Logging", test_logging),
        ("Base de datos", test_database),
        ("Integraciones", test_integrations),
        ("Rutas de API", test_api_routes),
        ("Wordlists", test_wordlists)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Resultados: {passed} ✅ | {failed} ❌")
    
    if failed == 0:
        print("🎉 ¡Todos los tests pasaron! El sistema está listo.")
        return True
    else:
        print(f"⚠️ {failed} tests fallaron. Revisar errores arriba.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)