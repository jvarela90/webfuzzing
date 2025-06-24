#!/usr/bin/env python3
"""
Diagnóstico y Reparación de Archivos YAML
Identifica y soluciona problemas con config.yaml
"""

import os
import yaml
import json
from pathlib import Path
import traceback

def check_yaml_files():
    """Verificar todos los archivos YAML en el proyecto"""
    print("🔍 Verificando archivos YAML...")
    print("=" * 50)
    
    # Posibles ubicaciones de archivos YAML
    yaml_files = [
        'config.yaml',
        'config/config.yaml', 
        'config/settings.yaml',
        'settings.yaml',
        'app.yaml',
        'web/config.yaml'
    ]
    
    existing_files = []
    missing_files = []
    broken_files = []
    
    for yaml_file in yaml_files:
        path = Path(yaml_file)
        if path.exists():
            print(f"✅ {yaml_file} - EXISTE")
            existing_files.append(yaml_file)
            
            # Verificar si es válido
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                print(f"   📄 YAML válido ({type(content).__name__})")
                
                # Mostrar contenido si es pequeño
                if isinstance(content, dict) and len(str(content)) < 200:
                    print(f"   📋 Contenido: {content}")
                elif isinstance(content, dict):
                    print(f"   📋 Claves: {list(content.keys())}")
                    
            except yaml.YAMLError as e:
                print(f"   ❌ YAML INVÁLIDO: {e}")
                broken_files.append(yaml_file)
            except Exception as e:
                print(f"   ❌ ERROR AL LEER: {e}")
                broken_files.append(yaml_file)
        else:
            print(f"❌ {yaml_file} - FALTA")
            missing_files.append(yaml_file)
    
    return existing_files, missing_files, broken_files

def check_yaml_usage_in_code():
    """Verificar dónde se usa YAML en el código"""
    print("\n🔍 Verificando uso de YAML en código...")
    print("=" * 50)
    
    # Archivos Python que podrían usar YAML
    python_files = []
    for pattern in ['*.py', '**/*.py']:
        python_files.extend(Path('.').glob(pattern))
    
    yaml_usage = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Buscar referencias a archivos YAML
                yaml_refs = []
                if 'config.yaml' in content:
                    yaml_refs.append('config.yaml')
                if 'settings.yaml' in content:
                    yaml_refs.append('settings.yaml')
                if 'yaml.load' in content or 'yaml.safe_load' in content:
                    yaml_refs.append('yaml_loading')
                if 'import yaml' in content:
                    yaml_refs.append('yaml_import')
                
                if yaml_refs:
                    print(f"📄 {py_file}: {', '.join(yaml_refs)}")
                    yaml_usage.append({
                        'file': str(py_file),
                        'references': yaml_refs
                    })
                    
        except Exception as e:
            continue
    
    return yaml_usage

def find_config_loading_errors():
    """Buscar errores específicos de carga de configuración"""
    print("\n🔍 Buscando errores de configuración...")
    print("=" * 50)
    
    # Verificar si PyYAML está instalado
    try:
        import yaml
        print("✅ PyYAML instalado")
        print(f"   📦 Versión: {yaml.__version__}")
    except ImportError:
        print("❌ PyYAML NO INSTALADO")
        return ["PyYAML no instalado"]
    
    # Verificar carga de archivos de configuración comunes
    config_files_to_test = [
        'config.yaml',
        'config/config.yaml',
        'config/settings.yaml'
    ]
    
    errors = []
    
    for config_file in config_files_to_test:
        try:
            path = Path(config_file)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                print(f"✅ {config_file} - Carga OK")
            else:
                print(f"⚠️ {config_file} - No existe")
        except Exception as e:
            print(f"❌ {config_file} - Error: {e}")
            errors.append(f"{config_file}: {e}")
    
    return errors

def generate_default_configs():
    """Generar archivos de configuración por defecto"""
    print("\n🔧 Generando archivos de configuración...")
    print("=" * 50)
    
    # Configuración básica
    basic_config = {
        'system': {
            'name': 'URLControl Security System',
            'version': '2.0.0',
            'debug': False
        },
        'server': {
            'host': '127.0.0.1',
            'port': 5000,
            'api_port': 8000
        },
        'database': {
            'url': 'sqlite:///urlcontrol.db',
            'pool_size': 10
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/system.log',
            'max_files': 10
        },
        'fuzzing': {
            'threads': 10,
            'delay': 0.1,
            'timeout': 10,
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            ]
        },
        'notifications': {
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_ids': []
            },
            'email': {
                'enabled': False,
                'smtp_server': '',
                'port': 587,
                'username': '',
                'password': ''
            }
        },
        'security': {
            'api_key_required': False,
            'rate_limit': '100/hour',
            'allowed_hosts': ['localhost', '127.0.0.1']
        }
    }
    
    # Configuración de settings específicos
    settings_config = {
        'targets': {
            'domains': [],
            'default_paths': [
                '/admin', '/api', '/backup', '/config', '/dashboard',
                '/login', '/panel', '/phpmyadmin', '/wp-admin'
            ]
        },
        'payloads': {
            'directories': [
                'admin', 'api', 'backup', 'config', 'dashboard',
                'login', 'panel', 'test', 'dev', 'staging'
            ],
            'files': [
                'config.php', 'admin.php', 'login.php', 'test.php',
                'backup.sql', 'database.sql', '.env', 'config.json'
            ]
        },
        'scan_settings': {
            'max_depth': 3,
            'follow_redirects': True,
            'verify_ssl': False,
            'custom_headers': {}
        }
    }
    
    generated_files = []
    
    # Crear directorio config si no existe
    os.makedirs('config', exist_ok=True)
    
    # Generar config.yaml
    try:
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(basic_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        print("✅ config/config.yaml creado")
        generated_files.append('config/config.yaml')
    except Exception as e:
        print(f"❌ Error creando config/config.yaml: {e}")
    
    # Generar settings.yaml
    try:
        with open('config/settings.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(settings_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        print("✅ config/settings.yaml creado")
        generated_files.append('config/settings.yaml')
    except Exception as e:
        print(f"❌ Error creando config/settings.yaml: {e}")
    
    # También crear config.yaml en la raíz si no existe
    if not Path('config.yaml').exists():
        try:
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(basic_config, f, default_flow_style=False, indent=2, allow_unicode=True)
            print("✅ config.yaml (raíz) creado")
            generated_files.append('config.yaml')
        except Exception as e:
            print(f"❌ Error creando config.yaml: {e}")
    
    return generated_files

def test_yaml_loading():
    """Probar carga de archivos YAML generados"""
    print("\n🧪 Probando carga de archivos YAML...")
    print("=" * 50)
    
    yaml_files = ['config.yaml', 'config/config.yaml', 'config/settings.yaml']
    
    for yaml_file in yaml_files:
        path = Path(yaml_file)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                print(f"✅ {yaml_file} - Carga exitosa")
                print(f"   📊 Tipo: {type(data).__name__}")
                if isinstance(data, dict):
                    print(f"   🔑 Claves principales: {list(data.keys())}")
            except Exception as e:
                print(f"❌ {yaml_file} - Error: {e}")
                print(f"   🔍 Traceback: {traceback.format_exc()}")

def fix_common_yaml_issues():
    """Solucionar problemas comunes de YAML"""
    print("\n🔧 Solucionando problemas comunes...")
    print("=" * 50)
    
    fixes_applied = []
    
    # 1. Instalar PyYAML si no está
    try:
        import yaml
    except ImportError:
        print("🔧 Instalando PyYAML...")
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyyaml'])
            print("✅ PyYAML instalado")
            fixes_applied.append("PyYAML instalado")
        except Exception as e:
            print(f"❌ Error instalando PyYAML: {e}")
    
    # 2. Verificar encoding de archivos existentes
    yaml_files = ['config.yaml', 'config/config.yaml', 'config/settings.yaml']
    
    for yaml_file in yaml_files:
        path = Path(yaml_file)
        if path.exists():
            try:
                # Intentar leer con diferentes encodings
                encodings = ['utf-8', 'latin-1', 'cp1252']
                content = None
                working_encoding = None
                
                for encoding in encodings:
                    try:
                        with open(path, 'r', encoding=encoding) as f:
                            content = f.read()
                        working_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content and working_encoding != 'utf-8':
                    # Reescribir en UTF-8
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ {yaml_file} convertido a UTF-8")
                    fixes_applied.append(f"{yaml_file} encoding fixed")
                    
            except Exception as e:
                print(f"❌ Error procesando {yaml_file}: {e}")
    
    return fixes_applied

def main():
    """Función principal de diagnóstico YAML"""
    print("🔍 Diagnóstico Completo de Archivos YAML")
    print("=" * 60)
    
    # 1. Verificar archivos YAML existentes
    existing, missing, broken = check_yaml_files()
    
    # 2. Verificar uso en código
    yaml_usage = check_yaml_usage_in_code()
    
    # 3. Buscar errores específicos
    config_errors = find_config_loading_errors()
    
    # 4. Aplicar soluciones
    fixes = fix_common_yaml_issues()
    
    # 5. Generar archivos faltantes
    generated = generate_default_configs()
    
    # 6. Probar carga final
    test_yaml_loading()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    print(f"📁 Archivos YAML existentes: {len(existing)}")
    print(f"❌ Archivos YAML faltantes: {len(missing)}")
    print(f"🔴 Archivos YAML rotos: {len(broken)}")
    print(f"🔧 Correcciones aplicadas: {len(fixes)}")
    print(f"✅ Archivos generados: {len(generated)}")
    
    if broken:
        print(f"\n🚨 Archivos con problemas: {broken}")
    
    if config_errors:
        print(f"\n🔍 Errores encontrados: {config_errors}")
    
    if generated:
        print(f"\n🎉 Archivos creados: {generated}")
        print("\n🔧 Comandos para verificar:")
        for file in generated:
            print(f"   cat {file}")
    
    print("\n✅ Diagnóstico completo!")

if __name__ == "__main__":
    main()