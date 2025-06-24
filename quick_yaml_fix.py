#!/usr/bin/env python3
"""
Solución Rápida para Problemas YAML
Instala PyYAML y genera archivos config necesarios
"""

import os
import sys
import subprocess
from pathlib import Path

def install_pyyaml():
    """Instalar PyYAML"""
    print("🔧 Instalando PyYAML...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyyaml>=6.0'])
        print("✅ PyYAML instalado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error instalando PyYAML: {e}")
        return False

def create_config_yaml():
    """Crear config.yaml básico"""
    config_content = """# URLControl Security System Configuration
system:
  name: "URLControl Security System"
  version: "2.0.0"
  debug: false

server:
  host: "127.0.0.1"
  port: 5000
  api_port: 8000

database:
  url: "sqlite:///urlcontrol.db"
  pool_size: 10

logging:
  level: "INFO"
  file: "logs/system.log"
  max_files: 10

fuzzing:
  threads: 10
  delay: 0.1
  timeout: 10
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    - "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

notifications:
  telegram:
    enabled: false
    bot_token: ""
    chat_ids: []
  email:
    enabled: false
    smtp_server: ""
    port: 587

security:
  api_key_required: false
  rate_limit: "100/hour"
  allowed_hosts:
    - "localhost"
    - "127.0.0.1"
"""
    
    try:
        with open('config.yaml', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ config.yaml creado")
        return True
    except Exception as e:
        print(f"❌ Error creando config.yaml: {e}")
        return False

def create_settings_yaml():
    """Crear config/settings.yaml"""
    settings_content = """# URLControl Settings Configuration
targets:
  domains: []
  default_paths:
    - "/admin"
    - "/api" 
    - "/backup"
    - "/config"
    - "/dashboard"
    - "/login"
    - "/panel"
    - "/phpmyadmin"
    - "/wp-admin"

payloads:
  directories:
    - "admin"
    - "api"
    - "backup"
    - "config"
    - "dashboard"
    - "login"
    - "panel"
    - "test"
    - "dev"
    - "staging"
  files:
    - "config.php"
    - "admin.php" 
    - "login.php"
    - "test.php"
    - "backup.sql"
    - "database.sql"
    - ".env"
    - "config.json"

scan_settings:
  max_depth: 3
  follow_redirects: true
  verify_ssl: false
  custom_headers: {}
"""
    
    try:
        os.makedirs('config', exist_ok=True)
        with open('config/settings.yaml', 'w', encoding='utf-8') as f:
            f.write(settings_content)
        print("✅ config/settings.yaml creado")
        return True
    except Exception as e:
        print(f"❌ Error creando config/settings.yaml: {e}")
        return False

def create_config_config_yaml():
    """Crear config/config.yaml"""
    config_content = """# URLControl Main Configuration  
app:
  name: "URLControl"
  debug: false
  secret_key: "change-this-secret-key"

database:
  type: "sqlite"
  path: "data/urlcontrol.db"
  
web:
  host: "0.0.0.0"
  port: 5000
  
api:
  host: "0.0.0.0" 
  port: 8000
  
fuzzing:
  enabled: true
  concurrent_requests: 10
  request_delay: 0.1
  
monitoring:
  enabled: true
  scan_interval: 3600
"""
    
    try:
        os.makedirs('config', exist_ok=True)
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ config/config.yaml creado")
        return True
    except Exception as e:
        print(f"❌ Error creando config/config.yaml: {e}")
        return False

def test_yaml_files():
    """Probar que los archivos YAML se pueden leer"""
    print("\n🧪 Probando archivos YAML...")
    
    try:
        import yaml
        
        files_to_test = [
            'config.yaml',
            'config/config.yaml', 
            'config/settings.yaml'
        ]
        
        for file_path in files_to_test:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    print(f"✅ {file_path} - OK")
                except Exception as e:
                    print(f"❌ {file_path} - Error: {e}")
            else:
                print(f"⚠️ {file_path} - No existe")
                
    except ImportError:
        print("❌ PyYAML no está instalado correctamente")

def main():
    """Función principal de solución rápida"""
    print("🚀 Solución Rápida para Problemas YAML")
    print("=" * 50)
    
    success_count = 0
    
    # 1. Instalar PyYAML
    if install_pyyaml():
        success_count += 1
    
    # 2. Crear archivos de configuración
    if create_config_yaml():
        success_count += 1
        
    if create_config_config_yaml():
        success_count += 1
        
    if create_settings_yaml():
        success_count += 1
    
    # 3. Probar archivos
    test_yaml_files()
    
    print(f"\n🎯 Proceso completado: {success_count}/4 pasos exitosos")
    
    if success_count >= 3:
        print("✅ Problema YAML solucionado!")
        print("\n🔧 Archivos creados:")
        print("  - config.yaml")
        print("  - config/config.yaml") 
        print("  - config/settings.yaml")
        print("\n🚀 Ahora puedes reiniciar tu aplicación")
    else:
        print("❌ Algunos problemas persisten. Ejecuta el diagnóstico completo.")

if __name__ == "__main__":
    main()